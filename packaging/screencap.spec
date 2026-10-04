# -*- mode: python ; coding: utf-8 -*-
#
# screencap.spec
# 2026-10-04
# Version: v1.0.0
#
# PURPOSE:
# PyInstaller recipe for the packaged app: one folder holding a GUI program
# ("Screencap Documentation Tool.exe", no console window) and a command line
# program (screencap.exe) that share one bundled Python and Tkinter. FFmpeg,
# Tesseract, Pandoc, and VLC are not bundled (their licenses); the app finds
# them where they are installed, or in a tools\ folder next to the .exe.
#
# Build from the repository root:
#   python packaging/make_version_info.py build/version_info.txt
#   python -m PyInstaller packaging/screencap.spec --noconfirm --clean
# Output: dist/Screencap-Documentation-Tool/

import os
from pathlib import Path

ROOT = Path(SPECPATH).parent                     # noqa: F821 (set by PyInstaller)
ICON = str(ROOT / "assets" / "icon.ico")
VERSION_FILE = ROOT / "build" / "version_info.txt"
version_arg = {"version": str(VERSION_FILE)} if (os.name == "nt" and VERSION_FILE.is_file()) else {}

datas = [
    (str(ROOT / "assets" / "icon.ico"), "assets"),
    (str(ROOT / "assets" / "icon.png"), "assets"),
    (str(ROOT / "whisper_worker.py"), "."),      # run by an external Python for captions
    (str(ROOT / "LICENSE"), "."),
]
# Not needed at run time; keeps the folder smaller
excludes = ["unittest", "pydoc_data", "test", "lib2to3", "distutils", "setuptools", "pip"]

gui = Analysis([str(ROOT / "screencap_gui.pyw")], pathex=[str(ROOT)], datas=datas,
               excludes=excludes)
cli = Analysis([str(ROOT / "screencap.py")], pathex=[str(ROOT)], excludes=excludes)

gui_exe = EXE(PYZ(gui.pure), gui.scripts, [], exclude_binaries=True,
              name="Screencap Documentation Tool", console=False, icon=ICON,
              upx=False, **version_arg)
cli_exe = EXE(PYZ(cli.pure), cli.scripts, [], exclude_binaries=True,
              name="screencap", console=True, icon=ICON, upx=False, **version_arg)

COLLECT(gui_exe, gui.binaries, gui.datas, cli_exe, cli.binaries, cli.datas,
        name="Screencap-Documentation-Tool", upx=False)
