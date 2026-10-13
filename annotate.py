#!/usr/bin/env python3
#
# annotate.py
# 2026-10-12
# Version: v1.1.0
#
# PURPOSE:
# Annotations drawn on a screenshot in the step editor: arrows, numbered
# markers, text labels, and click rings (added by the built-in recorder). Arrows and the round markers are drawn here in
# plain Python into a transparent PAM image the size of the original frame
# (no Pillow or NumPy), which FFmpeg lays over the screenshot. The numbers
# and the label text are drawn by FFmpeg's drawtext filter with a font found
# on the system.
#
# Each annotation is stored in the step, in original-frame pixels:
#   {"kind": "arrow", "from": [x, y], "to": [x, y]}     tip at "to"
#   {"kind": "number", "at": [x, y], "n": 1}            centered on "at"
#   {"kind": "text", "at": [x, y], "text": "Click here"} top-left corner at "at"
#   {"kind": "click", "at": [x, y]}                     a ring around a click
# Annotations made automatically from a recording also have "auto": true.

import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
from pathlib import Path

KINDS = ("arrow", "number", "text", "click")
OVERLAY_DIR = "overlays"           # cached arrow/marker images, inside each output folder
FILL = (0xE5, 0x39, 0x35)          # red, the same as the "what changed" box
OUTLINE = (0xFF, 0xFF, 0xFF)       # white edge, so red shows on red or dark screens
TEXT_COLOR = "white"

NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

FONT_MISSING_HELP = (
    "No font was found for annotation text and numbers. Install DejaVu Sans "
    "(Linux: sudo apt install fonts-dejavu-core), or set SCREENCAP_FONT to the "
    "path of a .ttf font file.")

# Bold sans-serif fonts that are normally present, in order of preference
FONT_CANDIDATES = {
    "nt": ["segoeuib.ttf", "arialbd.ttf", "tahomabd.ttf", "verdanab.ttf"],
    "darwin": ["/System/Library/Fonts/Supplemental/Arial Bold.ttf",
               "/Library/Fonts/Arial Bold.ttf",
               "/System/Library/Fonts/Helvetica.ttc"],
    "linux": ["DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf", "NotoSans-Bold.ttf",
              "FreeSansBold.ttf", "Arial_Bold.ttf", "arialbd.ttf"],
}
LINUX_FONT_DIRS = ["/usr/share/fonts", "/usr/local/share/fonts", "~/.local/share/fonts",
                   "~/.fonts", "/var/lib/snapd/hostfs/usr/share/fonts"]

_font_cache = {}


def find_font():
    """Path of a bold sans-serif .ttf for drawtext, or None. SCREENCAP_FONT
    overrides the search."""
    explicit = os.environ.get("SCREENCAP_FONT")
    if explicit:
        return explicit if Path(explicit).is_file() else None
    if "font" in _font_cache:
        return _font_cache["font"]
    found = None
    if os.name == "nt":
        fonts = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
        found = next((str(fonts / n) for n in FONT_CANDIDATES["nt"] if (fonts / n).is_file()),
                     None)
    elif sys.platform == "darwin":
        found = next((p for p in FONT_CANDIDATES["darwin"] if Path(p).is_file()), None)
    else:
        dirs = [Path(d).expanduser() for d in LINUX_FONT_DIRS]
        if os.environ.get("SNAP"):
            dirs.insert(0, Path(os.environ["SNAP"]) / "usr" / "share" / "fonts")
        for name in FONT_CANDIDATES["linux"]:
            for d in dirs:
                if d.is_dir():
                    hit = next(d.rglob(name), None)
                    if hit:
                        found = str(hit)
                        break
            if found:
                break
        if not found and shutil.which("fc-match"):
            res = subprocess.run(["fc-match", "-f", "%{file}", "sans:bold"],
                                 stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
            if res.returncode == 0 and res.stdout.lower().endswith((".ttf", ".otf", ".ttc")) \
                    and Path(res.stdout).is_file():
                found = res.stdout
    _font_cache["font"] = found
    return found


def filter_value(value):
    """Escape a value (a path or text) for an FFmpeg filter option, at both
    levels FFmpeg parses: the option value, then the filter graph."""
    s = str(value)
    s = s.replace("\\", "\\\\").replace("'", "\\'").replace(":", "\\:")
    for ch in "\\'[],;":
        s = s.replace(ch, "\\" + ch)
    return s


def filter_path(path):
    """A file path for a filter option; forward slashes work on Windows too."""
    return filter_value(str(path).replace("\\", "/"))


# ---------------------------------------------------------------------------
# Sizes (scaled to the frame, so annotations look the same at any resolution)
# ---------------------------------------------------------------------------

def sizes(width):
    w = width or 1280
    line = max(4, round(w / 200))          # arrow shaft thickness
    font = max(14, round(w / 64))          # label text size
    return {
        "line": line,
        "outline": max(2, round(line / 3)),
        "head_len": line * 5.0,
        "head_half": line * 3.0,
        "marker": max(12, round(font * 0.85)),   # marker radius
        "font": font,
        "marker_font": max(12, round(font * 0.95)),
        "pad": max(4, round(font / 3)),
    }


def valid(ann):
    kind = ann.get("kind")
    if kind == "arrow":
        return len(ann.get("from") or []) == 2 and len(ann.get("to") or []) == 2
    if kind in ("number", "click"):
        return len(ann.get("at") or []) == 2
    if kind == "text":
        return len(ann.get("at") or []) == 2 and bool((ann.get("text") or "").strip())
    return False


def step_annotations(step):
    return [a for a in step.get("annotations") or [] if valid(a)]


def next_number(step):
    numbers = [a.get("n", 0) for a in step_annotations(step) if a["kind"] == "number"]
    return max(numbers, default=0) + 1


# ---------------------------------------------------------------------------
# Drawing arrows and markers into an RGBA image
# ---------------------------------------------------------------------------

class _Capsule:
    """A thick line with round ends."""

    def __init__(self, a, b, r):
        self.a, self.b, self.r = a, b, r
        dx, dy = b[0] - a[0], b[1] - a[1]
        self.dx, self.dy, self.len2 = dx, dy, dx * dx + dy * dy

    def sdist(self, x, y):
        ax, ay = self.a
        t = 0.0 if self.len2 == 0 else max(0.0, min(1.0, ((x - ax) * self.dx + (y - ay) * self.dy)
                                                     / self.len2))
        return math.hypot(x - (ax + t * self.dx), y - (ay + t * self.dy)) - self.r

    def bounds(self, grow):
        r = self.r + grow
        return (min(self.a[0], self.b[0]) - r, min(self.a[1], self.b[1]) - r,
                max(self.a[0], self.b[0]) + r, max(self.a[1], self.b[1]) + r)

    def row_span(self, y, grow):
        """x range that can be within reach on row y (the rest is skipped)."""
        r = self.r + grow
        (ax, ay), (bx, by) = self.a, self.b
        if abs(by - ay) < 1e-9:
            if abs(y - ay) > r:
                return None
            return min(ax, bx) - r, max(ax, bx) + r
        t0, t1 = sorted(((y - r - ay) / (by - ay), (y + r - ay) / (by - ay)))
        t0, t1 = max(0.0, t0), min(1.0, t1)
        if t0 > t1:
            return None
        x0, x1 = sorted((ax + t0 * (bx - ax), ax + t1 * (bx - ax)))
        return x0 - r, x1 + r


class _Polygon:
    """A convex polygon (the arrow head)."""

    def __init__(self, points):
        area = sum(points[i][0] * points[i - 1][1] - points[i - 1][0] * points[i][1]
                   for i in range(len(points)))
        self.points = points if area < 0 else points[::-1]
        self.edges = []
        for i in range(len(self.points)):
            (x0, y0), (x1, y1) = self.points[i - 1], self.points[i]
            length = math.hypot(x1 - x0, y1 - y0) or 1.0
            # outward normal of the edge
            self.edges.append((x0, y0, (y1 - y0) / length, -(x1 - x0) / length))

    def sdist(self, x, y):
        return max((x - x0) * nx + (y - y0) * ny for x0, y0, nx, ny in self.edges)

    def bounds(self, grow):
        xs = [p[0] for p in self.points]
        ys = [p[1] for p in self.points]
        return min(xs) - grow, min(ys) - grow, max(xs) + grow, max(ys) + grow

    def row_span(self, y, grow):
        x0, y0, x1, y1 = self.bounds(grow)
        return (x0, x1) if y0 <= y <= y1 else None


class _Circle:
    def __init__(self, c, r):
        self.c, self.r = c, r

    def sdist(self, x, y):
        return math.hypot(x - self.c[0], y - self.c[1]) - self.r

    def bounds(self, grow):
        r = self.r + grow
        return self.c[0] - r, self.c[1] - r, self.c[0] + r, self.c[1] + r

    def row_span(self, y, grow):
        r = self.r + grow
        dy = y - self.c[1]
        if abs(dy) > r:
            return None
        half = math.sqrt(r * r - dy * dy)
        return self.c[0] - half, self.c[0] + half


class _Ring:
    """A circle outline (a click)."""

    def __init__(self, c, r, thickness):
        self.c, self.r, self.half = c, r, thickness / 2

    def sdist(self, x, y):
        return abs(math.hypot(x - self.c[0], y - self.c[1]) - self.r) - self.half

    def bounds(self, grow):
        r = self.r + self.half + grow
        return self.c[0] - r, self.c[1] - r, self.c[0] + r, self.c[1] + r

    def row_span(self, y, grow):
        r = self.r + self.half + grow
        dy = y - self.c[1]
        if abs(dy) > r:
            return None
        half = math.sqrt(r * r - dy * dy)
        return self.c[0] - half, self.c[0] + half


def ring_radius(sz):
    return sz["marker"] * 1.25


def arrow_shapes(start, tip, sz):
    """Shaft and head of an arrow from start to tip."""
    dx, dy = tip[0] - start[0], tip[1] - start[1]
    length = math.hypot(dx, dy)
    if length < 1:
        return []
    ux, uy = dx / length, dy / length
    head = min(sz["head_len"], length * 0.6)
    half = sz["head_half"] * head / sz["head_len"]
    base = (tip[0] - ux * head, tip[1] - uy * head)
    shapes = [_Polygon([tuple(tip), (base[0] - uy * half, base[1] + ux * half),
                        (base[0] + uy * half, base[1] - ux * half)])]
    if length - head > 0.5:
        # the shaft runs a little into the head so they join without a gap
        join = (base[0] + ux * head * 0.3, base[1] + uy * head * 0.3)
        shapes.append(_Capsule(tuple(start), join, sz["line"] / 2))
    return shapes


def shape_groups(annotations, width):
    """Shapes to draw, one group per annotation (each group gets one white
    edge around its union, so an arrow's head and shaft merge cleanly)."""
    sz = sizes(width)
    groups = []
    for ann in annotations:
        if ann["kind"] == "arrow":
            shapes = arrow_shapes(ann["from"], ann["to"], sz)
            if shapes:
                groups.append(shapes)
        elif ann["kind"] == "number":
            groups.append([_Circle(tuple(ann["at"]), sz["marker"])])
        elif ann["kind"] == "click":
            groups.append([_Ring(tuple(ann["at"]), ring_radius(sz), sz["line"])])
    return groups


def draw_rgba(width, height, annotations):
    """RGBA pixels (bytes) of the arrows and markers on a transparent frame,
    with a white edge and anti-aliased borders."""
    sz = sizes(width)
    edge = sz["outline"]
    grow = edge + 1.0
    buf = bytearray(width * height * 4)
    for group in shape_groups(annotations, width):
        y0 = min(s.bounds(grow)[1] for s in group)
        y1 = max(s.bounds(grow)[3] for s in group)
        for py in range(max(0, int(y0)), min(height, int(math.ceil(y1)) + 1)):
            cy = py + 0.5
            spans = [s.row_span(cy, grow) for s in group]
            spans = [sp for sp in spans if sp]
            if not spans:
                continue
            lo = max(0, int(min(sp[0] for sp in spans)))
            hi = min(width, int(math.ceil(max(sp[1] for sp in spans))) + 1)
            row = py * width * 4
            for px in range(lo, hi):
                cx = px + 0.5
                d = min(s.sdist(cx, cy) for s in group)
                if d >= edge + 0.5:
                    continue
                fill = min(1.0, max(0.0, 0.5 - d))           # 1 inside the shape
                cover = min(1.0, max(0.0, edge + 0.5 - d))    # 1 inside shape + edge
                r = OUTLINE[0] + (FILL[0] - OUTLINE[0]) * fill
                g = OUTLINE[1] + (FILL[1] - OUTLINE[1]) * fill
                b = OUTLINE[2] + (FILL[2] - OUTLINE[2]) * fill
                i = row + px * 4
                old_a = buf[i + 3] / 255.0
                if old_a <= 0.0:
                    buf[i:i + 4] = bytes((round(r), round(g), round(b), round(cover * 255)))
                else:   # lay this shape over one drawn earlier
                    a = cover + old_a * (1 - cover)
                    mix = cover / a
                    buf[i] = round(r * mix + buf[i] * (1 - mix))
                    buf[i + 1] = round(g * mix + buf[i + 1] * (1 - mix))
                    buf[i + 2] = round(b * mix + buf[i + 2] * (1 - mix))
                    buf[i + 3] = round(a * 255)
    return bytes(buf)


def write_pam(path, width, height, rgba):
    header = (f"P7\nWIDTH {width}\nHEIGHT {height}\nDEPTH 4\nMAXVAL 255\n"
              "TUPLTYPE RGB_ALPHA\nENDHDR\n").encode("ascii")
    tmp = Path(str(path) + ".tmp")
    tmp.write_bytes(header + rgba)
    os.replace(tmp, path)


def _shapes(annotations):
    return [a for a in annotations if a["kind"] in ("arrow", "number", "click")]


def overlay_name(width, height, annotations):
    """File name of the arrow/marker image for these annotations (it changes
    whenever they do), or None when there is nothing to draw."""
    drawn = _shapes(annotations)
    if not drawn or not width or not height:
        return None
    key = json.dumps([width, height, sizes(width), drawn], sort_keys=True)
    return "shapes_" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:16] + ".pam"


def overlay_file(work_dir, width, height, annotations):
    """The cached arrow/marker image for these annotations, drawn if needed.
    None when there is nothing to draw (only text labels, or no annotations)."""
    name = overlay_name(width, height, annotations)
    if not name:
        return None
    drawn = _shapes(annotations)
    folder = Path(work_dir) / OVERLAY_DIR
    path = folder / name
    if not path.is_file():
        folder.mkdir(exist_ok=True)
        write_pam(path, width, height, draw_rgba(width, height, drawn))
    return path


def remove_stale_overlays(work_dir, keep):
    folder = Path(work_dir) / OVERLAY_DIR
    if not folder.is_dir():
        return
    for f in folder.glob("shapes_*.pam"):
        if f.name not in keep:
            f.unlink(missing_ok=True)
    if not any(folder.iterdir()):
        folder.rmdir()


# ---------------------------------------------------------------------------
# FFmpeg filters
# ---------------------------------------------------------------------------

def text_filters(annotations, width, font):
    """drawtext filters for the marker numbers and the text labels."""
    sz = sizes(width)
    out = []
    font_opt = f"fontfile={filter_path(font)}"
    for ann in annotations:
        if ann["kind"] == "number":
            cx, cy = (round(v) for v in ann["at"])
            out.append(f"drawtext={font_opt}:text={filter_value(ann.get('n', 1))}"
                       f":expansion=none:fontsize={sz['marker_font']}:fontcolor={TEXT_COLOR}"
                       f":x={cx}-text_w/2:y={cy}-text_h/2")
        elif ann["kind"] == "text":
            x, y = (round(v) for v in ann["at"])
            pad = sz["pad"]
            color = "0x%02X%02X%02X" % FILL
            out.append(f"drawtext={font_opt}:text={filter_value(ann['text'].strip())}"
                       f":expansion=none:fontsize={sz['font']}:fontcolor={TEXT_COLOR}"
                       f":box=1:boxcolor={color}@0.95:boxborderw={pad}"
                       f":x={x + pad}:y={y + pad}")
    return out


def filters(step, width, height, work_dir, font=None):
    """(overlay image or None, list of drawtext filters) for a step's
    annotations. Raises RuntimeError when text is needed but no font exists."""
    anns = step_annotations(step)
    if not anns or not width or not height:
        return None, []
    image = overlay_file(work_dir, width, height, anns)
    texts = []
    if any(a["kind"] in ("number", "text") for a in anns):
        font = font or find_font()
        if not font:
            raise RuntimeError(FONT_MISSING_HELP)
        texts = text_filters(anns, width, font)
    return image, texts


def label_size(text, width):
    """Rough on-screen size of a text label, in original-frame pixels (for
    picking it with the mouse; FFmpeg decides the exact size)."""
    sz = sizes(width)
    return len(text) * sz["font"] * 0.6 + 2 * sz["pad"], sz["font"] * 1.25 + 2 * sz["pad"]


def hit(ann, x, y, width):
    """Distance from (x, y) to an annotation, or None when it is not near."""
    sz = sizes(width)
    reach = max(12, sz["font"])
    if ann["kind"] == "arrow":
        d = _Capsule(tuple(ann["from"]), tuple(ann["to"]), 0).sdist(x, y)
    elif ann["kind"] == "number":
        d = _Circle(tuple(ann["at"]), sz["marker"]).sdist(x, y)
    elif ann["kind"] == "click":
        d = max(0.0, _Circle(tuple(ann["at"]), ring_radius(sz)).sdist(x, y))
    else:
        w, h = label_size(ann["text"], width)
        ax, ay = ann["at"]
        dx = max(ax - x, 0, x - (ax + w))
        dy = max(ay - y, 0, y - (ay + h))
        d = math.hypot(dx, dy)
    return d if d <= reach else None
