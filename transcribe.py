#!/usr/bin/env python3
#
# transcribe.py
# 2026-10-03
# Version: v1.0.0
#
# PURPOSE:
# Turns spoken narration in a recording into first-draft captions. FFmpeg
# pulls the audio out, whisper_worker.py transcribes it offline with
# faster-whisper (in the optional whisper-env Python environment), and each
# spoken sentence is attached to the step that was on screen while it was
# said. Only empty captions are filled, so nothing typed by hand is ever
# replaced. The full transcript is saved as transcript.txt.

import importlib.util
import json
import os
import queue
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

import stepdoc

SCRIPT_DIR = Path(__file__).resolve().parent
WORKER = SCRIPT_DIR / "whisper_worker.py"
ENV_DIR = SCRIPT_DIR / "whisper-env"
TRANSCRIPT_NAME = "transcript.txt"
DEFAULT_MODEL = "base"
# Offered in the GUI. Bigger is more accurate but slower; ".en" models are
# English only and a little more accurate for English.
MODELS = ("tiny", "base", "small", "medium", "tiny.en", "base.en", "small.en", "medium.en")
EXIT_NOT_INSTALLED = 3

WHISPER_MISSING_HELP = (
    "Speech recognition (faster-whisper) is not installed, so narration cannot be "
    "turned into captions. It is an optional download of about 450 MB. To add it, "
    "paste the Quick Start command again with -WithWhisper on Windows, or with "
    "SCREENCAP_WITH_WHISPER=1 on Linux and macOS (see \"Captions From Narration\" "
    "in README.md).")


class TranscribeError(Exception):
    """A problem worth showing to the user as-is."""


def find_python(explicit=None):
    """The Python that has faster-whisper: an explicit path, the
    SCREENCAP_WHISPER_PYTHON variable, the whisper-env folder made by the
    installer, or (for developers) the Python running this tool."""
    for candidate in (explicit, os.environ.get("SCREENCAP_WHISPER_PYTHON")):
        if candidate:
            return str(candidate) if Path(candidate).is_file() else None
    for exe in (ENV_DIR / "Scripts" / "python.exe", ENV_DIR / "bin" / "python"):
        if exe.is_file():
            return str(exe)
    if importlib.util.find_spec("faster_whisper") is not None:
        return sys.executable
    return None


def extract_audio(ffmpeg, video, wav):
    """Write the first audio track as 16 kHz mono WAV, the format Whisper
    uses. Returns False when the recording has no audio."""
    res = stepdoc.run_quiet([ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
                             "-i", str(video), "-map", "0:a:0?", "-vn",
                             "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(wav)])
    wav = Path(wav)
    if res.returncode == 0 and wav.is_file() and wav.stat().st_size > 1000:
        return True
    if "does not contain any stream" in res.stderr or res.returncode == 0:
        return False
    raise TranscribeError(f"Could not read the audio: {res.stderr.strip()[-300:]}")


def run_worker(python, wav, model, out_json, language=None, progress=None, cancel=None):
    """Run whisper_worker.py and return its parsed JSON."""
    cmd = [python, str(WORKER), str(wav), "--model", model, "--out", str(out_json)]
    if language:
        cmd += ["--language", language]
    env = dict(os.environ, PYTHONIOENCODING="utf-8", HF_HUB_DISABLE_SYMLINKS_WARNING="1",
               HF_HUB_DISABLE_PROGRESS_BARS="1")
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            stdin=subprocess.DEVNULL, creationflags=stepdoc.NO_WINDOW,
                            text=True, encoding="utf-8", errors="replace", env=env)
    # Read output on a thread so Cancel works even while the model loads or
    # downloads and the worker prints nothing for a while
    lines = queue.Queue()
    reader = threading.Thread(target=lambda: [lines.put(l) for l in proc.stdout], daemon=True)
    reader.start()
    messages = []
    try:
        while True:
            if cancel is not None and cancel.is_set():
                proc.terminate()
                proc.wait()
                raise stepdoc.Cancelled()
            try:
                line = lines.get(timeout=0.2).strip()
            except queue.Empty:
                if proc.poll() is not None and not reader.is_alive() and lines.empty():
                    break
                continue
            if line.startswith("PROGRESS "):
                if progress:
                    try:
                        progress(float(line.split()[1]))
                    except ValueError:
                        pass
            elif line:
                messages.append(line)
        code = proc.wait()
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
        reader.join(timeout=2)
        proc.stdout.close()
    if code == EXIT_NOT_INSTALLED:
        raise TranscribeError(WHISPER_MISSING_HELP)
    if code != 0:
        detail = "\n".join(messages[-5:]) or f"exit code {code}"
        raise TranscribeError(f"Speech recognition failed: {detail}")
    try:
        return json.loads(Path(out_json).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise TranscribeError(f"Speech recognition gave no usable result: {exc}")


def step_windows(steps):
    """For each step, the stretch of the recording during which its screen
    was showing: from when it appeared until the next step's screen
    appeared. Narration spoken in that stretch describes that screen."""
    def appeared(step):
        start = step.get("still_from")
        return step["time"] if start is None else start

    ordered = sorted(steps, key=lambda s: s["time"])
    windows = []
    for i, step in enumerate(ordered):
        start = float("-inf") if i == 0 else appeared(step)
        end = appeared(ordered[i + 1]) if i + 1 < len(ordered) else float("inf")
        windows.append((start, end, step))
    return windows


def apply(doc, segments, overwrite=False):
    """Attach each spoken segment to a step (by its middle point). Every step
    with speech gets a "narration" field; empty captions are filled from it.
    Returns the number of captions filled."""
    windows = step_windows(doc["steps"])
    if not windows:
        return 0
    spoken = {id(step): [] for _, _, step in windows}
    for seg in segments:
        mid = (seg["start"] + seg["end"]) / 2
        for start, end, step in windows:
            if start <= mid < end:
                spoken[id(step)].append(seg["text"].strip())
                break
    filled = 0
    for _, _, step in windows:
        text = " ".join(t for t in spoken[id(step)] if t)
        step.pop("narration", None)
        if not text:
            continue
        step["narration"] = text
        if overwrite or not (step.get("caption") or "").strip():
            step["caption"] = text
            filled += 1
    return filled


def write_transcript(out_dir, doc, result, model):
    lines = [f"Transcript of {doc.get('source_video', 'the recording')}",
             f"Speech recognition: faster-whisper, model {model}, "
             f"language {result.get('language') or 'unknown'}", ""]
    for seg in result.get("segments", []):
        lines.append(f"[{stepdoc.fmt_ts(seg['start'])[:8]}] {seg['text']}")
    if not result.get("segments"):
        lines.append("(no speech found)")
    path = Path(out_dir) / TRANSCRIPT_NAME
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def transcribe(video, out_dir, doc, ffmpeg, model=DEFAULT_MODEL, python=None,
               language=None, progress=None, cancel=None):
    """Transcribe the recording and update doc in memory (the caller saves
    it). Returns a summary dict: segments, filled, language, audio."""
    python = python or find_python()
    if not python:
        raise TranscribeError(WHISPER_MISSING_HELP)
    video = Path(video)
    if not video.is_file():
        raise TranscribeError(f"The original recording was not found: {video}")
    with tempfile.TemporaryDirectory(prefix="screencap_audio_") as tmp:
        wav = Path(tmp) / "audio.wav"
        if not extract_audio(ffmpeg, video, wav):
            doc["narration"] = {"model": model, "language": None, "segments": 0,
                                "transcript": None, "audio": False}
            return {"segments": 0, "filled": 0, "language": None, "audio": False,
                    "result": []}
        result = run_worker(python, wav, model, Path(tmp) / "result.json",
                            language, progress, cancel)
    segments = result.get("segments", [])
    filled = apply(doc, segments)
    write_transcript(out_dir, doc, result, model)
    doc["narration"] = {"model": model, "language": result.get("language"),
                        "segments": len(segments), "transcript": TRANSCRIPT_NAME,
                        "audio": True}
    return {"segments": len(segments), "filled": filled,
            "language": result.get("language"), "audio": True, "result": segments}
