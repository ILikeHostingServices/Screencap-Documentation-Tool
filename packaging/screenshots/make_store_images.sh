#!/usr/bin/env bash
#
# make_store_images.sh
# 2026-10-30
# Version: v1.0.0
#
# PURPOSE:
# Makes the images for the Snap Store listing in docs/store/: exactly five
# screenshots (the store takes no more than five) and the featured banner
# (1920 x 640, 3:1), from the screenshots in docs/screenshots/. Upload them
# in the snapcraft.io dashboard under Listing: the five in order as Images,
# banner.png as Featured banner. Run by make_screenshots.sh; can also be run
# on its own after it.
#
# Needs: Chromium or Google Chrome (CHROME, or on the PATH), ImageMagick,
# curl, and internet access for the brand fonts (Google Fonts).
#
# Usage: packaging/screenshots/make_store_images.sh

set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
SHOTS="$ROOT/docs/screenshots"
OUT="$ROOT/docs/store"
CHROME="${CHROME:-$(command -v chromium || command -v chromium-browser || command -v google-chrome || true)}"
[ -n "$CHROME" ] || { echo "Chromium was not found (set CHROME)" >&2; exit 1; }
FONTS="https://fonts.googleapis.com/css2?family=Familjen+Grotesk:wght@700&family=Source+Sans+3:wght@400;600&display=swap"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

rm -rf "$OUT"
mkdir -p "$OUT"
# The five, in listing order: the Steps tab, recording, annotations, and the
# two kinds of finished document
n=1
for name in 01-steps-editor 05-recording 02-annotate-menu 06-export-html 07-powerpoint; do
    cp "$SHOTS/$name.png" "$OUT/screenshot-$n.png"
    n=$((n + 1))
done

# The brand fonts, downloaded first so the banner never falls back to a
# system font when Chromium cannot reach Google Fonts itself
curl -fsS -A "Mozilla/5.0 Chrome/120" -o "$WORK/fonts.css" "$FONTS"
grep -o 'https://[^)]*' "$WORK/fonts.css" | while read -r url; do
    file="$WORK/$(basename "$url")"
    curl -fsS -o "$file" "$url"
    sed -i "s|$url|file://$file|" "$WORK/fonts.css"
done
sed -e "s|FONTS|file://$WORK/fonts.css|" -e "s|ICON|file://$ROOT/assets/icon.png|" \
    -e "s|SHOT|file://$SHOTS/01-steps-editor.png|" "$HERE/banner.html" > "$WORK/banner.html"
# Headless Chromium's page is shorter than its window, so draw a taller
# window and keep the top 1920 x 640
"$CHROME" --headless=new --no-sandbox --disable-gpu --hide-scrollbars --allow-file-access-from-files \
    --window-size=1920,900 --virtual-time-budget=5000 --screenshot="$WORK/banner.png" \
    "file://$WORK/banner.html" >/dev/null 2>&1
convert "$WORK/banner.png" -crop 1920x640+0+0 +repage -strip "$OUT/banner.png"

# Every file must be under the store's 2 MB limit
for f in "$OUT"/*.png; do
    size=$(stat -c %s "$f")
    [ "$size" -lt 2000000 ] || { echo "$f is over 2 MB" >&2; exit 1; }
    echo "$(identify -format '%wx%h' "$f")  $((size / 1024)) KB  $f"
done
