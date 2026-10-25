#!/usr/bin/env python3
#
# web_demo.py
# 2026-10-25
# Version: v1.0.0
#
# PURPOSE:
# One of the example tasks in the store screenshots: filling in a made-up
# internal web form (onboarding.html, "Black Mesa Research Facility: New
# Employee Onboarding") for the new employee Gordon Freeman in Chromium,
# then submitting it. Opens the page as a full-screen app window on the
# 1600 x 972 virtual display, then clicks and types with real X input
# (xdotool), so the built-in recorder notes real clicks and keys. With
# --static it only opens the empty form and stays open. Run by
# make_screenshots.sh and gui_shots.py.
#
# Needs: Chromium or Google Chrome (CHROME, or on the PATH) and xdotool.
#
# Usage: web_demo.py [--static]

import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from demo_common import PERSON, click, clock, exit_on_terminate, type_text, wait_window

PAGE = Path(__file__).resolve().parent / "onboarding.html"
TITLE = "New Employee Onboarding"


def browser():
    found = os.environ.get("CHROME") or next(
        (shutil.which(n) for n in ("chromium", "chromium-browser", "google-chrome")
         if shutil.which(n)), None)
    if not found:
        sys.exit("Chromium was not found (set CHROME)")
    return found


def open_form():
    profile = tempfile.mkdtemp(prefix="chrome-demo-")
    # --test-type hides the "unsupported command-line flag" bar that
    # --no-sandbox (needed as root in a container) would show
    proc = subprocess.Popen(
        [browser(), "--no-sandbox", "--test-type", f"--user-data-dir={profile}",
         "--no-first-run", "--no-default-browser-check", "--disable-features=Translate",
         "--password-store=basic", "--window-position=0,0", "--window-size=1600,972",
         f"--app={PAGE.as_uri()}"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if not wait_window(TITLE):
        proc.kill()
        sys.exit("Chromium did not open the form")
    time.sleep(1.0)
    return proc, profile


def run_task(start):
    at = clock(start)
    p = PERSON
    # Each field is a step of its own: a click next to its label, then typing
    at(3.0); click(528, 242); type_text(p["first"])
    at(6.5); click(1071, 242); type_text(p["last"])
    at(10.0); click(528, 317)                               # Department
    at(12.0); click(370, 374)                               # Anomalous Materials
    at(15.0); click(1071, 318); type_text(p["employee_id"])
    at(18.5); click(528, 394); type_text(p["title"])
    at(24.0); click(1071, 393)                              # Security clearance
    at(26.0); click(860, 503)                               # Level 3
    at(29.0); click(528, 470); type_text(p["workspace"])
    at(33.5); click(1071, 470); type_text(p["email"])
    at(38.5); click(528, 546); type_text(p["office"])
    at(42.5); click(1071, 546); type_text(p["mobile"])
    # AD groups: clicking the name ticks its box
    at(46.5); click(373, 618)
    at(48.5); click(559, 618)
    at(50.5); click(800, 618)
    at(53.5); click(326, 681)                               # Submit


def main():
    exit_on_terminate()
    start = time.monotonic()
    proc, profile = open_form()
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
        shutil.rmtree(profile, ignore_errors=True)


if __name__ == "__main__":
    main()
