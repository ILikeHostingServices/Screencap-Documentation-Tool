#!/usr/bin/env python3
#
# player.py
# 2026-10-02
# Version: v1.0.0
#
# PURPOSE:
# Opens the original screen recording in VLC media player at a given moment,
# so the action that led to a step (the click or keystroke) can be watched.

import os
import shutil
import subprocess
import sys
from pathlib import Path

LEAD_IN = 3.0   # seconds of video shown before the step's screen appeared

VLC_MISSING_HELP = (
    "VLC media player was not found. Install it from https://www.videolan.org/ "
    "(Windows: winget install --id VideoLAN.VLC -e).")


def find_vlc(explicit=None):
    if explicit:
        return explicit if Path(explicit).is_file() else None
    found = shutil.which("vlc")
    if found:
        return found
    candidates = []
    if os.name == "nt":
        for base in (os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)")):
            if base:
                candidates.append(Path(base) / "VideoLAN" / "VLC" / "vlc.exe")
    elif sys.platform == "darwin":
        candidates.append(Path("/Applications/VLC.app/Contents/MacOS/VLC"))
    for c in candidates:
        if c.is_file():
            return str(c)
    return None


def start_time(step, lead_in=LEAD_IN):
    """Where to start playback for a step: a little before its screen
    appeared, so the action that caused it is visible."""
    begin = step.get("still_from")
    if begin is None:
        begin = step.get("time", 0.0)
    return max(0.0, float(begin) - lead_in)


def vlc_command(vlc, video, seconds):
    # --no-one-instance: a VLC already open in single-instance mode would
    # otherwise queue the file and ignore the start time
    return [vlc, "--no-one-instance", f"--start-time={seconds:.2f}", str(video)]


def open_at(vlc, video, seconds):
    """Launch VLC without waiting for it, detached from this program."""
    kwargs = {"stdin": subprocess.DEVNULL, "stdout": subprocess.DEVNULL,
              "stderr": subprocess.DEVNULL, "close_fds": True}
    if os.name == "nt":
        kwargs["creationflags"] = (subprocess.DETACHED_PROCESS |
                                   subprocess.CREATE_NEW_PROCESS_GROUP)
    else:
        kwargs["start_new_session"] = True
    return subprocess.Popen(vlc_command(vlc, video, seconds), **kwargs)
