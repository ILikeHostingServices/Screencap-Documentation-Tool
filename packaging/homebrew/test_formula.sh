#!/usr/bin/env bash
#
# test_formula.sh
# 2026-10-10
# Version: v1.0.0
#
# PURPOSE:
# Installs a Homebrew formula file for the Screencap Documentation Tool in a
# throwaway local tap and tests it the way a user would use it: the formula's
# own test, the command line program on a recording, the default folders in
# ~/Documents, the app bundle, the GUI window, then uninstalling. Used by
# build-macos.yml here and by the tap's update workflow before it publishes.
#
# Usage (macOS with Homebrew):  test_formula.sh path/to/screencap-documentation-tool.rb VERSION

set -euo pipefail

FORMULA="${1:?usage: test_formula.sh FORMULA.rb VERSION}"
VERSION="${2:?usage: test_formula.sh FORMULA.rb VERSION}"
NAME=screencap-documentation-tool
export HOMEBREW_NO_AUTO_UPDATE=1 HOMEBREW_NO_INSTALL_CLEANUP=1 HOMEBREW_NO_ENV_HINTS=1

brew tap-new --no-git ilhs/ci >/dev/null 2>&1 || true
TAP="$(brew --repository)/Library/Taps/ilhs/homebrew-ci"
mkdir -p "$TAP/Formula"
cp "$FORMULA" "$TAP/Formula/$NAME.rb"

echo "== Install"
brew install --formula "ilhs/ci/$NAME"
echo "== Formula test"
brew test "ilhs/ci/$NAME"
echo "== Audit (informational)"
brew audit --strict --formula "ilhs/ci/$NAME" || echo "::warning::brew audit reported the issues above"

echo "== Command line"
out="$(screencap --version)"
echo "$out"
grep -q "v$VERSION" <<< "$out"
work="$(mktemp -d)"
mkdir -p "$work/src"
"$(brew --prefix ffmpeg)/bin/ffmpeg" -hide_banner -loglevel error -y -f lavfi -i color=white:s=640x360:r=10:d=8 \
    -vf "drawbox=x=150:y=100:w=300:h=150:color=gray:t=fill:enable='gte(t,3)'" \
    -c:v libx264 -pix_fmt yuv420p "$work/src/Demo.mp4"
screencap -s "$work/src" -o "$work/out"
test -f "$work/out/Demo/steps.md"
[ "$(find "$work/out/Demo" -maxdepth 1 -name "*.png" | wc -l)" -ge 2 ]
screencap
test -d "$HOME/Documents/Screencap Documentation Tool/source"

echo "== App bundle"
app="$(brew --prefix "ilhs/ci/$NAME")/Screencap Documentation Tool.app"
test -x "$app/Contents/MacOS/Screencap Documentation Tool"
test -f "$app/Contents/Resources/AppIcon.icns" || echo "::warning::The app has no icon"
plutil -lint "$app/Contents/Info.plist"

echo "== GUI"
# macOS has no timeout command; perl's alarm stops a hung window after 120 s
title="$(perl -e 'alarm shift; exec @ARGV' 120 screencap-gui --smoke-test)"
echo "Window title: $title"
[ "$title" = "Screencap Documentation Tool v$VERSION" ]

echo "== Uninstall"
brew uninstall --formula "ilhs/ci/$NAME"
if command -v screencap; then echo "screencap is still installed" >&2; exit 1; fi
brew untap ilhs/ci >/dev/null
echo "Homebrew formula v$VERSION works."
