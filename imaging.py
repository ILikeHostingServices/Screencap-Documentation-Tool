#!/usr/bin/env python3
#
# imaging.py
# 2026-10-02
# Version: v1.0.0
#
# PURPOSE:
# Small image comparisons done with FFmpeg and the Python standard library
# (no Pillow or NumPy): grayscale thumbnails and how much of the picture
# differs between two screenshots. Used to spot duplicate screenshots.

import subprocess

from stepdoc import NO_WINDOW

DEDUP_SIZE = (160, 90)     # comparison size for duplicate detection
PIXEL_DELTA = 24           # 0-255 gray difference that counts as "changed"


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


def changed_percent(a, b, delta=PIXEL_DELTA):
    """Percentage of pixels whose gray level differs by more than delta."""
    changed = sum(1 for x, y in zip(a, b) if abs(x - y) > delta)
    return 100.0 * changed / max(len(a), 1)


def find_duplicate(thumb, kept_thumbs, threshold_percent):
    """Index of the first kept thumbnail that thumb is a duplicate of, or None."""
    for i, other in enumerate(kept_thumbs):
        if changed_percent(thumb, other) <= threshold_percent:
            return i
    return None
