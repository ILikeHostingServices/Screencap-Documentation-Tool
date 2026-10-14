#!/usr/bin/env python3
#
# imaging.py
# 2026-10-14
# Version: v1.2.0
#
# PURPOSE:
# Small image comparisons done with FFmpeg and the Python standard library
# (no Pillow or NumPy): grayscale thumbnails, how much of the picture
# differs between two screenshots (duplicate detection), and where it
# differs (the "what changed" highlight box).

import re
import subprocess

NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

DEDUP_SIZE = (160, 90)     # comparison size for duplicate detection
CHANGE_SIZE = (320, 180)   # comparison size for locating what changed
CELL = 10                  # changed-area grid cell size at CHANGE_SIZE
CELL_MIN_PIXELS = 3        # changed pixels needed to mark a cell as changed
MINOR_RATIO = 0.25         # other areas must be this big vs the main change
MAX_BOX_AREA = 0.5         # bigger changes (a new window) are not boxed
PIXEL_DELTA = 24           # 0-255 gray difference that counts as "changed"
EDGE_DELTA = 48            # stronger difference used to place the box edges,
                           # so faint compression noise does not widen the box


def thumbnail(ffmpeg, path, size=DEDUP_SIZE):
    """Return the image as raw 8-bit grayscale bytes at the given size.
    Area scaling averages pixels, so a small mouse cursor mostly vanishes."""
    w, h = size
    res = subprocess.run([ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin",
                          "-i", str(path), "-vf", f"scale={w}:{h}:flags=area,format=gray",
                          "-f", "rawvideo", "-"],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         stdin=subprocess.DEVNULL, creationflags=NO_WINDOW)
    if res.returncode != 0 or len(res.stdout) != w * h:
        raise RuntimeError(f"Could not read {path}: {res.stderr.decode(errors='replace')[-200:]}")
    return res.stdout


def changed_rows(a, b, width):
    """Start offsets of the rows that differ at all. Comparing whole rows is
    done in C, so the pixel loops below only visit rows that changed (on a
    screen recording, most rows of two steps are identical)."""
    return [i for i in range(0, len(a), width) if a[i:i + width] != b[i:i + width]]


def changed_count(a, b, width, delta=PIXEL_DELTA, limit=None):
    """Pixels whose gray level differs by more than delta, counting stops
    once it passes limit."""
    changed = 0
    for i in changed_rows(a, b, width):
        changed += sum(1 for x, y in zip(a[i:i + width], b[i:i + width]) if abs(x - y) > delta)
        if limit is not None and changed > limit:
            break
    return changed


def changed_percent(a, b, delta=PIXEL_DELTA, width=DEDUP_SIZE[0]):
    """Percentage of pixels whose gray level differs by more than delta."""
    return 100.0 * changed_count(a, b, width, delta) / max(len(a), 1)


def find_duplicate(thumb, kept_thumbs, threshold_percent, width=DEDUP_SIZE[0]):
    """Index of the first kept thumbnail that thumb is a duplicate of, or None."""
    limit = threshold_percent / 100.0 * len(thumb)
    for i, other in enumerate(kept_thumbs):
        if changed_count(thumb, other, width, limit=limit) <= limit:
            return i
    return None


def change_box(prev, cur, full_w, full_h, size=CHANGE_SIZE):
    """Bounding box [x, y, w, h] (full-resolution pixels) around what changed
    between two thumbnails, or None when nothing meaningful changed or the
    whole screen changed. Small far-away changes (typically the mouse
    cursor) are ignored when a bigger change exists."""
    w, h = size
    cols, rows = (w + CELL - 1) // CELL, (h + CELL - 1) // CELL
    counts = [[0] * cols for _ in range(rows)]
    extents = {}   # cell -> [min x, min y, max x, max y] of its strongly changed pixels
    for start in changed_rows(prev, cur, w):
        for i in range(start, start + w):
            d = abs(prev[i] - cur[i])
            if d <= PIXEL_DELTA:
                continue
            y, x = divmod(i, w)
            cell = (y // CELL, x // CELL)
            counts[cell[0]][cell[1]] += 1
            if d <= EDGE_DELTA:
                continue
            e = extents.get(cell)
            if e is None:
                extents[cell] = [x, y, x, y]
            else:
                e[0], e[1] = min(e[0], x), min(e[1], y)
                e[2], e[3] = max(e[2], x), max(e[3], y)
    changed = {(r, c) for r in range(rows) for c in range(cols)
               if counts[r][c] >= CELL_MIN_PIXELS}
    if not changed:
        return None

    # Group neighboring changed cells into areas (8-connected)
    areas, seen = [], set()
    for start in changed:
        if start in seen:
            continue
        stack, cells, weight = [start], [], 0
        seen.add(start)
        while stack:
            r, c = stack.pop()
            cells.append((r, c))
            weight += counts[r][c]
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    n = (r + dr, c + dc)
                    if n in changed and n not in seen:
                        seen.add(n)
                        stack.append(n)
        areas.append((weight, cells))
    biggest = max(weight for weight, _ in areas)
    cells = [cell for weight, cs in areas if weight >= biggest * MINOR_RATIO for cell in cs]
    cells = [c for c in cells if c in extents]
    if not cells:
        return None

    # Tight box around the changed pixels themselves, not the grid cells
    px0 = min(extents[c][0] for c in cells)
    py0 = min(extents[c][1] for c in cells)
    px1 = max(extents[c][2] for c in cells) + 1
    py1 = max(extents[c][3] for c in cells) + 1
    sx, sy = full_w / w, full_h / h
    x, y = px0 * sx, py0 * sy
    bw, bh = (px1 - px0) * sx, (py1 - py0) * sy
    if bw * bh > MAX_BOX_AREA * full_w * full_h:
        return None
    pad = max(4, round(full_w / 200))
    x0, y0 = max(0, round(x - pad)), max(0, round(y - pad))
    x1, y1 = min(full_w, round(x + bw + pad)), min(full_h, round(y + bh + pad))
    return [x0, y0, x1 - x0, y1 - y0]


def image_size(ffmpeg, path):
    """(width, height) of an image, read from FFmpeg's stream information."""
    res = subprocess.run([ffmpeg, "-hide_banner", "-nostdin", "-i", str(path)],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                         errors="replace", stdin=subprocess.DEVNULL, creationflags=NO_WINDOW)
    m = re.search(r"Video:.*?(\d{2,5})x(\d{2,5})", res.stderr)
    if not m:
        raise RuntimeError(f"Could not read the size of {path}")
    return int(m.group(1)), int(m.group(2))
