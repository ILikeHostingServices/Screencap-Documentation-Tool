#!/usr/bin/env python3
#
# apppaths.py
# 2026-10-10
# Version: v1.2.0
#
# PURPOSE:
# Where the tool's files live. The same code runs two ways:
#   - from the Python install (screencap.py and friends in one folder): the
#     program, its tools/ folder, and the default source/ and output/
#     folders are all in that folder, as they always have been;
#   - as the packaged Windows app (PyInstaller), from a Linux package
#     (.deb, .rpm, Arch, snap), or from Homebrew on macOS: the program files are in a folder normal
#     users cannot write to (Program Files, /usr/share), so the default
#     source/ and output/ folders go in the user's Documents folder instead.
#     Linux packages and the Homebrew formula mark themselves with a
#     package-kind file next to the program (see packaging/linux/stage.sh
#     and packaging/homebrew/).

import os
import sys
from pathlib import Path

FROZEN = bool(getattr(sys, "frozen", False))

# Folder of the program itself: the .exe folder for the packaged app, the
# script folder otherwise. tools/ffmpeg, tools/tesseract, and whisper-env
# are looked for here.
APP_DIR = (Path(sys.executable).resolve().parent if FROZEN
           else Path(__file__).resolve().parent)

# Read-only files that ship with the program (icons, the speech recognition
# worker). PyInstaller unpacks them into its own folder (sys._MEIPASS).
BUNDLE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))


def documents_dir():
    """The user's real Documents folder, including when Windows has moved it
    (for example into OneDrive)."""
    if os.name == "nt":
        try:
            import ctypes
            from ctypes import wintypes
            buf = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
            # CSIDL_PERSONAL (5) is Documents; 0 = current path, not default
            if ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, buf) == 0 and buf.value:
                return Path(buf.value)
        except (AttributeError, OSError):
            pass
    if os.environ.get("SNAP_REAL_HOME"):          # inside a snap, HOME is the snap's own
        home = Path(os.environ["SNAP_REAL_HOME"])
    else:
        home = Path.home()
    if sys.platform.startswith("linux"):
        # The desktop's own Documents folder (it can have a translated name)
        try:
            import subprocess
            out = subprocess.run(["xdg-user-dir", "DOCUMENTS"], capture_output=True,
                                 text=True, timeout=3).stdout.strip()
            if out and Path(out) != home and Path(out).is_absolute():
                if not os.environ.get("SNAP_REAL_HOME"):
                    return Path(out)
        except (OSError, ValueError, subprocess.SubprocessError):
            pass
    return home / "Documents"


def package_kind():
    """'deb', 'rpm', 'arch', 'snap' (Linux packages), or 'brew' (Homebrew),
    else None."""
    try:
        kind = (APP_DIR / "package-kind").read_text(encoding="ascii").strip()
    except OSError:
        return None
    return kind if kind in ("deb", "rpm", "arch", "snap", "brew") else None


PACKAGE_KIND = package_kind()

# Default home of the source/ and output/ folders
DATA_DIR = ((documents_dir() / "Screencap Documentation Tool") if FROZEN or PACKAGE_KIND
            else APP_DIR)
