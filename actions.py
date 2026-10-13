#!/usr/bin/env python3
#
# actions.py
# 2026-10-12
# Version: v1.0.0
#
# PURPOSE:
# Uses the clicks and keys noted by the built-in recorder (recorder.py) to
# describe each step: every action is given to the step whose screen it was
# done on, each click gets a red ring on the screenshot (a drag gets an
# arrow), and an empty caption is filled with a first draft such as
#   Click "Next".
#   Click "User name", type the text, then press Tab.
# The words of a clicked button or menu item are read with Tesseract OCR,
# when it is installed, from the recording at the moment of the click (not
# from the screenshot, which can already show text typed afterwards). Words that look sensitive (the
# same patterns that are blurred) are never put in a caption.

import logging
import subprocess
import tempfile
from pathlib import Path

import recorder
import redact

log = logging.getLogger("screencap")

TOLERANCE = 0.4         # seconds; a click this soon after a change still belongs before it
MAX_MARKS = 5           # click rings per step
MAX_ACTIONS = 4         # actions written out in one caption
LABEL_WORDS = 5
LABEL_CHARS = 40
VERBS = {"left": "Click", "right": "Right-click", "middle": "Middle-click"}


def to_frame(events, width, height):
    """Map screen coordinates to recording pixels."""
    screen = events.get("screen") or [0, 0, width, height]
    sx, sy, sw, sh = screen
    kx = width / sw if sw else 1.0
    ky = height / sh if sh else 1.0

    def conv(x, y):
        return [min(max(round((x - sx) * kx), 0), width - 1),
                min(max(round((y - sy) * ky), 0), height - 1)]
    out = []
    for e in events.get("events") or []:
        e = dict(e)
        if "x" in e and "y" in e:
            e["x"], e["y"] = conv(e["x"], e["y"])
        if "x2" in e and "y2" in e:
            e["x2"], e["y2"] = conv(e["x2"], e["y2"])
        out.append(e)
    return out


def boundary(step, following):
    """End of the time when a step's screen was on show: when the next
    change started (plus a little, since clicks come before the change)."""
    if step.get("still_to") is not None:
        end = float(step["still_to"])
    elif following is not None:
        end = float(following["still_from"] if following.get("still_from") is not None
                    else following["time"])
    else:
        return None
    return end + TOLERANCE


def assign(steps, events):
    """{id(step): [events]} for steps sorted by time."""
    ordered = sorted(steps, key=lambda s: float(s["time"]))
    out = {id(s): [] for s in ordered}
    if not ordered:
        return out
    # the last step takes everything after it (the recording ends there)
    ends = [boundary(s, ordered[i + 1]) for i, s in enumerate(ordered[:-1])] + [None]
    for e in sorted(events, key=lambda e: e["t"]):
        for s, end in zip(ordered, ends):
            if end is None or e["t"] < end:
                out[id(s)].append(e)
                break
    return out


# ---------------------------------------------------------------------------
# Words under a click
# ---------------------------------------------------------------------------

def _gap_ok(a, b):
    """True when word box b follows a closely on the same line."""
    h = max(a[3], b[3], 1)
    return 0 <= b[0] - (a[0] + a[2]) <= h * 0.9


def click_label(lines, x, y, width):
    """Text of the button, link, or item at (x, y), from OCR lines (lists of
    (text, [x, y, w, h])). None when nothing readable is there."""
    reach = max(14, width // 90)
    best = None
    for li, words in enumerate(lines):
        for wi, (text, (bx, by, bw, bh)) in enumerate(words):
            dx = max(bx - x, 0, x - (bx + bw))
            dy = max(by - y, 0, y - (by + bh))
            if dy > reach or dx > reach * 2:
                continue
            d = dx + dy * 2
            if best is None or d < best[0]:
                best = (d, li, wi)
    if best is None:
        return None
    return _phrase(lines[best[1]], best[2])


def nearby_label(lines, x, y, width):
    """Text just left of (x, y) on the same row, such as the label of an
    empty text box that was clicked. None when there is none."""
    reach = max(40, width // 5)
    best = None
    for li, words in enumerate(lines):
        for wi, (text, (bx, by, bw, bh)) in enumerate(words):
            if not (by - bh <= y <= by + 2 * bh):
                continue
            gap = x - (bx + bw)
            if 0 <= gap <= reach and (best is None or gap < best[0]):
                best = (gap, li, wi)
    if best is None:
        return None
    return _phrase(lines[best[1]], best[2], leftward=True)


def _phrase(words, wi, leftward=False):
    """The run of closely spaced words around words[wi], cleaned up."""
    lo = hi = wi
    while lo > 0 and _gap_ok(words[lo - 1][1], words[lo][1]) and hi - lo + 1 < LABEL_WORDS:
        lo -= 1
    while not leftward and hi + 1 < len(words) and \
            _gap_ok(words[hi][1], words[hi + 1][1]) and hi - lo + 1 < LABEL_WORDS:
        hi += 1
    text = " ".join(w for w, _ in words[lo:hi + 1])
    text = text.strip(" .:;,|>»<«*_-—–\"'`()[]{}")
    if len(text) > LABEL_CHARS:
        text = text[:LABEL_CHARS].rsplit(" ", 1)[0]
    letters = sum(c.isalnum() for c in text)
    if letters < 2 or letters < len(text) * 0.5:
        return None
    return text


def safe_label(text, extra_patterns=()):
    """The label, or None when it looks like something that is blurred."""
    if not text:
        return None
    width = 10_000
    lines = [[(w, [i * 10, 0, 8, 8]) for i, w in enumerate(text.split())]]
    if redact.find_sensitive(lines, width, width, extra_patterns):
        return None
    return text


# ---------------------------------------------------------------------------
# Captions
# ---------------------------------------------------------------------------

def describe(event, label=None):
    kind = event["type"]
    if kind == "click":
        verb = "Double-click" if event.get("count", 1) == 2 and event["button"] == "left" \
            else VERBS.get(event["button"], "Click")
        if event.get("count", 1) > 2:
            verb = f"{verb} {event['count']} times on"
        if label:
            return f'{verb} "{label}"'
        if event.get("near"):
            return f'{verb} next to "{event["near"]}"'
        return f"{verb} the marked spot"
    if kind == "drag":
        return f'Drag "{label}" to where the arrow points' if label else \
            "Drag from the marked spot to where the arrow points"
    if kind == "typing":
        return "type the text"
    if kind == "key":
        n = event.get("count", 1)
        return f"press {event['key']}" + (f" {n} times" if n > 1 else "")
    if kind == "shortcut":
        return f"press {event['keys']}"
    return None


def caption(actions):
    """First-draft caption for a step's actions (dicts with an optional
    "label"), or "" when there are none."""
    parts = [p for p in (describe(a, a.get("label")) for a in actions) if p]
    if not parts:
        return ""
    more = len(parts) > MAX_ACTIONS
    parts = parts[:MAX_ACTIONS]
    parts = [p[0].lower() + p[1:] if i and p.split(" ")[0] in
             ("Click", "Double-click", "Right-click", "Middle-click", "Drag") else p
             for i, p in enumerate(parts)]
    if len(parts) == 1:
        text = parts[0]
    else:
        text = ", ".join(parts[:-1]) + (", then " if not more else ", ") + parts[-1]
    if more:
        text += ", and so on"
    return text[0].upper() + text[1:] + "."


def marks(actions):
    """Click rings and drag arrows for a step's actions."""
    out = []
    for a in actions:
        if len(out) >= MAX_MARKS:
            break
        if a["type"] == "click":
            out.append({"kind": "click", "at": [a["x"], a["y"]], "auto": True})
        elif a["type"] == "drag":
            out.append({"kind": "arrow", "from": [a["x"], a["y"]], "to": [a["x2"], a["y2"]],
                        "auto": True})
    return out


NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
OCR_SCALE = 2           # small screen text reads better enlarged
MIN_CONF = 60           # Tesseract confidence below which a word is ignored


def crop_around(x, y, width, height):
    """[x, y, w, h] of the area read around a click: wide enough for the
    label left of a text box."""
    half_w, half_h = max(400, width // 3), max(90, height // 10)
    x0, y0 = max(0, x - half_w), max(0, y - half_h)
    x1, y1 = min(width, x + half_w), min(height, y + half_h)
    return [x0, y0, x1 - x0, y1 - y0]


def words_at(ffmpeg, tesseract, video, t, area, tmp):
    """OCR lines in area of the recording at time t, in frame pixels."""
    x, y, w, h = area
    image = Path(tmp) / f"click_{t:.3f}.png"
    res = subprocess.run([ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
                          "-ss", f"{max(t - 0.05, 0):.3f}", "-i", str(video),
                          "-frames:v", "1", "-vf",
                          f"crop={w}:{h}:{x}:{y},scale=iw*{OCR_SCALE}:-1:flags=lanczos",
                          str(image)],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                         errors="replace", stdin=subprocess.DEVNULL, creationflags=NO_WINDOW)
    if res.returncode != 0 or not image.is_file():
        raise RuntimeError(res.stderr.strip()[-200:])
    lines = redact.read_words(tesseract, image, psm=11, min_conf=MIN_CONF)
    return [[(text, [x + bx // OCR_SCALE, y + by // OCR_SCALE, bw // OCR_SCALE,
                     bh // OCR_SCALE]) for text, (bx, by, bw, bh) in words]
            for words in lines]


def label_actions(acts, video, ffmpeg, tesseract, width, height, extra, tmp):
    """Add "label" (the words clicked) or "near" (the words beside an empty
    spot) to clicks and drags."""
    for a in acts:
        if a["type"] not in ("click", "drag"):
            continue
        area = crop_around(a["x"], a["y"], width, height)
        try:
            lines = words_at(ffmpeg, tesseract, video, a["t"], area, tmp)
        except (RuntimeError, OSError) as exc:
            log.debug("  Reading the words at a click failed: %s", exc)
            continue
        label = safe_label(click_label(lines, a["x"], a["y"], width), extra)
        if label:
            a["label"] = label
        elif a["type"] == "click":
            near = safe_label(nearby_label(lines, a["x"], a["y"], width), extra)
            if near:
                a["near"] = near


def apply(out_dir, doc, events, tesseract=None, mark=True, video=None, ffmpeg=None):
    """Give each step its actions, click marks, and (when empty) a caption.
    Clicked words are read when tesseract, video, and ffmpeg are given.
    Returns the number of steps that got a caption."""
    width, height = doc.get("width"), doc.get("height")
    if not width or not height:
        return 0
    frame_events = to_frame(events, width, height)
    steps = doc["steps"]
    per_step = assign(steps, frame_events)
    extra = doc.get("redact_patterns") or []
    filled = 0
    read = bool(tesseract and video and ffmpeg)
    with tempfile.TemporaryDirectory(prefix="screencap_clicks_") as tmp:
        for step in steps:
            acts = per_step.get(id(step), [])
            if not acts:
                continue
            if read:
                label_actions(acts[:MAX_ACTIONS + 1], video, ffmpeg, tesseract, width, height,
                              extra, tmp)
            filled += _describe_step(step, acts, mark)
    return filled


def _describe_step(step, acts, mark):
    """Store a step's actions, its click marks, and a caption when it has
    none. Returns 1 when a caption was written."""
    step["actions"] = acts
    if mark:
        kept = [a for a in step.get("annotations") or [] if not a.get("auto")]
        step["annotations"] = kept + marks(acts)
    if (step.get("caption") or "").strip():
        return 0
    text = caption(acts)
    if not text:
        return 0
    step["caption"] = text
    step["caption_auto"] = True
    return 1


def apply_recording(out_dir, doc, video, tesseract=None, mark=True, ffmpeg=None):
    """apply() with the events file next to video, when there is one."""
    events = recorder.load_events(video)
    if events is None:
        return None
    if events.get("input_error"):
        log.warning("  %s", events["input_error"])
    filled = apply(out_dir, doc, events, tesseract, mark, video=video, ffmpeg=ffmpeg)
    n = len(events.get("events") or [])
    log.info("  Recorder: %d click(s) and key(s) noted, %d caption(s) written", n, filled)
    return filled

