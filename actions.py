#!/usr/bin/env python3
#
# actions.py
# 2026-10-25
# Version: v1.3.0
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

import difflib
import logging
import os
import subprocess
import tempfile
from pathlib import Path

import recorder
import redact
import workers

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


def _is_word(text):
    """True for real words; OCR also reads borders, carets, and the text
    cursor as | or I, which must not count as the clicked words."""
    return sum(c.isalnum() for c in text) >= 2


def click_label(lines, x, y, width):
    """Text of the button, link, or item at (x, y), from OCR lines (lists of
    (text, [x, y, w, h])). None when nothing readable is there."""
    reach = max(14, width // 90)
    best = None
    for li, words in enumerate(lines):
        for wi, (text, (bx, by, bw, bh)) in enumerate(words):
            dx = max(bx - x, 0, x - (bx + bw))
            dy = max(by - y, 0, y - (by + bh))
            if not _is_word(text) or dy > reach or dx > reach * 2:
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
            if not _is_word(text) or not (by - bh <= y <= by + 2 * bh):
                continue
            gap = x - (bx + bw)
            if 0 <= gap <= reach and (best is None or gap < best[0]):
                best = (gap, li, wi)
    if best is None:
        return None
    return _phrase(lines[best[1]], best[2], leftward=True)


def above_label(lines, x, y, width):
    """Text just above (x, y) and starting left of it, such as the label
    over an empty text box on a web form. None when there is none. Of the
    labels on the row above, the nearest one left of the click is taken: in
    two columns of boxes, the one over the right column belongs to it."""
    reach_y, reach_x = max(30, width // 40), max(300, width // 3)
    best = None
    for li, words in enumerate(lines):
        for wi, (text, (bx, by, bw, bh)) in enumerate(words):
            gap_y = y - (by + bh)
            if not _is_word(text) or not 0 <= gap_y <= reach_y or not 0 <= x - bx <= reach_x:
                continue
            d = (gap_y // max(bh, 1), x - bx)
            if best is None or d < best[0]:
                best = (d, li, wi)
    if best is None:
        return None
    return _phrase(lines[best[1]], best[2])


def right_label(lines, x, y, width):
    """Text just right of (x, y), such as the label of a checkbox or option
    button that was clicked on its box. None when there is none. Only words
    that start just beside the click count: a label sits next to its box,
    while words farther right belong to another control (the next button
    over when the clicked button could not be read)."""
    reach = max(36, width // 40)
    best = None
    for li, words in enumerate(lines):
        for wi, (text, (bx, by, bw, bh)) in enumerate(words):
            if not _is_word(text) or not (by - bh <= y <= by + 2 * bh):
                continue
            gap = bx - x
            if 0 <= gap <= reach and (best is None or gap < best[0]):
                best = (gap, li, wi)
    if best is None:
        return None
    return _phrase(lines[best[1]], best[2])


def _phrase(words, wi, leftward=False):
    """The run of closely spaced words around words[wi], cleaned up."""
    def joins(a, b):    # a symbol-only token (|, <, >) is an edge between two buttons
        return _gap_ok(words[a][1], words[b][1]) and \
            any(c.isalnum() for c in words[a][0]) and any(c.isalnum() for c in words[b][0])
    lo = hi = wi
    while lo > 0 and joins(lo - 1, lo) and hi - lo + 1 < LABEL_WORDS:
        lo -= 1
    while not leftward and hi + 1 < len(words) and joins(hi, hi + 1) and \
            hi - lo + 1 < LABEL_WORDS:
        hi += 1
    text = " ".join(w for w, _ in words[lo:hi + 1])
    text = text.strip(" .:;,|>\u00bb<\u00ab*_-\u2014\u2013\"'`()[]{}")
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


def tight_area(x, y, width, height):
    """[x, y, w, h] of a button-sized area around a click, read as one line
    when the wider area gave nothing (the mouse pointer sits on the words)."""
    half_w, half_h = max(160, width // 12), max(28, height // 40)
    x0, y0 = max(0, x - half_w), max(0, y - half_h)
    x1, y1 = min(width, x + half_w), min(height, y + half_h)
    return [x0, y0, x1 - x0, y1 - y0]


def words_at(ffmpeg, tesseract, video, t, area, tmp, psm=11):
    """OCR lines in area of the recording at time t, in frame pixels. Gray,
    enlarged pixels read best, even with the mouse pointer over a letter."""
    x, y, w, h = area
    fd, image = tempfile.mkstemp(prefix="click_", suffix=".png", dir=tmp)
    os.close(fd)   # a name of its own, so reads running at the same time never mix
    image = Path(image)
    res = subprocess.run([ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
                          "-ss", f"{max(t - 0.05, 0):.3f}", "-i", str(video),
                          "-frames:v", "1", "-vf",
                          f"crop={w}:{h}:{x}:{y},scale=iw*{OCR_SCALE}:-1:flags=lanczos,"
                          "format=gray",
                          str(image)],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                         errors="replace", stdin=subprocess.DEVNULL, creationflags=NO_WINDOW)
    if res.returncode != 0 or not image.is_file():
        raise RuntimeError(res.stderr.strip()[-200:])
    lines = redact.read_words(tesseract, image, psm=psm, min_conf=MIN_CONF)
    return [[(text, [x + bx // OCR_SCALE, y + by // OCR_SCALE, bw // OCR_SCALE,
                     bh // OCR_SCALE]) for text, (bx, by, bw, bh) in words]
            for words in lines]


LOOK_BACK = 1.0     # seconds; the pointer is usually not on the words yet


def fuller_label(label, a, video, ffmpeg, tesseract, area, width, tmp):
    """The pointer often covers part of the clicked words ("Ne" for "Next").
    Read the same place a moment earlier and take that reading when it is
    the same words read better, so a screen that changed in between cannot
    give a wrong label."""
    if a["t"] < LOOK_BACK:
        return label
    try:
        before = words_at(ffmpeg, tesseract, video, a["t"] - LOOK_BACK, area, tmp)
    except (RuntimeError, OSError):
        return label
    earlier = click_label(before, a["x"], a["y"], width) or \
        right_label(before, a["x"], a["y"], width)
    if earlier and len(earlier) >= len(label) and same_words(earlier, label):
        return earlier
    return label


def same_words(clean, read):
    """True when read is clean with letters lost or misread under the
    pointer ("Ne" or "Confjpue" for "Continue", "ck Done" for "Done")."""
    a, b = clean.lower(), read.lower()
    return a in b or b in a or difflib.SequenceMatcher(None, a, b).ratio() >= 0.6


def label_actions(acts, video, ffmpeg, tesseract, width, height, extra, tmp):
    """Add "label" (the words clicked) or "near" (the words beside an empty
    spot) to clicks and drags, reading several at once."""
    clicks = [a for a in acts if a["type"] in ("click", "drag")]
    workers.run_all(lambda a: label_action(a, video, ffmpeg, tesseract, width, height,
                                           extra, tmp), clicks)


def narrow_area(x, y, width, height):
    """[x, y, w, h] of just the button under a click: the button-sized area
    can take in the buttons on both sides, whose colors spoil the reading."""
    half_w, half_h = max(80, width // 20), max(14, height // 70)
    x0, y0 = max(0, x - half_w), max(0, y - half_h)
    x1, y1 = min(width, x + half_w), min(height, y + half_h)
    return [x0, y0, x1 - x0, y1 - y0]


def button_label(a, video, ffmpeg, tesseract, width, height, tmp):
    """The words on the button under a click, read as one line from a
    button-sized area, then from just the button. The pointer on the words
    can spoil them ("mm continue") or hide them, so a reading from a moment
    earlier is taken when it holds the same words or nothing else was read.
    None when nothing is readable."""
    def read(area, t):
        try:
            return click_label(words_at(ffmpeg, tesseract, video, t, area, tmp, psm=7),
                               a["x"], a["y"], width)
        except (RuntimeError, OSError) as exc:
            log.debug("  Reading the words at a click failed: %s", exc)
            return None
    for area in (tight_area(a["x"], a["y"], width, height),
                 narrow_area(a["x"], a["y"], width, height)):
        label = read(area, a["t"])
        earlier = read(area, a["t"] - LOOK_BACK) if a["t"] >= LOOK_BACK else None
        if earlier and (not label or same_words(earlier, label)):
            return earlier
        if label:
            return label
    return None


def label_action(a, video, ffmpeg, tesseract, width, height, extra, tmp):
    """label_actions() for one click or drag."""
    area = crop_around(a["x"], a["y"], width, height)
    try:
        lines = words_at(ffmpeg, tesseract, video, a["t"], area, tmp)
    except (RuntimeError, OSError) as exc:
        log.debug("  Reading the words at a click failed: %s", exc)
        return
    label = click_label(lines, a["x"], a["y"], width)
    if label:
        label = fuller_label(label, a, video, ffmpeg, tesseract, area, width, tmp)
    else:
        # The clicked button itself comes before any words beside it: light
        # text on a colored button ("Continue" in white on green) is often
        # not read in the wide area, and the next button over must not be
        # taken for it
        label = button_label(a, video, ffmpeg, tesseract, width, height, tmp) or \
            right_label(lines, a["x"], a["y"], width)
    label = safe_label(label, extra)
    if label:
        a["label"] = label
    elif a["type"] == "click":
        near = safe_label(nearby_label(lines, a["x"], a["y"], width) or
                          above_label(lines, a["x"], a["y"], width), extra)
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
    if read:
        wanted = [a for step in steps for a in per_step.get(id(step), [])[:MAX_ACTIONS + 1]]
        with tempfile.TemporaryDirectory(prefix="screencap_clicks_") as tmp:
            label_actions(wanted, video, ffmpeg, tesseract, width, height, extra, tmp)
    for step in steps:
        acts = per_step.get(id(step), [])
        if acts:
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

