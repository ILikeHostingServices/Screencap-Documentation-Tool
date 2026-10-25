#!/usr/bin/env python3
#
# calc_demo.py
# 2026-10-25
# Version: v1.0.0
#
# PURPOSE:
# One of the example tasks in the store screenshots: adding the new
# employee Gordon Freeman to a made-up staff directory spreadsheet in
# LibreOffice Calc, sorting it by last name, and saving it. Writes the
# spreadsheet (three made-up colleagues) into the demo home folder, opens
# it in Calc with a fresh profile (full screen on the 1600 x 972 virtual
# display), then clicks and types with real X input (xdotool), so the
# built-in recorder notes real clicks and keys. With --static it only
# opens the spreadsheet and stays open. Run by make_screenshots.sh and
# gui_shots.py.
#
# Needs: LibreOffice Calc (soffice), xdotool, and HOME set to the demo home
# folder.
#
# Usage: calc_demo.py [--static]

import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from demo_common import PERSON, click, clock, exit_on_terminate, key, type_text, wait_window, xdo

NAME = "Black Mesa staff directory"
SHEET = Path.home() / "Documents" / f"{NAME}.ods"
# Left behind if Calc is stopped; Calc would then ask about it
LOCK = SHEET.with_name(f".~lock.{SHEET.name}#")
ROWS = [
    ["Last name", "First name", "Department", "Employee ID", "Job title", "Clearance",
     "Workspace", "Email"],
    ["Kleiner", "Isaac", "Research Administration", "1002", "Senior Research Scientist",
     "Level 5", "Sector C, Administration", "Isaac.Kleiner@totallyblackmesa.tld"],
    ["Vance", "Eli", "Anomalous Materials", "1045", "Research Scientist", "Level 4",
     "Sector C, Test Lab C-33/a", "Eli.Vance@totallyblackmesa.tld"],
    ["Calhoun", "Barney", "Security", "3301", "Security Guard", "Level 2",
     "Sector C, Checkpoint", "Barney.Calhoun@totallyblackmesa.tld"],
]


def make_sheet(profile):
    """Write the staff directory as .ods (LibreOffice converts a CSV)."""
    work = Path(tempfile.mkdtemp(prefix="calc-demo-"))
    csv = work / f"{NAME}.csv"
    csv.write_text("\n".join(",".join(f'"{c}"' for c in row) for row in ROWS) + "\n",
                   encoding="utf-8")
    subprocess.run(["soffice", f"-env:UserInstallation={Path(profile).as_uri()}",
                    "--headless", "--infilter=CSV:44,34,76,1", "--convert-to", "ods",
                    "--outdir", str(work), str(csv)],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    SHEET.parent.mkdir(parents=True, exist_ok=True)
    LOCK.unlink(missing_ok=True)
    shutil.move(str(work / f"{NAME}.ods"), SHEET)
    shutil.rmtree(work, ignore_errors=True)


def open_calc():
    profile = tempfile.mkdtemp(prefix="calc-profile-")
    make_sheet(profile)
    proc = subprocess.Popen(["soffice", f"-env:UserInstallation={Path(profile).as_uri()}",
                             "--norestore", "--nologo", "--calc", str(SHEET)],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    win = wait_window(f"{NAME}.ods", timeout=60)
    if not win:
        proc.kill()
        sys.exit("LibreOffice Calc did not open the spreadsheet")
    xdo("windowmove", win, 0, 0)
    xdo("windowsize", win, 1600, 972)
    time.sleep(2.0)
    return proc, profile


def run_task(start):
    at = clock(start)
    p = PERSON
    # Row 5 is the first empty row; Tab moves to the next cell
    at(3.0); click(75, 220)
    fields = [p["last"], p["first"], p["department"], p["employee_id"], p["title"],
              p["clearance"], p["workspace"], p["email"]]
    t = 5.0
    for n, value in enumerate(fields):
        at(t)
        type_text(value)
        key("Return" if n == len(fields) - 1 else "Tab")
        t += 2.0 + 0.07 * len(value)
    # Sort the people by last name: Calc finds the table and its headings
    # from the cell picked
    at(t + 1.0); click(75, 152)                     # Last name heading
    at(t + 4.0); click(306, 29)                     # Data
    at(t + 6.0); click(365, 69)                     # Sort Ascending
    at(t + 9.0); key("ctrl+Home"); xdo("mousemove", 800, 600)
    at(t + 11.0); key("ctrl+s")                     # Save (.ods, no questions)


def main():
    exit_on_terminate()
    start = time.monotonic()
    proc, profile = open_calc()
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
        SHEET.unlink(missing_ok=True)
        LOCK.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
