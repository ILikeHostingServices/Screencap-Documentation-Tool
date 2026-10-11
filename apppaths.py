#!/usr/bin/env python3
#
# apppaths.py
# 2026-10-10
# Version: v1.3.0
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
# The Windows installer (v1.24.0 and later) lets the user pick the source
# and output folders, or keep the defaults inside the install folder; it
# records the choice in the registry (see installer_folders below), and
# those folders then become the defaults.

import os
import sys
from collections import namedtuple
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

# The folders chosen in the Windows installer. `stamp` changes each time
# they are chosen, so the GUI applies a new choice once and otherwise keeps
# what the user picked in the app; an empty stamp means "do not override".
InstallerFolders = namedtuple("InstallerFolders", "source output stamp")
INSTALLER_KEY = r"Software\ILHS\Screencap Documentation Tool"


def installer_folders():
    """InstallerFolders from the registry for the packaged Windows app, or None."""
    if os.name != "nt" or not FROZEN:
        return None
    try:
        import winreg
    except ImportError:
        return None
    local = os.environ.get("LOCALAPPDATA", "")
    per_user = bool(local) and str(APP_DIR).lower().startswith(local.lower())
    roots = ((winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE) if per_user
             else (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER))
    for root in roots:
        try:
            with winreg.OpenKey(root, INSTALLER_KEY) as key:
                source = winreg.QueryValueEx(key, "SourceDir")[0]
                output = winreg.QueryValueEx(key, "OutputDir")[0]
                try:
                    stamp = winreg.QueryValueEx(key, "FoldersStamp")[0]
                except OSError:
                    stamp = ""
        except OSError:
            continue
        if source and output:
            return InstallerFolders(Path(source), Path(output), str(stamp))
    return None


INSTALLER_FOLDERS = installer_folders()
SOURCE_DIR = INSTALLER_FOLDERS.source if INSTALLER_FOLDERS else DATA_DIR / "source"
OUTPUT_DIR = INSTALLER_FOLDERS.output if INSTALLER_FOLDERS else DATA_DIR / "output"
