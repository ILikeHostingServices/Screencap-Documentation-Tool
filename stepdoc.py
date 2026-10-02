#!/usr/bin/env python3
#
# stepdoc.py
# 2026-10-02
# Version: v1.3.0
#
# PURPOSE:
# The step document for one processed recording: loads and saves steps.json,
# renders the screenshots shown in steps.md from the untouched originals,
# and writes steps.md. Shared by screencap.py and the GUI step editor.
#
# Folder layout for each recording:
#   originals/capture_<time>.<ext>   full frames from the video, never modified
#   step_NNN_<time>.<ext>            rendered screenshots used by steps.md
#                                    (sensitive areas blurred when redaction is on)
#   unredacted/step_NNN_<time>.<ext> the same screenshots without blurring
#   steps.json                       the step document (source of truth)
#   steps.md                         generated from steps.json
#   steps-unredacted.md              same, using the unredacted screenshots

import hashlib
import json
import logging
import shutil
import subprocess
import time
from pathlib import Path

import imaging
import redact

SCHEMA = 2
INDEX_NAME = "steps.md"
MANIFEST_NAME = "steps.json"
ORIGINALS_DIR = "originals"
UNREDACTED_DIR = "unredacted"
UNREDACTED_INDEX = "steps-unredacted.md"

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
        "highlight": True,
        "crop": None,
        "redact": True,
        "redact_patterns": [],
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


HIGHLIGHT_COLOR = "0xE53935"   # red


def effective(step, doc, key, default=True):
    """A per-step setting (True/False) overrides the recording-wide one."""
    value = step.get(key)
    return doc.get(key, default) if value is None else value


NO_CROP = "none"   # step["crop"] value meaning "do not crop this step"


def effective_crop(step, doc):
    """[x, y, w, h] crop for a step: its own crop, the recording-wide crop,
    or None. All values are original-frame pixels."""
    crop = step.get("crop")
    if crop == NO_CROP:
        return None
    return crop or doc.get("crop")


def clamp_rect(rect, width, height, minimum=16):
    """Keep a rectangle inside the frame, at least `minimum` pixels, with
    even width and height (some image encoders require it)."""
    x, y, w, h = (int(round(v)) for v in rect)
    if w < 0:
        x, w = x + w, -w
    if h < 0:
        y, h = y + h, -h
    x, y = max(0, min(x, width - minimum)), max(0, min(y, height - minimum))
    w, h = max(minimum, min(w, width - x)), max(minimum, min(h, height - y))
    return [x, y, w - w % 2, h - h % 2]


BLUR_BLOCK = 12   # pixelation block size before blurring (makes text unreadable)


def redaction_boxes(step, doc):
    """Boxes to blur for a step: detected ones not switched off, plus boxes
    drawn by hand. Empty when redaction is off for this step."""
    if not effective(step, doc, "redact"):
        return []
    boxes = [r["box"] for r in step.get("auto_redactions") or [] if not r.get("ignored")]
    return boxes + list(step.get("manual_redactions") or [])


def blur_graph(boxes):
    """Filter graph that pixelates and blurs each box, then passes the frame on."""
    if not boxes:
        return ""
    n = len(boxes)
    graph = [f"split={n + 1}[base]" + "".join(f"[r{i}]" for i in range(n))]
    prev = "base"
    for i, (x, y, w, h) in enumerate(boxes):
        w, h = max(2, int(w)), max(2, int(h))
        graph.append(f"[r{i}]crop={w}:{h}:{int(x)}:{int(y)},"
                     f"scale=w='max(1,iw/{BLUR_BLOCK})':h='max(1,ih/{BLUR_BLOCK})',"
                     f"scale={w}:{h}:flags=neighbor,boxblur=2[b{i}]")
        out = f"o{i}"
        graph.append(f"[{prev}][b{i}]overlay={int(x)}:{int(y)}" + ("" if i == n - 1 else f"[{out}]"))
        prev = out
    return ";".join(graph)


def build_filter(step, doc, redacted=True):
    """FFmpeg filter graph that turns an original frame into the finished
    screenshot, or None when the original is used as-is. The GUI preview uses
    the same graph, so what you see is what gets saved. All coordinates are
    in original-frame pixels. redacted=False gives the unblurred copy."""
    parts = []
    blur = blur_graph(redaction_boxes(step, doc)) if redacted else ""
    box = step.get("change_box")
    if box and effective(step, doc, "highlight"):
        x, y, w, h = box
        thick = max(3, round((doc.get("width") or 1280) / 320))
        parts.append(f"drawbox=x={x}:y={y}:w={w}:h={h}:color={HIGHLIGHT_COLOR}@1:t={thick}")
    crop = effective_crop(step, doc)
    if crop:   # always last, so everything above uses original coordinates
        x, y, w, h = crop
        parts.append(f"crop={w}:{h}:{x}:{y}")
    chain = ",".join(parts)
    if blur:   # blur first, so the highlight box is drawn on top, unblurred
        return blur + ("," + chain if chain else "")
    return chain or None


def ensure_frame_size(out_dir, doc, ffmpeg):
    if not doc.get("width") or not doc.get("height"):
        first = next((s for s in doc["steps"] + doc["deleted_steps"]), None)
        if first:
            doc["width"], doc["height"] = imaging.image_size(ffmpeg, Path(out_dir) / first["original"])


def ensure_change_boxes(out_dir, doc, ffmpeg):
    """Work out what changed since the previous step for any step that has
    not been analyzed yet (new captures, or output from older versions)."""
    pending = [i for i, s in enumerate(doc["steps"]) if "change_box" not in s]
    if not pending:
        return
    ensure_frame_size(out_dir, doc, ffmpeg)
    out_dir = Path(out_dir)
    thumbs = {}

    def thumb(i):
        if i not in thumbs:
            thumbs[i] = imaging.thumbnail(ffmpeg, out_dir / doc["steps"][i]["original"],
                                          imaging.CHANGE_SIZE)
        return thumbs[i]

    for i in pending:
        step = doc["steps"][i]
        step["change_box"] = None if i == 0 else imaging.change_box(
            thumb(i - 1), thumb(i), doc["width"], doc["height"])


def render_image(ffmpeg, src, dest, step, doc, run, redacted=True):
    """Produce one screenshot from its original."""
    vf = build_filter(step, doc, redacted)
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


def redaction_wanted(doc):
    return doc.get("redact", True) or any(s.get("redact") for s in doc["steps"])


def ensure_redactions(out_dir, doc, ffmpeg, tesseract, progress=None, cancel=None):
    """Scan any step that has not been scanned for sensitive text yet.
    Without Tesseract nothing is scanned (manual blur boxes still apply)."""
    pending = [s for s in doc["steps"] if "auto_redactions" not in s]
    if not pending or not tesseract:
        if pending and not tesseract:
            log.warning("Tesseract OCR not found: sensitive text was not detected "
                        "automatically. Manual blur boxes still work.")
        return
    ensure_frame_size(out_dir, doc, ffmpeg)
    for i, step in enumerate(pending, 1):
        if cancel is not None and cancel.is_set():
            raise Cancelled()
        if progress is not None:
            progress((i - 1) / len(pending), f"Scanning for sensitive text {i}/{len(pending)}")
        step["auto_redactions"] = redact.scan_image(
            tesseract, Path(out_dir) / step["original"], doc["width"], doc["height"],
            doc.get("redact_patterns", []))
    found = sum(len(s["auto_redactions"]) for s in pending)
    log.info("  Sensitive text scan: %d area(s) to blur in %d screenshot(s)", found, len(pending))


def render(out_dir, doc, ffmpeg, progress=None, cancel=None, tesseract=None):
    """Re-render every screenshot from its original, remove stale ones, and
    save steps.md and steps.json. When redaction is on, an unblurred copy of
    every screenshot goes in unredacted/ with its own steps-unredacted.md."""
    out_dir = Path(out_dir)
    ext = doc.get("format", "png")
    keep = set()
    if doc.get("highlight", True) or any(s.get("highlight") for s in doc["steps"]):
        ensure_change_boxes(out_dir, doc, ffmpeg)
    redacting = redaction_wanted(doc)
    if redacting:
        ensure_redactions(out_dir, doc, ffmpeg, tesseract, progress, cancel)
    unredacted = out_dir / UNREDACTED_DIR
    if redacting:
        unredacted.mkdir(exist_ok=True)
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
        if redacting:
            render_image(ffmpeg, src, unredacted / name, step, doc, run_quiet, redacted=False)
        step["file"] = name
        keep.add(name)
    for folder in (out_dir, unredacted):
        for stale in folder.glob("step_*"):
            if stale.is_file() and stale.suffix.lower() in (".png", ".jpg") and \
                    (stale.name not in keep or (folder == unredacted and not redacting)):
                stale.unlink()
    if not redacting:
        if unredacted.is_dir() and not any(unredacted.iterdir()):
            unredacted.rmdir()
        (out_dir / UNREDACTED_INDEX).unlink(missing_ok=True)
    else:
        (out_dir / UNREDACTED_INDEX).write_text(markdown(doc, unredacted=True), encoding="utf-8")
    save(out_dir, doc)


# ---------------------------------------------------------------------------
# Markdown
# ---------------------------------------------------------------------------

def markdown(doc, unredacted=False):
    steps = doc["steps"]
    s = doc.get("settings", {})
    lines = [
        f"# {doc.get('document', {}).get('title') or 'Steps'}",
        "",
    ]
    if unredacted:
        lines += ["> **UNREDACTED COPY.** These screenshots are not blurred and may show "
                  "passwords, keys, or internal addresses. Do not publish or share this file. "
                  f"Use `{INDEX_NAME}` instead.", ""]
    lines += [
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
        image = f"{UNREDACTED_DIR}/{step['file']}" if unredacted else step["file"]
        lines += [f"![Step {i}]({image})", ""]
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
        step.pop("duplicate_of_time", None)
        pos = 0
        for i, existing in enumerate(doc["steps"]):
            if existing["time"] <= step["time"]:
                pos = i + 1
        doc["steps"].insert(pos, step)
    doc["deleted_steps"] = []
    return len(restored)
