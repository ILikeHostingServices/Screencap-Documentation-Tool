#!/usr/bin/env bash
#
# install.sh
# 2026-10-02
# Version: v1.3.0
#
# PURPOSE:
# One-step Linux and macOS installer for the Screencap Documentation Tool.
# Installs FFmpeg, Python 3, Tkinter, and (optional) Tesseract OCR and Pandoc
# if missing,
# downloads the latest
# version from GitHub, and adds screencap / screencap-gui launch commands.
# Safe to re-run to update; your source and output folders are kept.
#
# Linux (needs root, installs to /opt/Screencap-Documentation-Tool):
#   sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/ILikeHostingServices/Screencap-Documentation-Tool/HEAD/install.sh)"
#
# macOS (run as your normal user, installs to ~/Applications/Screencap-Documentation-Tool):
#   bash -c "$(curl -fsSL https://raw.githubusercontent.com/ILikeHostingServices/Screencap-Documentation-Tool/HEAD/install.sh)"
#
# Optional environment variables:
#   SCREENCAP_DIR  install folder (overrides the defaults above)
#   SCREENCAP_REF  branch, tag, or commit to install (default: HEAD = default branch)

set -euo pipefail

REPO="ILikeHostingServices/Screencap-Documentation-Tool"
REF="${SCREENCAP_REF:-HEAD}"
APP_NAME="Screencap Documentation Tool"

step() { printf '\033[36m==> %s\033[0m\n' "$*"; }
warn() { printf '\033[33mWARNING: %s\033[0m\n' "$*" >&2; }
die()  { printf '\033[31mERROR: %s\033[0m\n' "$*" >&2; exit 1; }
have() { command -v "$1" >/dev/null 2>&1; }

# ---------------------------------------------------------------------------
# Prerequisites
# ---------------------------------------------------------------------------

install_optional_linux() {
    # Pandoc makes Word exports. Optional: failures only warn.
    if ! have pandoc; then
        step "Installing Pandoc (optional, for Word export)"
        if have apt-get; then
            DEBIAN_FRONTEND=noninteractive apt-get install -y -qq pandoc || true
        elif have dnf; then
            dnf install -y -q pandoc || true
        elif have pacman; then
            pacman -S --needed --noconfirm pandoc-cli || true
        fi
        have pandoc || warn "Pandoc was not installed. Word export is unavailable; HTML export still works."
    fi
    # Tesseract OCR finds sensitive text to blur. Optional: failures only warn.
    have tesseract && return 0
    step "Installing Tesseract OCR (optional, for automatic blurring)"
    if have apt-get; then
        DEBIAN_FRONTEND=noninteractive apt-get install -y -qq tesseract-ocr || true
    elif have dnf; then
        dnf install -y -q tesseract tesseract-langpack-eng || dnf install -y -q tesseract || true
    elif have pacman; then
        pacman -S --needed --noconfirm tesseract tesseract-data-eng || true
    fi
    have tesseract || warn "Tesseract OCR was not installed. Sensitive text will not be found automatically; hand-drawn blur boxes still work."
}

linux_install_packages() {
    local need_ffmpeg=0 need_python=0
    have ffmpeg && have ffprobe || need_ffmpeg=1
    have python3 || need_python=1

    if have apt-get; then
        local pkgs=(python3-tk)
        [ "$need_ffmpeg" = 1 ] && pkgs+=(ffmpeg)
        [ "$need_python" = 1 ] && pkgs+=(python3)
        step "Installing packages with apt: ${pkgs[*]}"
        apt-get update -qq
        DEBIAN_FRONTEND=noninteractive apt-get install -y -qq "${pkgs[@]}"
    elif have dnf; then
        # Fedora ships FFmpeg as ffmpeg-free. Only install it when no FFmpeg is
        # present, so an existing RPM Fusion ffmpeg is not replaced.
        local pkgs=(python3-tkinter)
        [ "$need_ffmpeg" = 1 ] && pkgs+=(ffmpeg-free)
        [ "$need_python" = 1 ] && pkgs+=(python3)
        step "Installing packages with dnf: ${pkgs[*]}"
        dnf install -y -q "${pkgs[@]}" || die "dnf could not install ${pkgs[*]}. On RHEL/Rocky/Alma, enable EPEL and RPM Fusion first, then re-run."
    elif have pacman; then
        local pkgs=(tk)
        [ "$need_ffmpeg" = 1 ] && pkgs+=(ffmpeg)
        [ "$need_python" = 1 ] && pkgs+=(python)
        step "Installing packages with pacman: ${pkgs[*]}"
        pacman -S --needed --noconfirm "${pkgs[@]}"
    fi
    install_optional_linux
    if ! have apt-get && ! have dnf && ! have pacman; then
        if [ "$need_ffmpeg" = 1 ] || [ "$need_python" = 1 ]; then
            die "Unsupported package manager. Install ffmpeg, python3 (3.8+), and python3 Tkinter yourself, then re-run this installer."
        fi
        warn "Unknown package manager; using the existing ffmpeg and python3."
    fi
    # Pick a Python 3.8+ that has Tkinter (the distro one python3-tk targets),
    # falling back to the first Python 3.8+ found for command line use.
    PYTHON=""
    local candidate fallback=""
    for candidate in /usr/bin/python3 "$(command -v python3 || true)" /usr/bin/python3.[0-9]*; do
        case "$candidate" in *-config|"") continue ;; esac
        [ -x "$candidate" ] || continue
        "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' 2>/dev/null || continue
        [ -n "$fallback" ] || fallback="$candidate"
        if "$candidate" -c 'import tkinter' >/dev/null 2>&1; then
            PYTHON="$candidate"
            break
        fi
    done
    [ -n "$PYTHON" ] || PYTHON="$fallback"
}

macos_install_packages() {
    if ! have brew; then
        for b in /opt/homebrew/bin/brew /usr/local/bin/brew; do
            if [ -x "$b" ]; then eval "$("$b" shellenv)"; break; fi
        done
    fi
    if ! have brew; then
        step "Installing Homebrew (the standard macOS package manager). It will ask for your password."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        for b in /opt/homebrew/bin/brew /usr/local/bin/brew; do
            if [ -x "$b" ]; then eval "$("$b" shellenv)"; break; fi
        done
        have brew || die "Homebrew did not install correctly. See https://brew.sh and re-run this installer."
    fi

    step "Installing FFmpeg and Python with Homebrew"
    brew install ffmpeg python
    if ! have tesseract; then
        step "Installing Tesseract OCR (optional, for automatic blurring)"
        brew install tesseract || warn "Tesseract OCR was not installed. Sensitive text will not be found automatically; hand-drawn blur boxes still work."
    fi
    if ! have pandoc; then
        step "Installing Pandoc (optional, for Word export)"
        brew install pandoc || warn "Pandoc was not installed. Word export is unavailable; HTML and PDF export still work."
    fi
    PYTHON="$(brew --prefix)/bin/python3"
    [ -x "$PYTHON" ] || die "Homebrew Python not found at $PYTHON"

    # Homebrew packages Tkinter separately, matched to the Python version
    local pyver
    pyver="$("$PYTHON" -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
    if ! "$PYTHON" -c 'import tkinter' >/dev/null 2>&1; then
        step "Installing Tkinter for Python $pyver (needed for the GUI)"
        brew install "python-tk@$pyver" || warn "Could not install python-tk@$pyver; the GUI will not start, the command line still works."
    fi
}

verify_prerequisites() {
    have ffmpeg  || die "ffmpeg is still not on the PATH after installing."
    have ffprobe || die "ffprobe is still not on the PATH after installing."
    if [ -z "${PYTHON:-}" ] || [ ! -x "$PYTHON" ]; then die "python3 was not found after installing."; fi
    "$PYTHON" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' \
        || die "Python 3.8 or newer is required; found $("$PYTHON" --version 2>&1)."
    if "$PYTHON" -c 'import tkinter' >/dev/null 2>&1; then
        GUI_OK=1
    else
        GUI_OK=0
        warn "Tkinter is not available, so the GUI will not start. The command line version still works."
    fi
}

# ---------------------------------------------------------------------------
# Download and install
# ---------------------------------------------------------------------------

download_and_copy() {
    step "Downloading $APP_NAME ($REF) from GitHub"
    TMP_DIR="$(mktemp -d)"
    trap 'rm -rf "$TMP_DIR"' EXIT
    curl -fsSL "https://github.com/$REPO/archive/$REF.tar.gz" \
        | tar -xz --no-same-owner -C "$TMP_DIR" --strip-components=1
    [ -f "$TMP_DIR/screencap.py" ] || die "The downloaded archive does not contain screencap.py."

    step "Installing to $INSTALL_DIR"
    mkdir -p "$INSTALL_DIR"
    # Copy over the top: nothing is deleted, so recordings and screenshots
    # already in source/ and output/ survive an update.
    cp -R "$TMP_DIR/." "$INSTALL_DIR/"
    chmod -R u=rwX,go=rX "$INSTALL_DIR"
    chmod 755 "$INSTALL_DIR/screencap.py" "$INSTALL_DIR/screencap_gui.pyw" "$INSTALL_DIR/install.sh"
    mkdir -p "$INSTALL_DIR/source" "$INSTALL_DIR/output"
}

write_launcher() {
    # $1 = launcher path, $2 = script inside INSTALL_DIR
    cat > "$1" <<EOF
#!/bin/sh
# Launcher created by $APP_NAME install.sh
exec "$PYTHON" "$INSTALL_DIR/$2" "\$@"
EOF
    chmod 755 "$1"
}

install_linux() {
    [ "$(id -u)" -eq 0 ] || die "Run this installer with sudo on Linux (it installs packages and writes to /opt)."
    INSTALL_DIR="${SCREENCAP_DIR:-/opt/Screencap-Documentation-Tool}"
    local owner="${SUDO_USER:-root}"

    linux_install_packages
    verify_prerequisites
    download_and_copy

    # Program files stay root-owned; the default source/ and output/ folders
    # belong to the user who ran sudo so they can be written without root.
    chown -R root:root "$INSTALL_DIR"
    chown -R "$owner": "$INSTALL_DIR/source" "$INSTALL_DIR/output"

    step "Adding commands: screencap, screencap-gui"
    write_launcher /usr/local/bin/screencap screencap.py
    write_launcher /usr/local/bin/screencap-gui screencap_gui.pyw

    if [ -d /usr/share/applications ]; then
        cat > /usr/share/applications/screencap-documentation-tool.desktop <<EOF
[Desktop Entry]
Type=Application
Name=$APP_NAME
Comment=Capture a screenshot of every step in screen recordings
Exec=/usr/local/bin/screencap-gui
Icon=$INSTALL_DIR/assets/icon.png
Terminal=false
Categories=Utility;Graphics;
StartupWMClass=Screencapdoctool
EOF
        chmod 644 /usr/share/applications/screencap-documentation-tool.desktop
    fi
}

install_macos() {
    [ "$(id -u)" -ne 0 ] || die "Do not use sudo on macOS. Homebrew refuses to run as root; run the command as your normal user."
    INSTALL_DIR="${SCREENCAP_DIR:-$HOME/Applications/Screencap-Documentation-Tool}"

    macos_install_packages
    verify_prerequisites
    download_and_copy

    # Commands on the PATH (Homebrew's bin folder is already on it and user-writable)
    local bindir
    bindir="$(brew --prefix)/bin"
    step "Adding commands: screencap, screencap-gui"
    write_launcher "$bindir/screencap" screencap.py
    write_launcher "$bindir/screencap-gui" screencap_gui.pyw

    # Double-clickable launcher for Finder
    write_launcher "$INSTALL_DIR/Screencap GUI.command" screencap_gui.pyw
}

main() {
    case "$(uname -s)" in
        Linux)  install_linux ;;
        Darwin) install_macos ;;
        *)      die "Unsupported OS $(uname -s). On Windows use install.ps1." ;;
    esac

    echo
    printf '\033[32m%s is installed in %s\033[0m\n' "$APP_NAME" "$INSTALL_DIR"
    if [ "${GUI_OK:-0}" = 1 ]; then
        echo "Start the GUI with:          screencap-gui"
    fi
    echo "Or the command line with:    screencap --help"
    echo "Put recordings in:           $INSTALL_DIR/source (or choose any folder in the GUI)"
    if [ "$(uname -s)" = Darwin ]; then
        echo "In Finder, double-click:     $INSTALL_DIR/Screencap GUI.command"
    fi
}

# Everything runs from main(), so a partially downloaded script does nothing
main "$@"
