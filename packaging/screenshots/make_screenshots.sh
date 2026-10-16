#!/usr/bin/env bash
#
# make_screenshots.sh
# 2026-10-16
# Version: v1.1.1
#
# PURPOSE:
# Makes the screenshots used in the README, the Linux software center
# listing (metainfo), and the Snap Store listing, on a virtual X display:
#   1. records the made-up "Example App" setup wizard with the built-in
#      recorder (real clicks and keys, so the click rings and captions are
#      the tool's own),
#   2. processes it, cropped to the wizard window,
#   3. opens the GUI on it and takes the screenshots (gui_shots.py),
#   4. exports the steps as HTML and PowerPoint and takes pictures of them
#      (the slides are drawn by LibreOffice Impress).
# The screenshots go to docs/screenshots/.
#
# Needs (Linux): Xvfb (xvfb-run), openbox, xdotool, ImageMagick (import),
# Tesseract, FFmpeg, Python 3 with Tkinter, Chromium or Google Chrome
# (set CHROME to its path if it is not on the PATH), LibreOffice Impress,
# and pdftoppm (poppler-utils).
#
# Usage: packaging/screenshots/make_screenshots.sh

set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
OUT="$ROOT/docs/screenshots"
PY="${PYTHON:-python3}"
# Shown in the GUI's folder boxes, so it should look like a real profile
DEMO_HOME="${DEMO_HOME:-/home/alex}"
DOCS="$DEMO_HOME/Documents/ScreenCap Docs"
if ! mkdir -p "$DOCS" 2>/dev/null; then
    DOCS="$(mktemp -d)/Documents/ScreenCap Docs"
    mkdir -p "$DOCS"
fi
CHROME="${CHROME:-$(command -v chromium || command -v chromium-browser || command -v google-chrome || true)}"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

if [ -z "${SCREENSHOT_DISPLAY_READY:-}" ]; then
    export SCREENSHOT_DISPLAY_READY=1
    exec xvfb-run -a -s "-screen 0 1600x972x24" "$0" "$@"
fi
openbox >/dev/null 2>&1 &
sleep 1
xsetroot -solid "#2b5d7a"

echo "Recording the demo wizard..."
rm -rf "$DOCS/Recordings" "$DOCS/Output"
mkdir -p "$WORK/rec"
# The wizard opens first (at the place the crop below expects) and starts
# clicking itself 3 seconds later; the recording starts in between
"$PY" "$HERE/demo_wizard.py" &
WIZ=$!
sleep 1
"$PY" "$ROOT/screencap.py" --record --record-seconds 34 -s "$WORK/rec" -o "$WORK/out" \
    >"$WORK/record.log" 2>&1 || { cat "$WORK/record.log"; exit 1; }
wait "$WIZ" || true

echo "Processing it..."
mkdir -p "$DOCS/Recordings"
video="$(ls "$WORK"/rec/*.mkv)"
cp "$video" "$DOCS/Recordings/Install Example App.mkv"
cp "${video%.mkv}.events.json" "$DOCS/Recordings/Install Example App.events.json"
"$PY" "$ROOT/screencap.py" -s "$DOCS/Recordings" -o "$DOCS/Output" --crop 216:56:852:608

echo "Taking the GUI screenshots..."
"$PY" "$HERE/gui_shots.py" "$DOCS" "$OUT"

echo "Taking the document screenshot..."
html="$(cat "$OUT/export.path")"
rm -f "$OUT/export.path"
if [ -n "$CHROME" ]; then
    "$CHROME" --headless=new --no-sandbox --disable-gpu --hide-scrollbars \
        --window-size=1600,972 --screenshot="$OUT/06-export-html.png" "file://$html" >/dev/null 2>&1
else
    echo "Chromium was not found (set CHROME): skipped 06-export-html.png" >&2
fi
echo "Taking the PowerPoint screenshot..."
deck="$(cat "$OUT/pptx.path")"
rm -f "$OUT/pptx.path"
mkdir -p "$WORK/slides"
cp "$deck" "$WORK/slides/deck.pptx"
( cd "$WORK/slides" && soffice --headless --norestore --convert-to pdf deck.pptx >/dev/null 2>&1 )
pdftoppm -r 60 -png -f 1 -l 4 "$WORK/slides/deck.pdf" "$WORK/slides/s"
# The first four slides in a 2 x 2 grid, the size of the other screenshots
montage "$WORK"/slides/s-*.png -tile 2x2 -geometry 768x432+12+12 -background "#2b5d7a" \
    -bordercolor "#d0d7de" -border 1 "$WORK/slides/grid.png"
convert "$WORK/slides/grid.png" -gravity center -background "#2b5d7a" -extent 1600x972 \
    "$OUT/07-powerpoint.png"
ls -la "$OUT"
