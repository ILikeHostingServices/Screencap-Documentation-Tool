#!/usr/bin/env python3
#
# screencap.py
# 2026-10-01
# Version: v1.0.0
#
# PURPOSE:
# Scans a source folder for screen recordings (.mp4, .mov, .mkv), uses FFmpeg
# scene detection to find the moments where the screen changes, and saves a
# screenshot of each step plus a Markdown index for writing documentation.
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

VERSION = "1.0.0"
VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv"}
SCRIPT_DIR = Path(__file__).resolve().parent
INDEX_NAME = "steps.md"
MANIFEST_NAME = "steps.json"

# Exit codes
EXIT_OK = 0
EXIT_VIDEO_FAILED = 1
EXIT_SETUP_ERROR = 2

log = logging.getLogger("screencap")

PTS_RE = re.compile(r"pts_time:\s*([0-9]+(?:\.[0-9]+)?)")
SCORE_RE = re.compile(r"lavfi\.scene_score=\s*([0-9]+(?:\.[0-9]+)?)")
OUT_TIME_RE = re.compile(r"^out_time_(?:us|ms)=([0-9]+)")


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
    for candidate in (SCRIPT_DIR / "tools" / "ffmpeg" / "bin" / exe,
                      SCRIPT_DIR / "tools" / "ffmpeg" / exe):
        if candidate.is_file():
            return str(candidate)
    return shutil.which(name)


def run(cmd, **kwargs):
    """Run a command and capture text output without ever invoking a shell."""
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          text=True, encoding="utf-8", errors="replace", **kwargs)


def fmt_ts(seconds, sep=":"):
    """Format seconds as HH:MM:SS.mmm (sep '-' gives a Windows-safe filename)."""
    ms_total = int(round(max(seconds, 0.0) * 1000))
    h, rem = divmod(ms_total, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}{sep}{m:02d}{sep}{s:02d}.{ms:03d}"


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


def detect_changes(ffmpeg, video, duration, args):
    """Return a list of (time_seconds, scene_score) for every analyzed frame
    whose scene score is above the threshold."""
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
                            text=True, encoding="utf-8", errors="replace")
    stderr_lines = []

    def read_stderr():
        for line in proc.stderr:
            stderr_lines.append(line)

    reader = threading.Thread(target=read_stderr, daemon=True)
    reader.start()

    last_report = 0.0
    for line in proc.stdout:
        m = OUT_TIME_RE.match(line.strip())
        if m and duration:
            # ffmpeg reports out_time_ms in microseconds as well (historic quirk)
            pos = int(m.group(1)) / 1_000_000
            now = time.monotonic()
            if now - last_report >= 2:
                pct = min(100.0, pos / duration * 100)
                print(f"    analyzing... {pct:5.1f}%", flush=True)
                last_report = now
    proc.wait()
    reader.join()

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

def write_index(out_dir, video, duration, steps, args):
    lines = [
        f"# {video.stem}",
        "",
        f"- Source video: `{video.name}`",
        f"- Duration: {fmt_ts(duration)}",
        f"- Generated: {time.strftime('%Y-%m-%d %H:%M:%S')} by screencap.py v{VERSION}",
        f"- Settings: threshold={args.threshold}, debounce={args.debounce}s, "
        f"capture-point={args.capture_point}, min-gap={args.min_gap}s",
        f"- Steps captured: {len(steps)}",
        "",
    ]
    for i, step in enumerate(steps, 1):
        label = ""
        if step["reason"] == "start":
            label = " (start of video)"
        elif i == len(steps):
            label = " (end of video)"
        lines.append(f"## Step {i} - {fmt_ts(step['time'])}{label}")
        lines.append("")
        details = []
        if step["still_from"] is not None and step["still_to"] is not None:
            details.append(f"Screen stable from {fmt_ts(step['still_from'])} "
                           f"to {fmt_ts(step['still_to'])}")
        if step["score"] is not None:
            details.append(f"change score {step['score']:.3f}")
        if details:
            lines.append("_" + ", ".join(details) + "._")
            lines.append("")
        lines.append(f"![Step {i}]({step['file']})")
        lines.append("")
        lines.append("_Notes:_")
        lines.append("")
    (out_dir / INDEX_NAME).write_text("\n".join(lines), encoding="utf-8")

    manifest = {
        "tool_version": VERSION,
        "source_video": video.name,
        "duration": duration,
        "settings": {k: getattr(args, k) for k in
                     ("threshold", "debounce", "capture_point", "settle", "lead",
                      "max_wait", "min_gap",
                      "analyze_fps", "analyze_width", "format")},
        "steps": steps,
    }
    (out_dir / MANIFEST_NAME).write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def clear_previous_output(out_dir):
    """Remove only files this tool created, never anything else in the folder."""
    for f in out_dir.glob("step_*"):
        if f.is_file() and f.suffix.lower() in (".png", ".jpg"):
            f.unlink()
    for name in (INDEX_NAME, MANIFEST_NAME):
        f = out_dir / name
        if f.is_file():
            f.unlink()


def process_video(ffmpeg, ffprobe, video, out_dir, args):
    if (out_dir / INDEX_NAME).is_file() and not args.force:
        log.info("Skipping %s (already processed, use --force to redo)", video.name)
        return "skipped"

    started = time.monotonic()
    duration, width, height = probe_duration(ffprobe, video)
    log.info("Processing %s (%s, %sx%s)", video, fmt_ts(duration), width, height)

    events = detect_changes(ffmpeg, video, duration, args)
    steps = group_changes(events, duration, args)
    log.info("  %d raw changes -> %d steps", len(events), len(steps))

    if args.dry_run:
        for i, step in enumerate(steps, 1):
            log.info("  [dry run] step %03d at %s (%s)", i, fmt_ts(step["time"]), step["reason"])
        return "ok"

    out_dir.mkdir(parents=True, exist_ok=True)
    if args.force:
        clear_previous_output(out_dir)

    for i, step in enumerate(steps, 1):
        name = f"step_{i:03d}_{fmt_ts(step['time'], sep='-')}.{args.format}"
        extract_frame(ffmpeg, video, step["time"], out_dir / name, args)
        step["file"] = name

    write_index(out_dir, video, duration, steps, args)
    log.info("  Saved %d screenshots to %s (%.1fs)", len(steps), out_dir,
             time.monotonic() - started)
    return "ok"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args(argv):
    p = argparse.ArgumentParser(
        description="Automatically capture a screenshot of every step in screen "
                    "recordings using FFmpeg scene detection.")
    p.add_argument("-s", "--source", type=Path, default=SCRIPT_DIR / "source",
                   help="Folder containing videos (default: ./source)")
    p.add_argument("-o", "--output", type=Path, default=SCRIPT_DIR / "output",
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
    p.add_argument("-f", "--format", choices=("png", "jpg"), default="png",
                   help="Screenshot image format (default: png)")
    p.add_argument("--force", action="store_true",
                   help="Reprocess videos that already have output")
    p.add_argument("--dry-run", action="store_true",
                   help="Detect and list steps without saving screenshots")
    p.add_argument("--ffmpeg", help="Path to ffmpeg executable")
    p.add_argument("--ffprobe", help="Path to ffprobe executable")
    p.add_argument("-v", "--verbose", action="store_true", help="Debug logging")
    p.add_argument("--version", action="version", version=f"%(prog)s v{VERSION}")
    args = p.parse_args(argv)

    if not 0 < args.threshold < 1:
        p.error("--threshold must be between 0 and 1")
    for name in ("debounce", "settle", "lead", "max_wait", "min_gap",
                 "analyze_fps"):
        if getattr(args, name) < 0:
            p.error(f"--{name.replace('_', '-')} cannot be negative")
    return args


def setup_logging(output, verbose):
    log.setLevel(logging.DEBUG)
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.DEBUG if verbose else logging.INFO)
    console.setFormatter(logging.Formatter("%(message)s"))
    log.addHandler(console)
    try:
        output.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(output / "screencap.log", encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s",
                                          "%Y-%m-%d %H:%M:%S"))
        log.addHandler(fh)
    except OSError as exc:
        log.warning("Could not open log file in %s: %s", output, exc)


def main(argv=None):
    args = parse_args(argv)
    source = args.source.expanduser().resolve()
    output = args.output.expanduser().resolve()
    setup_logging(output, args.verbose)
    log.info("screencap.py v%s", VERSION)

    ffmpeg = find_tool("ffmpeg", args.ffmpeg)
    ffprobe = find_tool("ffprobe", args.ffprobe)
    if not ffmpeg or not ffprobe:
        log.error("FFmpeg was not found. Install it and try again:\n"
                  "  Windows 11:  winget install --id Gyan.FFmpeg -e\n"
                  "               (then open a NEW terminal window)\n"
                  "  or extract a build into tools\\ffmpeg\\ next to this script\n"
                  "  Linux:       sudo apt install ffmpeg\n"
                  "  macOS:       brew install ffmpeg")
        return EXIT_SETUP_ERROR
    log.debug("ffmpeg: %s | ffprobe: %s", ffmpeg, ffprobe)

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
            results[process_video(ffmpeg, ffprobe, video, out_dir, args)] += 1
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
