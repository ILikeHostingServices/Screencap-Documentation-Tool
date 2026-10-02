#!/usr/bin/env python3
#
# stepdoc.py
# 2026-10-02
# Version: v1.0.0
#
# PURPOSE:
# The step document for one processed recording: loads and saves steps.json,
# renders the screenshots shown in steps.md from the untouched originals,
# and writes steps.md. Shared by screencap.py and the GUI step editor.
#
# Folder layout for each recording:
#   originals/capture_<time>.<ext>   full frames from the video, never modified
#   step_NNN_<time>.<ext>            rendered screenshots used by steps.md
#   steps.json                       the step document (source of truth)
#   steps.md                         generated from steps.json

import hashlib
import json
import logging
import shutil
import subprocess
import time
from pathlib import Path

SCHEMA = 2
INDEX_NAME = "steps.md"
MANIFEST_NAME = "steps.json"
ORIGINALS_DIR = "originals"

log = logging.getLogger("screencap")

# Keep FFmpeg from flashing a console window when run from the GUI on Windows
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


class Cancelled(Exception):
    """Raised when the user cancels a run from the GUI."""


def fmt_ts(seconds, sep=":"):
    """Format seconds as HH:MM:SS.mmm (sep '-' gives a Windows-safe filename)."""
    ms_total = int(round(max(seconds, 0.0) * 1000))
    h, rem = divmod(ms_total, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}{sep}{m:02d}{sep}{s:02d}.{ms:03d}"


def capture_name(t, ext):
    return f"capture_{fmt_ts(t, sep='-')}.{ext}"


def new_document(video_name, duration, width, height, ext, settings, tool_version):
    return {
        "schema": SCHEMA,
        "tool_version": tool_version,
        "source_video": video_name,
        "duration": duration,
        "width": width,
        "height": height,
        "format": ext,
        "settings": settings,
        "document": {"title": Path(video_name).stem},
        "steps": [],
        "deleted_steps": [],
        "generated_md_sha256": None,
    }


def new_step(t, original, still_from=None, still_to=None, score=None, reason="change"):
    return {
        "time": t,
        "original": original,
        "file": None,
        "caption": "",
        "still_from": still_from,
        "still_to": still_to,
        "score": score,
        "reason": reason,
    }


# ---------------------------------------------------------------------------
# Load / migrate / save
# ---------------------------------------------------------------------------

def load(out_dir):
    """Load steps.json, upgrading output from older versions in place.
    Returns None if the folder has no step document."""
    out_dir = Path(out_dir)
    path = out_dir / MANIFEST_NAME
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if doc.get("schema", 1) < 2:
        doc = _migrate_v1(out_dir, doc)
    for step in doc.get("steps", []) + doc.get("deleted_steps", []):
        step.setdefault("caption", "")
    doc.setdefault("deleted_steps", [])
    doc.setdefault("document", {"title": Path(doc.get("source_video", "steps")).stem})
    return doc


def _migrate_v1(out_dir, old):
    """Output from v1.4.0 and earlier: screenshots sit next to steps.md with
    no originals folder. Move them into originals/ so they can be re-rendered,
    and keep the old steps.md as a backup because it may hold notes."""
    log.info("Upgrading %s to the editable step format", out_dir)
    ext = old.get("settings", {}).get("format", "png")
    doc = new_document(old.get("source_video", out_dir.name), old.get("duration", 0),
                       None, None, ext, old.get("settings", {}),
                       old.get("tool_version", "unknown"))
    (out_dir / ORIGINALS_DIR).mkdir(exist_ok=True)
    for old_step in old.get("steps", []):
        src = out_dir / old_step.get("file", "")
        if not src.is_file():
            continue
        orig = f"{ORIGINALS_DIR}/{capture_name(old_step['time'], src.suffix.lstrip('.'))}"
        shutil.move(str(src), str(out_dir / orig))
        doc["steps"].append(new_step(old_step["time"], orig, old_step.get("still_from"),
                                     old_step.get("still_to"), old_step.get("score"),
                                     old_step.get("reason", "change")))
    backup_markdown(out_dir, "pre-upgrade")
    return doc


def backup_markdown(out_dir, label):
    md = Path(out_dir) / INDEX_NAME
    if md.is_file():
        dest = md.with_name(f"steps.{label}-{time.strftime('%Y%m%d-%H%M%S')}.md")
        shutil.copy2(md, dest)
        log.warning("Saved a copy of the previous steps.md as %s", dest.name)
        return dest
    return None


def save(out_dir, doc):
    """Write steps.md and steps.json. If steps.md was edited by hand since the
    tool last wrote it, a backup copy is kept before it is replaced."""
    out_dir = Path(out_dir)
    md_path = out_dir / INDEX_NAME
    if md_path.is_file() and doc.get("generated_md_sha256"):
        current = hashlib.sha256(md_path.read_bytes()).hexdigest()
        if current != doc["generated_md_sha256"]:
            backup_markdown(out_dir, "hand-edited")
    text = markdown(doc)
    md_path.write_text(text, encoding="utf-8")
    doc["generated_md_sha256"] = hashlib.sha256(md_path.read_bytes()).hexdigest()
    (out_dir / MANIFEST_NAME).write_text(json.dumps(doc, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def rendered_name(index, step, ext):
    return f"step_{index:03d}_{fmt_ts(step['time'], sep='-')}.{ext}"


def build_filter(step, doc):
    """FFmpeg filter chain that turns an original frame into the finished
    screenshot, or None when the original is used as-is. The GUI preview uses
    the same chain, so what you see is what gets saved."""
    return None


def render_image(ffmpeg, src, dest, step, doc, run):
    """Produce one screenshot from its original."""
    vf = build_filter(step, doc)
    if not vf:
        shutil.copyfile(src, dest)
        return
    cmd = [ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
           "-i", str(src), "-vf", vf, "-frames:v", "1"]
    if Path(dest).suffix.lower() == ".jpg":
        cmd += ["-q:v", "2"]
    res = run(cmd + [str(dest)])
    if res.returncode != 0:
        raise RuntimeError(f"Rendering {Path(dest).name} failed: {res.stderr.strip()[-300:]}")


def run_quiet(cmd):
    """Run a command without a shell or a console window (Windows GUI)."""
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          stdin=subprocess.DEVNULL, creationflags=NO_WINDOW,
                          text=True, encoding="utf-8", errors="replace")


def render(out_dir, doc, ffmpeg, progress=None, cancel=None):
    """Re-render every screenshot from its original, remove stale ones, and
    save steps.md and steps.json."""
    out_dir = Path(out_dir)
    ext = doc.get("format", "png")
    keep = set()
    steps = doc["steps"]
    for i, step in enumerate(steps, 1):
        if cancel is not None and cancel.is_set():
            raise Cancelled()
        if progress is not None:
            progress((i - 1) / max(len(steps), 1), f"Rendering screenshot {i}/{len(steps)}")
        src = out_dir / step["original"]
        if not src.is_file():
            raise RuntimeError(f"Original image missing: {src}")
        name = rendered_name(i, step, ext)
        render_image(ffmpeg, src, out_dir / name, step, doc, run_quiet)
        step["file"] = name
        keep.add(name)
    for stale in out_dir.glob("step_*"):
        if stale.is_file() and stale.suffix.lower() in (".png", ".jpg") and stale.name not in keep:
            stale.unlink()
    save(out_dir, doc)


# ---------------------------------------------------------------------------
# Markdown
# ---------------------------------------------------------------------------

def markdown(doc):
    steps = doc["steps"]
    s = doc.get("settings", {})
    lines = [
        f"# {doc.get('document', {}).get('title') or 'Steps'}",
        "",
        f"- Source video: `{doc.get('source_video', '')}`",
        f"- Duration: {fmt_ts(doc.get('duration') or 0)}",
        f"- Generated: {time.strftime('%Y-%m-%d %H:%M:%S')} by screencap.py "
        f"v{doc.get('tool_version', '')}",
        f"- Settings: threshold={s.get('threshold')}, debounce={s.get('debounce')}s, "
        f"capture-point={s.get('capture_point')}, min-gap={s.get('min_gap')}s",
        f"- Steps: {len(steps)}",
        "",
    ]
    for i, step in enumerate(steps, 1):
        label = ""
        if step.get("reason") == "start" and i == 1:
            label = " (start of video)"
        elif step.get("reason") == "end" and i == len(steps):
            label = " (end of video)"
        lines += [f"## Step {i} - {fmt_ts(step['time'])}{label}", ""]
        details = []
        if step.get("still_from") is not None and step.get("still_to") is not None:
            details.append(f"Screen stable from {fmt_ts(step['still_from'])} "
                           f"to {fmt_ts(step['still_to'])}")
        if step.get("score") is not None:
            details.append(f"change score {step['score']:.3f}")
        if details:
            lines += ["_" + ", ".join(details) + "._", ""]
        lines += [f"![Step {i}]({step['file']})", ""]
        caption = (step.get("caption") or "").strip()
        lines += [caption if caption else "_Notes:_", ""]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Editing helpers (used by the GUI step editor)
# ---------------------------------------------------------------------------

def move_step(doc, index, delta):
    steps = doc["steps"]
    j = index + delta
    if 0 <= index < len(steps) and 0 <= j < len(steps):
        steps[index], steps[j] = steps[j], steps[index]
        return j
    return index


def delete_step(doc, index):
    """Move a step to deleted_steps. Its original image is kept so it can be
    restored later."""
    step = doc["steps"].pop(index)
    step.setdefault("deleted_reason", "deleted in editor")
    doc["deleted_steps"].append(step)
    return step


def restore_deleted(doc):
    """Put every deleted step back by its time in the video, without
    disturbing any manual reordering of the remaining steps."""
    restored = sorted(doc["deleted_steps"], key=lambda s: s["time"])
    for step in restored:
        step.pop("deleted_reason", None)
        step.pop("duplicate_of", None)
        pos = 0
        for i, existing in enumerate(doc["steps"]):
            if existing["time"] <= step["time"]:
                pos = i + 1
        doc["steps"].insert(pos, step)
    doc["deleted_steps"] = []
    return len(restored)
