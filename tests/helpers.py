#!/usr/bin/env python3
#
# helpers.py
# 2026-10-02
# Version: v1.0.0
#
# PURPOSE:
# Shared test helpers: puts the repository on the import path, finds FFmpeg,
# and builds short synthetic screen recordings with FFmpeg so every test
# works on real files without shipping any videos.

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import screencap as sc  # noqa: E402

FFMPEG = sc.find_tool("ffmpeg")
FFPROBE = sc.find_tool("ffprobe")

# A white "desktop" where a dialog opens at 4 s, a title bar appears at 8 s,
# and a progress bar fills from 13 s.
DEMO_FILTER = ("drawbox=x=300:y=200:w=600:h=300:color=gray:t=fill:enable='gte(t,4)',"
               "drawbox=x=320:y=220:w=560:h=40:color=blue:t=fill:enable='between(t,8,12)',"
               "drawbox=x=320:y=300:w='min(560,(t-13)*400)':h=30:color=green:t=fill:"
               "enable='gte(t,13)'")


def make_video(path, vf=DEMO_FILTER, duration=18):
    res = sc.run([FFMPEG, "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi",
                  "-i", f"color=white:s=1280x720:r=30:d={duration}", "-vf", vf,
                  "-c:v", "libx264", "-pix_fmt", "yuv420p", str(path)])
    if res.returncode != 0:
        raise RuntimeError(res.stderr)
