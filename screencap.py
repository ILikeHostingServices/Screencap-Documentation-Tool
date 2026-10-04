#!/usr/bin/env python3
#
# screencap.py
# 2026-10-04
# Version: v1.11.0
#
# PURPOSE:
# Scans a source folder for screen recordings (.mp4, .mov, .mkv), uses FFmpeg
# scene detection to find the moments where the screen changes, and saves a
# screenshot of each step plus a Markdown index for writing documentation.
# Full frames are kept in originals/ so steps can be edited and re-rendered
# (see stepdoc.py and the GUI step editor).
#
# Requires: Python 3.8+ and FFmpeg (ffmpeg + ffprobe). Standard library only.
# Works on Windows 11, Linux, and macOS.

import argparse
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import apppaths  # noqa: E402
import export  # noqa: E402
import imaging  # noqa: E402
import presets  # noqa: E402
import redact  # noqa: E402
import stepdoc  # noqa: E402
import transcribe  # noqa: E402
import version  # noqa: E402
from stepdoc import (INDEX_NAME, MANIFEST_NAME, ORIGINALS_DIR, Cancelled,  # noqa: E402,F401
                     UNREDACTED_DIR, UNREDACTED_INDEX, fmt_ts)

VERSION = "1.11.0"
VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv"}

FFMPEG_MISSING_HELP = (
    "FFmpeg was not found. Install it and try again:\n"
    "  Windows 11:  winget install --id Gyan.FFmpeg -e\n"
    "               (then open a NEW terminal window)\n"
    "  or extract a build into tools\\ffmpeg\\bin\\ next to this script\n"
    "  Linux:       sudo apt install ffmpeg\n"
    "  macOS:       brew install ffmpeg")

# Exit codes
EXIT_OK = 0
EXIT_VIDEO_FAILED = 1
EXIT_SETUP_ERROR = 2

log = logging.getLogger("screencap")

PTS_RE = re.compile(r"pts_time:\s*([0-9]+(?:\.[0-9]+)?)")
SCORE_RE = re.compile(r"lavfi\.scene_score=\s*([0-9]+(?:\.[0-9]+)?)")
OUT_TIME_RE = re.compile(r"^out_time_(?:us|ms)=([0-9]+)")

NO_WINDOW = stepdoc.NO_WINDOW


# ---------------------------------------------------------------------------
# Setup helpers
# ---------------------------------------------------------------------------

def find_tool(name, explicit=None):
    """Locate ffmpeg/ffprobe: explicit path, then tools/ffmpeg/bin next to
    this script (portable Windows install), then the system PATH."""
    if explicit:
        p = Path(explicit)
        if p.is_file():
            return str(p)
        log.error("%s not found at --%s path: %s", name, name, explicit)
        return None
    exe = name + (".exe" if os.name == "nt" else "")
    for candidate in (apppaths.APP_DIR / "tools" / "ffmpeg" / "bin" / exe,
                      apppaths.APP_DIR / "tools" / "ffmpeg" / exe):
        if candidate.is_file():
            return str(candidate)
    return shutil.which(name)


def run(cmd):
    """Run a command and capture text output without ever invoking a shell."""
    return stepdoc.run_quiet(cmd)


# ---------------------------------------------------------------------------
# Video discovery
# ---------------------------------------------------------------------------

def discover_videos(source, recursive):
    pattern = "**/*" if recursive else "*"
    videos = [p for p in source.glob(pattern)
              if p.is_file() and p.suffix.lower() in VIDEO_EXTENSIONS]
    return sorted(videos, key=lambda p: str(p).lower())


def output_dir_for(video, source, output, all_videos):
    """Mirror the source layout. If two videos share a name with different
    extensions (demo.mp4 and demo.mkv) append the extension to keep both."""
    rel = video.relative_to(source)
    stem = video.stem
    clashes = [v for v in all_videos if v.parent == video.parent
               and v.stem.lower() == stem.lower() and v != video]
    if clashes:
        stem = f"{stem}_{video.suffix.lstrip('.').lower()}"
    return output / rel.parent / stem


# ---------------------------------------------------------------------------
# FFmpeg work
# ---------------------------------------------------------------------------

def probe_duration(ffprobe, video):
    res = run([ffprobe, "-v", "error", "-select_streams", "v:0",
               "-show_entries", "format=duration:stream=duration,width,height",
               "-of", "json", str(video)])
    if res.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {res.stderr.strip()[-500:]}")
    data = json.loads(res.stdout or "{}")
    streams = data.get("streams") or []
    if not streams:
        raise RuntimeError("no video stream found")
    duration = None
    for value in (data.get("format", {}).get("duration"), streams[0].get("duration")):
        try:
            duration = float(value)
            break
        except (TypeError, ValueError):
            continue
    if not duration or duration <= 0:
        raise RuntimeError("could not determine video duration")
    return duration, streams[0].get("width"), streams[0].get("height")


def detect_changes(ffmpeg, video, duration, args, progress=None, cancel=None):
    """Return a list of (time_seconds, scene_score) for every analyzed frame
    whose scene score is above the threshold.

    progress: optional callable(fraction 0-1) for UI updates.
    cancel:   optional threading.Event; when set, FFmpeg is stopped."""
    filters = []
    if args.analyze_fps > 0:
        filters.append(f"fps={args.analyze_fps}")
    if args.analyze_width > 0:
        filters.append(f"scale={args.analyze_width}:-2")
    filters.append(f"select='gt(scene,{args.threshold})'")
    filters.append("metadata=print:key=lavfi.scene_score")

    cmd = [ffmpeg, "-hide_banner", "-nostats", "-nostdin",
           "-i", str(video), "-map", "0:v:0", "-an", "-sn", "-dn",
           "-vf", ",".join(filters),
           "-progress", "pipe:1", "-f", "null", "-"]
    log.debug("Running: %s", " ".join(cmd))

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            stdin=subprocess.DEVNULL, creationflags=NO_WINDOW,
                            text=True, encoding="utf-8", errors="replace")
    stderr_lines = []

    def read_stderr():
        for line in proc.stderr:
            stderr_lines.append(line)

    reader = threading.Thread(target=read_stderr, daemon=True)
    reader.start()

    last_report = 0.0
    for line in proc.stdout:
        if cancel is not None and cancel.is_set():
            proc.kill()
            break
        m = OUT_TIME_RE.match(line.strip())
        if m and duration:
            # ffmpeg reports out_time_ms in microseconds as well (historic quirk)
            fraction = min(1.0, int(m.group(1)) / 1_000_000 / duration)
            if progress is not None:
                progress(fraction)
                continue
            now = time.monotonic()
            if now - last_report >= 2 and sys.stdout is not None:
                print(f"    analyzing... {fraction * 100:5.1f}%", flush=True)
                last_report = now
    proc.wait()
    reader.join()
    proc.stdout.close()
    proc.stderr.close()
    if cancel is not None and cancel.is_set():
        raise Cancelled()

    if proc.returncode != 0:
        tail = "".join(stderr_lines[-15:]).strip()
        raise RuntimeError(f"ffmpeg scene detection failed:\n{tail}")

    events = []
    pending_time = None
    for line in stderr_lines:
        m = PTS_RE.search(line)
        if m and "Parsed_metadata" in line:
            pending_time = float(m.group(1))
            continue
        m = SCORE_RE.search(line)
        if m and pending_time is not None:
            events.append((pending_time, float(m.group(1))))
            pending_time = None
    return events


def group_changes(events, duration, args):
    """Collapse bursts of changes (typing, animations, window fades) into
    single change groups, then pick one screenshot time per step.

    A new group starts when the screen has been quiet for more than
    `debounce` seconds, or when a burst runs longer than `max_wait`.

    capture point "end" (default): the still period between two changes is
    one step, captured just before the next change starts. This shows the
    finished state of each step (form filled in, progress bar complete,
    cursor on the button about to be clicked).
    capture point "start": captured `settle` seconds after each change."""
    groups = []
    for t, score in events:
        if groups and (t - groups[-1]["end"] <= args.debounce
                       and t - groups[-1]["start"] <= args.max_wait):
            groups[-1]["end"] = t
            groups[-1]["score"] = max(groups[-1]["score"], score)
        else:
            groups.append({"start": t, "end": t, "score": score})

    last_frame = max(duration - 0.1, 0.0)
    steps = []
    if args.capture_point == "end":
        # Still periods: [0, g1.start), [g1.end, g2.start), ... [gN.end, end]
        seg_start, seg_score, seg_reason = 0.0, None, "start"
        for g in groups + [{"start": duration, "end": duration, "score": None}]:
            seg_end = g["start"]
            t = min(max(seg_end - args.lead, seg_start), last_frame)
            steps.append({"time": max(t, 0.0), "still_from": seg_start,
                          "still_to": min(seg_end, duration),
                          "score": seg_score, "reason": seg_reason})
            seg_start, seg_score, seg_reason = g["end"], g["score"], "change"
    else:
        steps.append({"time": min(args.settle, duration / 2), "still_from": 0.0,
                      "still_to": None, "score": None, "reason": "start"})
        for g in groups:
            steps.append({"time": min(g["end"] + args.settle, last_frame),
                          "still_from": g["end"], "still_to": None,
                          "score": g["score"], "reason": "change"})
        steps.append({"time": last_frame, "still_from": None, "still_to": None,
                      "score": None, "reason": "end"})

    # Drop captures that land too close to the previous one, but always keep
    # the final state of the video.
    steps.sort(key=lambda s: s["time"])
    filtered = []
    for step in steps:
        if filtered and step["time"] - filtered[-1]["time"] < args.min_gap:
            if step is steps[-1]:
                filtered[-1] = step
            continue
        filtered.append(step)
    return filtered


def extract_frame(ffmpeg, video, t, dest, args):
    cmd = [ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
           "-ss", f"{t:.3f}", "-i", str(video), "-map", "0:v:0", "-frames:v", "1"]
    if args.format == "jpg":
        cmd += ["-q:v", "2"]
    cmd.append(str(dest))
    res = run(cmd)
    if res.returncode != 0 or not dest.is_file():
        raise RuntimeError(f"frame extraction at {fmt_ts(t)} failed: "
                           f"{res.stderr.strip()[-300:]}")


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def settings_snapshot(args):
    return {k: getattr(args, k) for k in
            ("threshold", "debounce", "capture_point", "settle", "lead",
             "max_wait", "min_gap", "analyze_fps", "analyze_width", "format",
             "no_dedup", "dedup_threshold", "no_highlight", "crop", "no_redact")}


def clear_previous_output(out_dir):
    """Before reprocessing, move the previous run's files (including any
    captions in steps.json and notes in steps.md) into a dated backup folder
    instead of deleting them. Only files this tool creates are touched."""
    targets = [f for f in out_dir.glob("step_*")
               if f.is_file() and f.suffix.lower() in (".png", ".jpg")]
    targets += [out_dir / n for n in (INDEX_NAME, MANIFEST_NAME, ORIGINALS_DIR,
                                      UNREDACTED_DIR, UNREDACTED_INDEX, export.EXPORT_DIR,
                                      transcribe.TRANSCRIPT_NAME)
                if (out_dir / n).exists()]
    targets += [f for f in out_dir.glob("steps.*.md") if f.is_file()]
    if not targets:
        return None
    backup = out_dir / f"previous-{time.strftime('%Y%m%d-%H%M%S')}"
    backup.mkdir()
    for f in targets:
        shutil.move(str(f), str(backup / f.name))
    log.info("  Previous output moved to %s", backup.name)
    return backup


def process_video(ffmpeg, ffprobe, video, out_dir, args, progress=None, cancel=None):
    """Process one video. progress: optional callable(fraction 0-1, text).
    cancel: optional threading.Event checked between stages."""
    def report(fraction, text):
        if progress is not None:
            progress(fraction, text)

    if (out_dir / INDEX_NAME).is_file() and not args.force:
        log.info("Skipping %s (already processed, use --force to redo)", video.name)
        return "skipped", None

    started = time.monotonic()
    duration, width, height = probe_duration(ffprobe, video)
    log.info("Processing %s (%s, %sx%s)", video, fmt_ts(duration), width, height)

    # Analysis is most of the work; frame extraction is the last 15%
    report(0.0, "Analyzing")
    events = detect_changes(ffmpeg, video, duration, args,
                            progress=(lambda f: report(f * 0.85, "Analyzing"))
                            if progress else None,
                            cancel=cancel)
    steps = group_changes(events, duration, args)
    log.info("  %d raw changes -> %d steps", len(events), len(steps))

    if args.dry_run:
        for i, step in enumerate(steps, 1):
            log.info("  [dry run] step %03d at %s (%s)", i, fmt_ts(step["time"]), step["reason"])
        return "ok", len(steps)

    out_dir.mkdir(parents=True, exist_ok=True)
    if args.force:
        clear_previous_output(out_dir)
    (out_dir / ORIGINALS_DIR).mkdir(exist_ok=True)

    doc = stepdoc.new_document(video.name, duration, width, height, args.format,
                               settings_snapshot(args), VERSION)
    doc["highlight"] = not args.no_highlight
    doc["source_path"] = str(video.resolve())   # lets the GUI open it in VLC
    if args.crop:
        doc["crop"] = stepdoc.clamp_rect(args.crop, width, height)
    doc["redact"] = not args.no_redact
    doc["redact_patterns"] = list(args.redact_pattern or [])
    kept_thumbs = []

    def dedup_check(new, image):
        """Mark new as a duplicate of an earlier kept step, if it is one.
        The final step is always kept so the end result is documented."""
        if args.no_dedup:
            return False
        thumb = imaging.thumbnail(ffmpeg, image)
        dup = imaging.find_duplicate(thumb, kept_thumbs, args.dedup_threshold)
        if dup is not None and new["reason"] != "end":
            new["deleted_reason"] = "duplicate"
            new["duplicate_of_time"] = doc["steps"][dup]["time"]
            log.debug("  %s duplicates step at %s", fmt_ts(new["time"]),
                      fmt_ts(new["duplicate_of_time"]))
            return True
        kept_thumbs.append(thumb)
        return False
    for i, step in enumerate(steps, 1):
        if cancel is not None and cancel.is_set():
            raise Cancelled()
        report(0.85 + 0.10 * (i - 1) / len(steps), f"Saving screenshot {i}/{len(steps)}")
        orig = f"{ORIGINALS_DIR}/{stepdoc.capture_name(step['time'], args.format)}"
        extract_frame(ffmpeg, video, step["time"], out_dir / orig, args)
        new = stepdoc.new_step(step["time"], orig, step["still_from"], step["still_to"],
                               step["score"], step["reason"])
        if dedup_check(new, out_dir / orig):
            doc["deleted_steps"].append(new)
        else:
            doc["steps"].append(new)
    if doc["deleted_steps"]:
        log.info("  %d duplicate screenshot(s) removed (restore them in the Steps tab)",
                 len(doc["deleted_steps"]))
    # Always analyze, so highlighting can be switched on later in the editor
    stepdoc.ensure_change_boxes(out_dir, doc, ffmpeg)

    tesseract = None if args.no_redact else redact.find_tesseract(args.tesseract)
    stepdoc.render(out_dir, doc, ffmpeg,
                   progress=(lambda f, t: report(0.95 + 0.05 * f, t)) if progress else None,
                   cancel=cancel, tesseract=tesseract)
    log.info("  Saved %d screenshots to %s (%.1fs)", len(doc["steps"]), out_dir,
             time.monotonic() - started)
    report(1.0, "Done")
    return "ok", len(doc["steps"])


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_formats(text):
    formats = [f.strip().lower() for f in text.split(",") if f.strip()]
    bad = [f for f in formats if f not in export.FORMATS]
    if bad or not formats:
        raise argparse.ArgumentTypeError(f"choose from {', '.join(export.FORMATS)}")
    return formats


def export_video(out_dir, args):
    """Export one processed recording in every format asked for. Returns the
    number of exports that failed."""
    doc = stepdoc.load(out_dir)
    if doc is None:
        return 0
    meta = doc.setdefault("document", {})
    if args.doc_author is not None or args.doc_version is not None:
        if args.doc_author is not None:
            meta["author"] = args.doc_author
        if args.doc_version is not None:
            meta["version"] = args.doc_version
        stepdoc.save(out_dir, doc)
    failed = 0
    for fmt in args.export:
        try:
            dest = export.export(out_dir, doc, fmt, pandoc=args.pandoc, browser=args.browser)
            log.info("  Exported %s", dest)
        except Exception as exc:
            failed += 1
            log.error("  Export to %s failed: %s", fmt, exc)
    return failed


def transcribe_video(video, out_dir, args, ffmpeg, progress=None, cancel=None):
    """Turn the recording's narration into captions for steps that have none.
    Returns 1 if it failed, else 0. Recordings already transcribed are
    skipped (use --force to start over)."""
    doc = stepdoc.load(out_dir)
    if doc is None:
        return 0
    if doc.get("narration"):
        log.info("  Narration already transcribed (%s)", transcribe.TRANSCRIPT_NAME)
        return 0
    log.info("  Transcribing narration (model %s)...", args.whisper_model)
    started = time.monotonic()
    try:
        summary = transcribe.transcribe(doc.get("source_path") or video, out_dir, doc, ffmpeg,
                                        args.whisper_model, args.whisper_python,
                                        progress=progress, cancel=cancel)
    except transcribe.TranscribeError as exc:
        log.error("  %s", exc)
        return 1
    stepdoc.save(out_dir, doc)
    if not summary["audio"]:
        log.info("  No audio track, nothing to transcribe")
    elif not summary["segments"]:
        log.info("  No speech found in the recording")
    else:
        log.info("  %d spoken passage(s), %d caption(s) filled, saved %s (%.1fs)",
                 summary["segments"], summary["filled"], transcribe.TRANSCRIPT_NAME,
                 time.monotonic() - started)
    return 0


def parse_crop(text):
    try:
        values = [int(v) for v in text.split(":")]
        if len(values) != 4 or values[2] <= 0 or values[3] <= 0 or min(values[:2]) < 0:
            raise ValueError
        return values
    except ValueError:
        raise argparse.ArgumentTypeError("use X:Y:W:H with whole pixel numbers, e.g. 0:0:1920:1080")


def parse_args(argv):
    p = argparse.ArgumentParser(
        description="Automatically capture a screenshot of every step in screen "
                    "recordings using FFmpeg scene detection.")
    p.add_argument("-s", "--source", type=Path, default=apppaths.DATA_DIR / "source",
                   help="Folder containing videos (default: ./source)")
    p.add_argument("-o", "--output", type=Path, default=apppaths.DATA_DIR / "output",
                   help="Folder to write screenshots to (default: ./output)")
    p.add_argument("-r", "--recursive", action="store_true",
                   help="Also scan subfolders of the source folder")
    p.add_argument("-t", "--threshold", type=float, default=0.005,
                   help="Scene change sensitivity 0-1. Lower = more screenshots "
                        "(default: 0.005, tuned for screen recordings)")
    p.add_argument("--debounce", type=float, default=1.0,
                   help="Seconds the screen must be still before a step is "
                        "captured (default: 1.0)")
    p.add_argument("-c", "--capture-point", choices=("end", "start"), default="end",
                   help="end = capture the settled screen just before the next "
                        "change (default, shows each step finished). start = "
                        "capture shortly after each change")
    p.add_argument("--lead", type=float, default=0.25,
                   help="capture-point end: seconds before the next change to "
                        "take the screenshot (default: 0.25)")
    p.add_argument("--settle", type=float, default=0.5,
                   help="capture-point start: seconds to wait after a change "
                        "so animations can finish (default: 0.5)")
    p.add_argument("--max-wait", type=float, default=10.0,
                   help="Force a capture after this many seconds of continuous "
                        "change, e.g. scrolling or a progress bar (default: 10)")
    p.add_argument("--min-gap", type=float, default=1.0,
                   help="Minimum seconds between two screenshots (default: 1.0)")
    p.add_argument("--analyze-fps", type=float, default=5.0,
                   help="Frames per second examined for changes, 0 = every "
                        "frame (default: 5)")
    p.add_argument("--analyze-width", type=int, default=640,
                   help="Downscale width used for analysis only, 0 = full size. "
                        "Screenshots are always full resolution (default: 640)")
    p.add_argument("--no-dedup", action="store_true",
                   help="Keep screenshots that look identical to an earlier one")
    p.add_argument("--dedup-threshold", type=float, default=0.01,
                   help="Two screenshots count as duplicates when at most this "
                        "percent of the picture differs (default: 0.01)")
    p.add_argument("--crop", type=parse_crop, metavar="X:Y:W:H",
                   help="Crop every screenshot to this rectangle, in pixels of the "
                        "recording (for example 0:0:1920:1080 for the left monitor of "
                        "a dual-screen recording). Originals stay uncropped")
    p.add_argument("--no-redact", action="store_true",
                   help="Do not blur sensitive information (passwords, keys, IP "
                        "addresses...). By default it is blurred and an unblurred copy "
                        "is kept in unredacted/")
    p.add_argument("--redact-pattern", action="append", metavar="REGEX",
                   help="Extra text to blur, as a regular expression (case-insensitive). "
                        "Repeat for several, e.g. --redact-pattern \"corp\\.example\\.com\"")
    p.add_argument("--tesseract", help="Path to the tesseract executable (OCR)")
    p.add_argument("--export", type=parse_formats, metavar="FORMATS",
                   help="After processing, export each recording as a document: any "
                        "of html, docx, pdf, comma separated (e.g. html,pdf). Already "
                        "processed recordings are exported too")
    p.add_argument("--transcribe", action="store_true",
                   help="Turn spoken narration into captions for steps that have none, "
                        "and save transcript.txt. Needs the optional speech recognition "
                        "download (see README). Already processed recordings are "
                        "transcribed too")
    p.add_argument("--whisper-model", default=transcribe.DEFAULT_MODEL, metavar="NAME",
                   help="Speech recognition model: tiny, base, small, or medium, or the "
                        "English-only tiny.en, base.en, small.en, medium.en. Bigger is "
                        "more accurate but slower (default: %(default)s)")
    p.add_argument("--whisper-python", metavar="PATH",
                   help="Python that has faster-whisper installed (default: the "
                        "whisper-env folder made by the installer)")
    p.add_argument("--doc-author", help="Author shown in exported documents")
    p.add_argument("--doc-version", help="Version shown in exported documents "
                                          "(default: v1.0.0)")
    p.add_argument("--pandoc", help="Path to pandoc (needed for docx export)")
    p.add_argument("--browser", help="Path to Microsoft Edge, Google Chrome, or "
                                     "Chromium (needed for pdf export)")
    p.add_argument("--no-highlight", action="store_true",
                   help="Do not draw a red box around what changed in each step")
    p.add_argument("-f", "--format", choices=("png", "jpg"), default="png",
                   help="Screenshot image format (default: png)")
    p.add_argument("--force", action="store_true",
                   help="Reprocess videos that already have output")
    p.add_argument("--dry-run", action="store_true",
                   help="Detect and list steps without saving screenshots")
    p.add_argument("--ffmpeg", help="Path to ffmpeg executable")
    p.add_argument("--ffprobe", help="Path to ffprobe executable")
    p.add_argument("--preset", metavar="NAME",
                   help="Start from a saved preset (see --list-presets). Any option "
                        "given on the command line overrides the preset")
    p.add_argument("--list-presets", action="store_true",
                   help="List the built-in and your saved presets, then exit")
    p.add_argument("-v", "--verbose", action="store_true", help="Debug logging")
    p.add_argument("--version", action="version",
                   version=f"{version.APP_NAME} v{version.RELEASE} (screencap.py v{VERSION})")
    # Two passes: read --preset first, make its values the defaults, then
    # parse again so options typed on the command line win over the preset
    first, _ = p.parse_known_args(argv)
    if first.list_presets:
        for name in presets.names():
            values = presets.get(name)
            shown = ", ".join(f"{k}={v}" for k, v in values.items()) or "defaults"
            print(f"{name}\n    {presets.describe(name)}\n    {shown}")
        p.exit()
    if first.preset:
        values = presets.get(first.preset)
        if values is None:
            p.error(f"unknown preset {first.preset!r}; choose from: {', '.join(presets.names())}")
        p.set_defaults(**values)
    args = p.parse_args(argv)

    if not 0 < args.threshold < 1:
        p.error("--threshold must be between 0 and 1")
    for rx in args.redact_pattern or []:
        try:
            re.compile(rx)
        except re.error as exc:
            p.error(f"--redact-pattern {rx!r} is not a valid regular expression: {exc}")
    for name in ("debounce", "settle", "lead", "max_wait", "min_gap",
                 "analyze_fps", "dedup_threshold"):
        if getattr(args, name) < 0:
            p.error(f"--{name.replace('_', '-')} cannot be negative")
    return args


def add_file_log(output):
    """Append a debug-level log to <output>/screencap.log. Returns the handler."""
    log.setLevel(logging.DEBUG)
    try:
        output.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(output / "screencap.log", encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s",
                                          "%Y-%m-%d %H:%M:%S"))
        log.addHandler(fh)
        return fh
    except OSError as exc:
        log.warning("Could not open log file in %s: %s", output, exc)
        return None


_cli_handlers = []


def setup_logging(output, verbose):
    # Remove handlers from an earlier main() call in the same process (tests)
    for h in _cli_handlers:
        log.removeHandler(h)
        h.close()
    _cli_handlers.clear()
    log.setLevel(logging.DEBUG)
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.DEBUG if verbose else logging.INFO)
    console.setFormatter(logging.Formatter("%(message)s"))
    log.addHandler(console)
    _cli_handlers.append(console)
    fh = add_file_log(output)
    if fh is not None:
        _cli_handlers.append(fh)


def main(argv=None):
    args = parse_args(argv)
    source = args.source.expanduser().resolve()
    output = args.output.expanduser().resolve()
    setup_logging(output, args.verbose)
    log.info("%s v%s (screencap.py v%s)", version.APP_NAME, version.RELEASE, VERSION)

    ffmpeg = find_tool("ffmpeg", args.ffmpeg)
    ffprobe = find_tool("ffprobe", args.ffprobe)
    if not ffmpeg or not ffprobe:
        log.error(FFMPEG_MISSING_HELP)
        return EXIT_SETUP_ERROR
    log.debug("ffmpeg: %s | ffprobe: %s", ffmpeg, ffprobe)
    if not args.no_redact and not args.dry_run and not redact.find_tesseract(args.tesseract):
        log.warning(redact.TESSERACT_MISSING_HELP)

    if args.transcribe and not args.dry_run and not transcribe.find_python(args.whisper_python):
        log.error(transcribe.WHISPER_MISSING_HELP)
        return EXIT_SETUP_ERROR

    if not source.is_dir():
        source.mkdir(parents=True, exist_ok=True)
        log.info("Created source folder %s - put your .mp4/.mov/.mkv files there.", source)
        return EXIT_OK

    videos = discover_videos(source, args.recursive)
    if not videos:
        log.info("No .mp4, .mov, or .mkv files found in %s", source)
        return EXIT_OK
    log.info("Found %d video(s) in %s", len(videos), source)

    results = {"ok": 0, "skipped": 0, "failed": 0}
    for video in videos:
        out_dir = output_dir_for(video, source, output, videos)
        try:
            status, _ = process_video(ffmpeg, ffprobe, video, out_dir, args)
            results[status] += 1
            if (args.transcribe and not args.dry_run
                    and transcribe_video(video, out_dir, args, ffmpeg)):
                results["failed"] += 1
            if args.export and not args.dry_run and export_video(out_dir, args):
                results["failed"] += 1
        except Exception as exc:  # keep going with the remaining videos
            results["failed"] += 1
            log.error("FAILED %s: %s", video.name, exc)
            log.debug("Details", exc_info=True)

    log.info("Done. processed=%d skipped=%d failed=%d. Output: %s",
             results["ok"], results["skipped"], results["failed"], output)
    return EXIT_VIDEO_FAILED if results["failed"] else EXIT_OK


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(130)
