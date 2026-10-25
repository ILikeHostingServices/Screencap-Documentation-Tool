#!/usr/bin/env python3
#
# demo_common.py
# 2026-10-25
# Version: v1.0.0
#
# PURPOSE:
# What the screenshot demos (keepassxc_demo.py, calc_demo.py, web_demo.py)
# share: real mouse and keyboard input with xdotool, so the built-in
# recorder notes real clicks and keys; waiting for a window; and a clock
# that runs each demo's steps at fixed times after it starts (the
# recording starts in between, see make_screenshots.sh).
#
# The sample data is the made-up Black Mesa employee Gordon Freeman: every
# name, address, and number in it is fictional (555-01xx phone numbers and
# the .tld domain are reserved for examples).

import signal
import subprocess
import sys
import time

PERSON = {
    "first": "Gordon",
    "last": "Freeman",
    "company": "Black Mesa Research Facility",
    "department": "Anomalous Materials",
    "employee_id": "4176",
    "title": "Research Associate / Theoretical Physicist",
    "clearance": "Level 3",
    "workspace": "Sector C, Test Lab C-33/a",
    "email": "Gordon.Freeman@totallyblackmesa.tld",
    "office": "+1-555-019-1998",
    "mobile": "+1-555-010-1825",
}


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
