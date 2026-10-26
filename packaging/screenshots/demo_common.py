#!/usr/bin/env python3
#
# demo_common.py
# 2026-10-26
# Version: v1.1.0
#
# PURPOSE:
# What the screenshot demos (keepassxc_demo.py, calc_demo.py, web_demo.py)
# share: real mouse and keyboard input with xdotool, so the built-in
# recorder notes real clicks and keys; waiting for a window; and a clock
# that runs each demo's steps at fixed times after its window opened (the
# recording is already running by then, see make_screenshots.sh).
#
# The sample data is in sample_data/: two made-up companies
# (companies.csv) and their staff (people.csv). Every name, address, and
# number in it is fictional (555-01xx phone numbers and the .tld and .corp
# endings are set aside for examples); the Black Mesa names belong to
# Valve Corporation (see CREDITS.md). Edit the CSV files (in a spreadsheet
# program, saved as CSV) to change what the demos type.

import csv
import signal
import subprocess
import sys
import time
from pathlib import Path

DATA = Path(__file__).resolve().parent / "sample_data"


def people(company=None):
    """The rows of people.csv (dicts keyed by its headings), in file order,
    only those of company when it is given."""
    with open(DATA / "people.csv", newline="", encoding="utf-8") as f:
        return [r for r in csv.DictReader(f) if company in (None, r["Company"])]


def person(first, last):
    return next(r for r in people() if (r["First Name"], r["Last Name"]) == (first, last))


# The new employee in the onboarding form and the staff directory, and the
# partner who saves a login in KeePassXC
PERSON = person("Gordon", "Freeman")
PARTNER = person("Jennifer", "Harris")


def exit_on_terminate():
    """Make terminate() (SIGTERM) end the demo through its finally: blocks,
    so the app it opened is closed too."""
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))


def xdo(*a):
    subprocess.run(["xdotool", *[str(v) for v in a]], check=False)


def click(x, y):
    # Show the pointer on the target first, as a person would move it there
    xdo("mousemove", x, y)
    time.sleep(0.45)
    xdo("click", "1")


def type_text(text):
    time.sleep(0.3)
    xdo("type", "--delay", "60", text)


def key(name):
    xdo("key", name)


def wait_window(name, timeout=30):
    """The id of the first visible window whose title contains name."""
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        out = subprocess.run(["xdotool", "search", "--onlyvisible", "--name", name],
                             capture_output=True, text=True).stdout.split()
        if out:
            return out[0]
        time.sleep(0.3)
    return ""


def clock(start):
    """at(t) waits until t seconds after start."""
    def at(t):
        time.sleep(max(0.0, start + t - time.monotonic()))
    return at
