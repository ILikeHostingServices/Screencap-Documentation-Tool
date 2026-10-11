#!/usr/bin/env bash
#
# test_package.sh
# 2026-10-11
# Version: v1.0.0
#
# PURPOSE:
# Installs one built Linux package in a clean system (a container), then
# tests it the way a user would: the command line program processes a
# synthetic recording, the default folders go in ~/Documents, the GUI window
# opens, and uninstalling leaves nothing behind. Used by
# .github/workflows/build-linux.yml for every distribution and CPU type
# (x86_64, arm64, and 32-bit ARM for Raspberry Pi OS). Runs as root.
#
# Usage: test_package.sh FAMILY VERSION [PACKAGE_DIR]
#   FAMILY: deb, fedora, rhel, suse, or arch
#   PACKAGE_DIR: folder holding the built package files (default: pkg)

set -euxo pipefail

family="$1"
V="$2"
pkg="${3:-pkg}"
echo "CPU: $(uname -m)"

# 1. Install the package; its dependencies come from the distribution
case "$family" in
  deb)
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -qq
    apt-get install -y -qq "./$pkg"/*.deb xvfb ;;
  fedora)
    dnf install -y "./$pkg"/*.rpm xorg-x11-server-Xvfb ;;
  rhel)
    # FFmpeg is not in RHEL; RPM Fusion has it (needs EPEL and CRB)
    dnf install -y epel-release dnf-plugins-core
    dnf config-manager --set-enabled crb
    dnf install -y "https://mirrors.rpmfusion.org/free/el/rpmfusion-free-release-9.noarch.rpm"
    dnf install -y "./$pkg"/*.rpm xorg-x11-server-Xvfb ;;
  suse)
    zypper --non-interactive install --allow-unsigned-rpm "./$pkg"/*.rpm xorg-x11-server-Xvfb dejavu-fonts ;;
  arch)
    pacman -Syu --noconfirm
    pacman -U --noconfirm "./$pkg"/*.pkg.tar.zst
    pacman -S --noconfirm --needed xorg-server-xvfb ;;
  *)
    echo "Unknown package family: $family" >&2
    exit 2 ;;
esac

# 2. The command line program
out="$(/usr/bin/screencap --version)"
echo "$out"
grep -q "v$V" <<< "$out"
test -f /usr/share/applications/io.github.ILikeHostingServices.ScreencapDocumentationTool.desktop
test -f /usr/share/icons/hicolor/256x256/apps/io.github.ILikeHostingServices.ScreencapDocumentationTool.png
export HOME=/tmp/home && mkdir -p "$HOME"
# A recording with two steps (FFV1 in Matroska: built into every
# distribution's FFmpeg, including Fedora's patent-free build)
mkdir -p /tmp/src
ffmpeg -hide_banner -loglevel error -y -f lavfi -i color=white:s=640x360:r=10:d=8 \
  -vf "drawbox=x=150:y=100:w=300:h=150:color=gray:t=fill:enable='gte(t,3)'" \
  -c:v ffv1 /tmp/src/Demo.mkv
/usr/bin/screencap -s /tmp/src -o /tmp/out
test -f /tmp/out/Demo/steps.md
ls /tmp/out/Demo
[ "$(ls /tmp/out/Demo/*.png | wc -l)" -ge 2 ]
# With no folders given, a package install uses ~/Documents
/usr/bin/screencap
test -d "$HOME/Documents/Screencap Documentation Tool/source"

# 3. The GUI window opens (generous time limit: 32-bit ARM runs emulated in CI)
Xvfb :99 -screen 0 1400x900x24 >/dev/null 2>&1 &
sleep 5
title="$(DISPLAY=:99 timeout 300 /usr/bin/screencap-gui --smoke-test)"
echo "Window title: $title"
[ "$title" = "Screencap Documentation Tool v$V" ]

# 4. Uninstalling leaves nothing behind
case "$family" in
  deb) apt-get remove -y screencap-documentation-tool ;;
  fedora|rhel) dnf remove -y screencap-documentation-tool ;;
  suse) zypper --non-interactive remove screencap-documentation-tool ;;
  arch) pacman -R --noconfirm screencap-documentation-tool ;;
esac
# (a bare "! test" would not stop the script under set -e)
for f in /usr/bin/screencap /usr/share/screencap-documentation-tool; do
  if [ -e "$f" ]; then echo "::error::$f is still there after uninstalling"; exit 1; fi
done
echo "All package tests passed on $(uname -m)"
