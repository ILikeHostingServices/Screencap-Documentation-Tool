#!/usr/bin/env bash
#
# make_screenshots.sh
# 2026-10-25
# Version: v1.3.0
#
# PURPOSE:
# Makes the screenshots used in the README, the Linux software center
# listing (metainfo), the Snap Store listing, and the website, on a
# virtual X display:
#   1. records three real tasks for the made-up new Black Mesa employee
#      Gordon Freeman with the built-in recorder (real clicks and keys, so
#      the click rings and captions are the tool's own):
#        - filling in an onboarding web form in Chromium (web_demo.py),
#        - adding him to a staff directory in LibreOffice Calc (calc_demo.py),
#        - saving his login in a new KeePassXC database (keepassxc_demo.py),
#   2. processes them, each cropped to the part of the screen it uses,
#   3. opens the GUI on them and takes the screenshots (gui_shots.py),
#   4. exports the steps as HTML and PowerPoint and takes pictures of them
#      (the slides are drawn by LibreOffice Impress).
# The screenshots go to docs/screenshots/.
#
# Needs (Linux): Xvfb (xvfb-run), openbox, xdotool, KeePassXC 2.7, ImageMagick (import),
# Tesseract, FFmpeg, Python 3 with Tkinter, Chromium or Google Chrome
# (set CHROME to its path if it is not on the PATH), LibreOffice Calc and
# Impress, and pdftoppm (poppler-utils).
#
# Usage: packaging/screenshots/make_screenshots.sh

set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
OUT="$ROOT/docs/screenshots"
PY="${PYTHON:-python3}"
# Shown in the GUI's folder boxes, so it should look like a real profile
DEMO_HOME="${DEMO_HOME:-/home/demo}"
DOCS="$DEMO_HOME/Documents/ScreenCap Docs"
if ! mkdir -p "$DOCS" 2>/dev/null; then
    DOCS="$(mktemp -d)/Documents/ScreenCap Docs"
    mkdir -p "$DOCS"
fi
CHROME="${CHROME:-$(command -v chromium || command -v chromium-browser || command -v google-chrome || true)}"
export CHROME
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

if [ -z "${SCREENSHOT_DISPLAY_READY:-}" ]; then
    export SCREENSHOT_DISPLAY_READY=1
    exec xvfb-run -a -s "-screen 0 1600x972x24" "$0" "$@"
fi
openbox >/dev/null 2>&1 &
sleep 1
xsetroot -solid "#2b5d7a"

rm -rf "$DOCS/Recordings" "$DOCS/Output"
mkdir -p "$DOCS/Recordings"

# record DEMO SECONDS NAME [PROCESSING OPTIONS...]
# The demo opens its app first and starts clicking 3 seconds after it
# starts; the recording starts in between. Recordings already processed are
# skipped, so each run below processes only the one just added.
record() {
    local demo="$1" seconds="$2" name="$3"
    shift 3
    echo "Recording: $name..."
    rm -rf "$WORK/rec"
    mkdir -p "$WORK/rec"
    HOME="$DEMO_HOME" "$PY" "$HERE/$demo" &
    local pid=$!
    sleep 1
    "$PY" "$ROOT/screencap.py" --record --record-seconds "$seconds" -s "$WORK/rec" -o "$WORK/out" \
        >"$WORK/record.log" 2>&1 || { cat "$WORK/record.log"; exit 1; }
    wait "$pid" || true
    local video
    video="$(ls "$WORK"/rec/*.mkv)"
    cp "$video" "$DOCS/Recordings/$name.mkv"
    cp "${video%.mkv}.events.json" "$DOCS/Recordings/$name.events.json"
    echo "Processing it..."
    "$PY" "$ROOT/screencap.py" -s "$DOCS/Recordings" -o "$DOCS/Output" "$@"
}
# A finer sensitivity than the default, so filling in each field of a form
# is a step of its own; each cropped to the part of the screen used
record web_demo.py 62 "Fill in the onboarding form" --crop 220:84:1160:720 -t 0.002
record calc_demo.py 50 "Add an employee to the staff directory" --crop 0:0:1160:400 -t 0.002
record keepassxc_demo.py 62 "Save a login in KeePassXC" --crop 300:120:1000:704 -t 0.002

echo "Taking the GUI screenshots..."
HOME="$DEMO_HOME" "$PY" "$HERE/gui_shots.py" "$DOCS" "$OUT"

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
