#!/usr/bin/env python3
#
# keepassxc_demo.py
# 2026-10-20
# Version: v1.0.0
#
# PURPOSE:
# The example task in the store screenshots: creating a KeePassXC password
# database for "Northwind Traders" and adding one login to it. Opens
# KeePassXC with a fresh profile (classic theme) in a fixed place on the
# screen (the crop
# in make_screenshots.sh expects it there), then clicks and types with real
# X input (xdotool), so the built-in recorder notes real clicks and keys.
# With --static it only opens the welcome screen and stays open (for the
# "recording in progress" screenshot). Run by make_screenshots.sh and
# gui_shots.py on a 1600 x 972 virtual display.
#
# Needs: KeePassXC 2.7, xdotool, and HOME set to the demo home folder.
#
# Usage: keepassxc_demo.py [--static]

import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# Where the main window goes; every click below is relative to the screen
X, Y, W, H = 300, 140, 1000, 680
DB_NAME = "Northwind Traders"
DB_FILE = Path.home() / f"{DB_NAME}.kdbx"


def xdo(*a):
    subprocess.run(["xdotool", *[str(v) for v in a]], check=False)


def click(x, y):
    # Show the pointer on the target first, as a person would move it there
    xdo("mousemove", x, y); time.sleep(0.45); xdo("click", "1")


def type_text(text):
    time.sleep(0.3); xdo("type", "--delay", "60", text)


def replace_text(x, y, text):
    click(x, y); time.sleep(0.2); xdo("key", "ctrl+a"); type_text(text)


def open_keepassxc():
    DB_FILE.unlink(missing_ok=True)
    conf = tempfile.mkdtemp(prefix="kpxc-")
    # The classic theme draws plain gray buttons, as most desktop apps do;
    # the default theme's white-on-green buttons are hard to read for OCR
    (Path(conf) / "keepassxc").mkdir()
    (Path(conf) / "keepassxc" / "keepassxc.ini").write_text("[GUI]\nApplicationTheme=classic\n")
    env = dict(os.environ, XDG_CONFIG_HOME=conf, XDG_CACHE_HOME=conf, QT_QPA_PLATFORM="xcb")
    proc = subprocess.Popen(["keepassxc"], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    win = ""
    end = time.monotonic() + 20
    while not win and time.monotonic() < end:
        time.sleep(0.3)
        out = subprocess.run(["xdotool", "search", "--onlyvisible", "--name", "KeePassXC"],
                             capture_output=True, text=True).stdout.split()
        win = out[0] if out else ""
    if not win:
        proc.kill(); sys.exit("KeePassXC did not open a window")
    xdo("windowsize", win, W, H); xdo("windowmove", win, X, Y); time.sleep(0.5)
    return proc, conf


def run_task(start):
    def at(t):
        time.sleep(max(0.0, start + t - time.monotonic()))
    at(3.0); click(800, 536)                          # Create new database
    at(7.0); replace_text(936, 321, DB_NAME)          # Database Name
    at(11.0); click(1044, 670)                        # Continue
    at(15.0); click(1044, 681)                        # Continue (encryption settings)
    at(19.0); click(915, 353); type_text("Demo-Vault-2026")    # Enter password
    at(23.0); click(942, 384); type_text("Demo-Vault-2026")    # Confirm password
    at(27.0); click(1044, 681)                        # Done
    at(31.0); replace_text(800, 612, f"{DB_NAME}.kdbx")        # File name
    at(35.0); xdo("key", "Return")                    # Save
    at(39.0); click(445, 182)                         # Add a new entry
    # Fields are clicked near their labels, as people do
    at(43.0); click(600, 253); type_text("Northwind Traders mail")
    at(47.0); click(600, 284); type_text("alex.morgan@example.com")
    at(51.0); click(600, 316); type_text("Tr4ders-Mail-2026")
    at(55.0); xdo("key", "Return")                    # OK


def main():
    if not shutil.which("keepassxc"):
        sys.exit("KeePassXC is not installed")
    start = time.monotonic()
    proc, conf = open_keepassxc()
    try:
        if "--static" in sys.argv:
            proc.wait()
            return
        run_task(start)
        time.sleep(3)
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(5)
            except subprocess.TimeoutExpired:
                proc.kill()
        shutil.rmtree(conf, ignore_errors=True)
        DB_FILE.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
