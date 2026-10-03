#!/usr/bin/env python3
#
# helpers.py
# 2026-10-03
# Version: v1.1.0
#
# PURPOSE:
# Shared test helpers: puts the repository on the import path, finds FFmpeg,
# builds short synthetic screen recordings with FFmpeg so every test works
# on real files without shipping any videos, and provides a stand-in for
# faster-whisper so the narration features can be tested without a model.

import contextlib
import json
import os
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


def make_video(path, vf=DEMO_FILTER, duration=18, audio=None, audio_delay=0.0):
    """audio: None (silent, no audio track), "tone" (a beep, no speech), or
    the path of a sound file to play starting audio_delay seconds in."""
    cmd = [FFMPEG, "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi",
           "-i", f"color=white:s=1280x720:r=30:d={duration}"]
    if audio == "tone":
        cmd += ["-f", "lavfi", "-i", f"sine=frequency=440:duration={duration}"]
    elif audio is not None:
        cmd += ["-i", str(audio)]
    cmd += ["-vf", vf, "-c:v", "libx264", "-pix_fmt", "yuv420p"]
    if audio is not None:
        ms = int(audio_delay * 1000)
        cmd += ["-af", f"adelay={ms}:all=1,apad", "-c:a", "aac", "-t", str(duration)]
    res = sc.run(cmd + [str(path)])
    if res.returncode != 0:
        raise RuntimeError(res.stderr)


FAKE_WHISPER = """
import json, os
from types import SimpleNamespace

if os.environ.get("SCREENCAP_FAKE_NOT_INSTALLED"):
    raise ImportError("simulated: not installed")


class WhisperModel:
    def __init__(self, model, device="cpu", compute_type="int8"):
        self.model = model

    def transcribe(self, audio, language=None, vad_filter=True):
        segs = json.loads(os.environ["SCREENCAP_FAKE_SEGMENTS"])
        return (iter([SimpleNamespace(**s) for s in segs]),
                SimpleNamespace(language="en", duration=18.0))
"""


@contextlib.contextmanager
def fake_whisper(folder, segments, installed=True):
    """Make transcribe.py use a stand-in faster-whisper that returns the
    given segments, through the real worker process."""
    pkg = Path(folder) / "fake_whisper" / "faster_whisper"
    pkg.mkdir(parents=True, exist_ok=True)
    (pkg / "__init__.py").write_text(FAKE_WHISPER, encoding="utf-8")
    values = {"SCREENCAP_WHISPER_PYTHON": sys.executable,
              "PYTHONPATH": str(pkg.parent),
              "SCREENCAP_FAKE_SEGMENTS": json.dumps(segments),
              "SCREENCAP_FAKE_NOT_INSTALLED": "" if installed else "1"}
    saved = {k: os.environ.get(k) for k in values}
    os.environ.update(values)
    try:
        yield
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
