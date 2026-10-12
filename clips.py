#!/usr/bin/env python3
#
# clips.py
# 2026-10-12
# Version: v1.0.0
#
# PURPOSE:
# Short animated GIF clips of single steps, for actions a still picture
# cannot show well (dragging, a menu opening on hover, a slider). A step's
# clip runs from just before the screen changes to when the next screen
# has settled, so it shows the action taken on that step. Clips are made
# with FFmpeg from the original recording, cropped like the screenshot, and
# blurred with the blur boxes of this step and the next one, so they do not
# show what the screenshots hide.
#
# Clips go in clips/ in the recording's output folder, named by the step's
# time in the recording (clips/clip_<time>.gif, so reordering steps does not
# make them again). They are only made for steps that have "clip": true,
# and only made again when something they depend on changes.

import hashlib
import json
import logging
import subprocess
from pathlib import Path

CLIP_DIR = "clips"
LEAD = 1.5          # seconds of the finished screen before the change
TAIL = 0.6          # seconds of the next screen once it has settled
MIN_LENGTH = 1.5
MAX_LENGTH = 6.0
FPS = 10
MAX_WIDTH = 960     # px; GIFs get big fast

NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
log = logging.getLogger("screencap")


def clip_name(step):
    ms = int(round(max(float(step["time"]), 0.0) * 1000))
    h, rem = divmod(ms, 3_600_000)
    m, rem = divmod(rem, 60_000)
    sec, ms = divmod(rem, 1000)
    return f"clip_{h:02d}-{m:02d}-{sec:02d}.{ms:03d}.gif"


def wanted(step):
    return bool(step.get("clip"))


def clip_range(step, doc):
    """(start, end) in seconds of the recording for a step's clip."""
    t = float(step["time"])
    duration = float(doc.get("duration") or 0) or None
    changes = [float(s["still_from"]) for s in doc["steps"] + doc.get("deleted_steps", [])
               if s.get("still_from") is not None and float(s["still_from"]) > t + 0.05]
    begin = step.get("still_from")
    start = t - LEAD if begin is None else max(float(begin), t - LEAD)
    end = min(changes) + TAIL if changes else t + 1.0
    end = min(end, start + MAX_LENGTH)
    if end - start < MIN_LENGTH:
        end = start + MIN_LENGTH
    if duration:
        end = min(end, duration)
        start = max(0.0, min(start, end - MIN_LENGTH))
    return max(0.0, start), end


def next_step(step, doc):
    later = [s for s in doc["steps"] if float(s["time"]) > float(step["time"])]
    return min(later, key=lambda s: float(s["time"])) if later else None


def blur_boxes(step, doc, redaction_boxes):
    """Blur boxes for a clip: this step's and the next step's, since the clip
    shows both screens."""
    boxes = list(redaction_boxes(step, doc))
    following = next_step(step, doc)
    if following is not None:
        boxes += [b for b in redaction_boxes(following, doc) if b not in boxes]
    return boxes


def gif_filter(width, crop, blur):
    """Filter graph: blur, crop, scale, then a palette made for this clip
    (GIFs have 256 colors)."""
    parts = []
    if crop:
        x, y, w, h = crop
        parts.append(f"crop={w}:{h}:{x}:{y}")
        width = w
    out_w = min(MAX_WIDTH, width or MAX_WIDTH)
    out_w -= out_w % 2
    parts += [f"fps={FPS}", f"scale={out_w}:-2:flags=lanczos"]
    chain = ",".join(parts)
    graph = (blur + "," if blur else "") + chain
    return (graph + ",split[c1][c2];[c1]palettegen=stats_mode=full[pal];"
            "[c2][pal]paletteuse=dither=bayer:bayer_scale=4")


def clip_key(video, start, end, vf):
    try:
        stat = Path(video).stat()
        stamp = [stat.st_size, int(stat.st_mtime)]
    except OSError:
        stamp = None
    data = json.dumps([str(video), stamp, round(start, 3), round(end, 3), vf])
    return hashlib.sha256(data.encode("utf-8")).hexdigest()[:16]


def make_clip(ffmpeg, video, dest, start, end, vf, run):
    tmp = Path(str(dest) + ".tmp.gif")
    cmd = [ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
           "-ss", f"{start:.3f}", "-t", f"{end - start:.3f}", "-i", str(video),
           "-filter_complex", vf, "-loop", "0", str(tmp)]
    res = run(cmd)
    if res.returncode != 0 or not tmp.is_file():
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"Making the clip {Path(dest).name} failed: "
                           f"{(res.stderr or '').strip()[-300:]}")
    tmp.replace(dest)


def render_clips(out_dir, doc, ffmpeg, run, crop_of, redaction_boxes, blur_graph,
                 progress=None):
    """Make or refresh the clip of every step that wants one, and remove
    clips nobody uses. Needs the original recording; when it is missing, an
    existing clip is kept and a warning is logged. Returns the number of
    clips in use."""
    out_dir = Path(out_dir)
    folder = out_dir / CLIP_DIR
    video = doc.get("source_path")
    video = Path(video) if video else None
    keep = set()
    todo = [(i, s) for i, s in enumerate(doc["steps"], 1) if wanted(s)]
    for n, (i, step) in enumerate(todo, 1):
        name = clip_name(step)
        dest = folder / name
        start, end = clip_range(step, doc)
        vf = gif_filter(doc.get("width"), crop_of(step, doc),
                        blur_graph(blur_boxes(step, doc, redaction_boxes)))
        if video is None or not video.is_file():
            if dest.is_file() and step.get("clip_file") == f"{CLIP_DIR}/{name}":
                keep.add(name)
            else:
                step.pop("clip_file", None)
                log.warning("Step %d: the clip could not be made because the recording "
                            "was not found (%s).", i, video or "unknown")
            continue
        key = clip_key(video, start, end, vf)
        if not (dest.is_file() and step.get("clip_key") == key):
            if progress is not None:
                progress((n - 1) / len(todo), f"Making animated clip {n}/{len(todo)}")
            folder.mkdir(exist_ok=True)
            try:
                make_clip(ffmpeg, video, dest, start, end, vf, run)
            except RuntimeError as exc:
                log.warning("Step %d: %s", i, exc)
                step.pop("clip_file", None)
                continue
        step["clip_key"] = key
        step["clip_file"] = f"{CLIP_DIR}/{name}"
        keep.add(name)
    for step in doc["steps"] + doc.get("deleted_steps", []):
        if not wanted(step) or (step in doc.get("deleted_steps", [])):
            step.pop("clip_file", None)
    if folder.is_dir():
        for f in folder.glob("*.gif"):
            if f.name not in keep:
                f.unlink(missing_ok=True)
        if not any(folder.iterdir()):
            folder.rmdir()
    return len(keep)


def clip_path(out_dir, step):
    """The step's clip file, or None when it has none (yet)."""
    rel = step.get("clip_file")
    if not rel or not wanted(step):
        return None
    path = Path(out_dir) / rel
    return path if path.is_file() else None
