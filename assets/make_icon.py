#!/usr/bin/env python3
#
# make_icon.py
# 2026-10-01
# Version: v1.0.0
#
# PURPOSE:
# Regenerates the application icon (icon.ico for Windows, icon.png for the
# GUI window, Linux menu entry, and macOS) from code, so the artwork can be
# tweaked and rebuilt without an image editor.
#
# Requires Pillow (developer machines only, not needed to run the tool):
#   py -3 -m pip install pillow
#   py -3 assets\make_icon.py

from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
S = 1024  # master canvas size; every size is downsampled from this

BG_TOP = (37, 99, 235)       # blue
BG_BOTTOM = (30, 58, 138)    # dark blue
BEZEL = (255, 255, 255)      # monitor frame and stand
SCREEN = (15, 30, 61)        # dark navy screen
ACCENT = (245, 158, 11)      # amber capture brackets and shutter dot


def px(fraction):
    return int(round(fraction * S))


def draw_master():
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))

    # Rounded-square background with a vertical gradient
    gradient = Image.new("RGBA", (S, S))
    gd = ImageDraw.Draw(gradient)
    for y in range(S):
        t = y / (S - 1)
        gd.line([(0, y), (S, y)], fill=tuple(
            int(BG_TOP[i] + (BG_BOTTOM[i] - BG_TOP[i]) * t) for i in range(3)) + (255,))
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, S - 1, S - 1], radius=px(0.22), fill=255)
    img.paste(gradient, (0, 0), mask)

    d = ImageDraw.Draw(img)

    # Monitor: white bezel, dark screen, neck, and base
    d.rounded_rectangle([px(0.14), px(0.18), px(0.86), px(0.70)], radius=px(0.06), fill=BEZEL)
    d.rounded_rectangle([px(0.19), px(0.23), px(0.81), px(0.65)], radius=px(0.03), fill=SCREEN)
    d.rectangle([px(0.44), px(0.70), px(0.56), px(0.78)], fill=BEZEL)
    d.rounded_rectangle([px(0.30), px(0.77), px(0.70), px(0.83)], radius=px(0.03), fill=BEZEL)

    # Capture brackets (viewfinder corners) on the screen
    left, top, right, bottom = px(0.27), px(0.29), px(0.73), px(0.59)
    arm, w = px(0.11), px(0.045)
    for x, y, dx, dy in ((left, top, 1, 1), (right, top, -1, 1),
                         (left, bottom, 1, -1), (right, bottom, -1, -1)):
        d.rectangle(sorted_box(x, y, x + dx * arm, y + dy * w), fill=ACCENT)
        d.rectangle(sorted_box(x, y, x + dx * w, y + dy * arm), fill=ACCENT)

    # Shutter dot in the middle
    cx, cy, r = px(0.50), px(0.44), px(0.07)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=ACCENT)
    return img


def sorted_box(x0, y0, x1, y1):
    return [min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)]


def main():
    master = draw_master()
    master.resize((256, 256), Image.LANCZOS).save(HERE / "icon.png", optimize=True)
    sizes = [16, 20, 24, 32, 40, 48, 64, 128, 256]
    master.save(HERE / "icon.ico", sizes=[(s, s) for s in sizes])
    print(f"Wrote {HERE / 'icon.png'} and {HERE / 'icon.ico'} ({', '.join(map(str, sizes))} px)")


if __name__ == "__main__":
    main()
