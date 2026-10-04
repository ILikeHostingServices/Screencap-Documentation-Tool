#!/usr/bin/env python3
#
# apppaths.py
# 2026-10-04
# Version: v1.0.0
#
# PURPOSE:
# Where the tool's files live. The same code runs two ways:
#   - from the Python install (screencap.py and friends in one folder): the
#     program, its tools/ folder, and the default source/ and output/
#     folders are all in that folder, as they always have been;
#   - as the packaged Windows app (PyInstaller): the program files are in
#     the app's folder (often under Program Files, which normal users cannot
#     write to), so the default source/ and output/ folders go in the user's
#     Documents folder instead.

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
    return Path.home() / "Documents"


# Default home of the source/ and output/ folders
DATA_DIR = (documents_dir() / "Screencap Documentation Tool") if FROZEN else APP_DIR
