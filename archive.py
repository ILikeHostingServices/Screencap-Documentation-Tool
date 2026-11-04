#!/usr/bin/env python3
#
# archive.py
# 2026-11-04
# Version: v1.0.0
#
# PURPOSE:
# Moves finished recordings out of the way and brings them back. Archiving
# a recording packs everything about it into one .zip in the archive
# folder (Output/Archived recordings by default):
#   video/<name>         the recording, re-encoded smaller unless that is
#                        turned off (kept as is when re-encoding does not
#                        make it smaller)
#   video/<name>.events.json   the built-in recorder's clicks and keys
#   output/...           its output folder: screenshots, originals,
#                        steps.json (captions and edits), exports, and
#                        earlier runs (previous-*)
#   archive.json         what is in the archive and where it came from
# The originals are deleted only after the .zip is written and checked.
# Restoring unpacks the video into the recordings folder and the output
# folder into the output folder, where they were (or with " (restored)"
# added when something of the same name is already there), and then
# deletes the .zip. Standard library and FFmpeg only.

import hashlib
import json
import os
import shutil
import subprocess
import time
import zipfile
from pathlib import Path

import recorder
import stepdoc

ARCHIVE_DIR_NAME = "Archived recordings"
MANIFEST = "archive.json"
FORMAT = 1
# The kinds of video the recordings folder holds (as screencap.VIDEO_EXTENSIONS)
VIDEO_EXTENSIONS = (".mp4", ".mov", ".mkv")
NO_WINDOW = stepdoc.NO_WINDOW


class ArchiveError(RuntimeError):
    pass


def archive_dir(output):
    return Path(output) / ARCHIVE_DIR_NAME


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def shrink_video(ffmpeg, video, dest, cancel=None):
    """Re-encode video into dest with settings that suit screen recordings
    (H.264, CRF 28, slow preset, sound as AAC 96k). Returns dest, or None
    when FFmpeg fails or the result is not smaller than the original."""
    cmd = [ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
           "-i", str(video), "-map", "0:v:0", "-map", "0:a?",
           "-c:v", "libx264", "-preset", "slow", "-crf", "28", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "96k", str(dest)]
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                            stdin=subprocess.DEVNULL, creationflags=NO_WINDOW)
    while proc.poll() is None:
        if cancel is not None and cancel.wait(0.2):
            proc.kill()
            proc.wait()
            dest.unlink(missing_ok=True)
            raise stepdoc.Cancelled()
    proc.stderr.close()
    if proc.returncode != 0 or not dest.is_file() \
            or dest.stat().st_size >= Path(video).stat().st_size:
        dest.unlink(missing_ok=True)
        return None
    return dest


def _free_name(folder, name, suffix=""):
    """name (plus suffix) in folder, or "name (2)" and so on if taken."""
    candidate = folder / f"{name}{suffix}"
    n = 2
    while candidate.exists():
        candidate = folder / f"{name} ({n}){suffix}"
        n += 1
    return candidate


def archive_recording(video, out_dir, source, output, ffmpeg=None, shrink=True,
                      progress=None, cancel=None, dest_dir=None):
    """Pack one recording and its output folder into a .zip in dest_dir (the
    archive folder in output by default), check it, then delete the
    originals. Returns the .zip path.
    progress: optional callable(fraction 0-1, text)."""
    video, out_dir, source, output = Path(video), Path(out_dir), Path(source), Path(output)
    if not video.is_file():
        raise ArchiveError(f"{video.name} was not found.")

    def report(fraction, text):
        if progress is not None:
            progress(fraction, text)

    dest_dir = Path(dest_dir) if dest_dir else archive_dir(output)
    dest_dir.mkdir(parents=True, exist_ok=True)
    zip_path = _free_name(dest_dir, video.stem, ".zip")
    work = dest_dir / f".{zip_path.stem}.part"
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir()
    try:
        packed_video = video
        if shrink and ffmpeg:
            report(0.0, f"Shrinking {video.name}")
            small = shrink_video(ffmpeg, video, work / (video.stem + ".mp4"), cancel)
            if small is not None:
                packed_video = small
        events = recorder.events_path(video)
        doc = stepdoc.load(out_dir) if (out_dir / stepdoc.INDEX_NAME).is_file() else None
        relative = _relative(video, source)
        manifest = {
            "format": FORMAT,
            "app": "ScreenCap Docs",
            "archived": time.strftime("%Y-%m-%d %H:%M:%S"),
            "recording": relative,
            "video": packed_video.name,
            "video_shrunk": packed_video is not video,
            "video_size": video.stat().st_size,
            "video_sha256": sha256(video),
            "output": (_relative(out_dir, output) if out_dir.is_dir() else None),
            "title": (doc or {}).get("document", {}).get("title") or video.stem,
            "steps": len(doc["steps"]) if doc else 0,
            "duration": (doc or {}).get("duration"),
        }
        files = [(packed_video, f"video/{packed_video.name}", zipfile.ZIP_STORED)]
        if events.is_file():
            files.append((events, f"video/{Path(packed_video.name).stem}"
                                  f"{recorder.EVENTS_SUFFIX}", zipfile.ZIP_DEFLATED))
        if out_dir.is_dir():
            for f in sorted(out_dir.rglob("*")):
                if f.is_file():
                    method = (zipfile.ZIP_STORED if f.suffix.lower() in
                              (".png", ".jpg", ".jpeg", ".gif", ".mp4", ".mkv", ".mov",
                               ".zip", ".docx", ".pptx", ".pdf") else zipfile.ZIP_DEFLATED)
                    files.append((f, "output/" + f.relative_to(out_dir).as_posix(), method))
        tmp_zip = work / "archive.zip"
        total = sum(f.stat().st_size for f, _, _ in files) or 1
        done = 0
        with zipfile.ZipFile(tmp_zip, "w") as z:
            z.writestr(MANIFEST, json.dumps(manifest, indent=2), zipfile.ZIP_DEFLATED)
            for f, name, method in files:
                if cancel is not None and cancel.is_set():
                    raise stepdoc.Cancelled()
                z.write(f, name, compress_type=method)
                done += f.stat().st_size
                report(0.5 + 0.4 * done / total, f"Packing {video.name}")
        report(0.9, f"Checking {zip_path.name}")
        with zipfile.ZipFile(tmp_zip) as z:
            bad = z.testzip()
            if bad is not None:
                raise ArchiveError(f"The archive could not be checked ({bad} is damaged); "
                                   "nothing was deleted.")
            if set(z.namelist()) != {MANIFEST} | {name for _, name, _ in files}:
                raise ArchiveError("The archive is incomplete; nothing was deleted.")
        os.replace(tmp_zip, zip_path)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    # Only now remove the originals
    video.unlink()
    if events.is_file():
        events.unlink()
    if out_dir.is_dir():
        shutil.rmtree(out_dir)
    report(1.0, f"Archived {video.name}")
    return zip_path


def _relative(path, base):
    try:
        return Path(path).resolve().relative_to(Path(base).resolve()).as_posix()
    except ValueError:
        return Path(path).name


def read_manifest(zip_path):
    with zipfile.ZipFile(zip_path) as z:
        return json.loads(z.read(MANIFEST).decode("utf-8"))


def list_archives(dest_dir):
    """[(zip path, manifest)] for every archive in dest_dir, newest first.
    Files that are not ScreenCap Docs archives are left out."""
    found = []
    for f in Path(dest_dir).glob("*.zip"):
        try:
            found.append((f, read_manifest(f)))
        except (OSError, KeyError, ValueError, zipfile.BadZipFile):
            continue
    found.sort(key=lambda item: item[1].get("archived", ""), reverse=True)
    return found


def _safe_target(base, name):
    """base/name, refusing names that would land outside base."""
    target = (base / name).resolve()
    if base.resolve() not in target.parents and target != base.resolve():
        raise ArchiveError(f"The archive holds an unsafe path ({name}); nothing was restored.")
    return target


def restore_recording(zip_path, source, output):
    """Unpack an archive back into the recordings and output folders, then
    delete it. Returns (video path, output folder or None)."""
    zip_path, source, output = Path(zip_path), Path(source), Path(output)
    manifest = read_manifest(zip_path)
    if manifest.get("format", 0) > FORMAT:
        raise ArchiveError(f"{zip_path.name} was made by a newer version of ScreenCap Docs.")
    rel = Path(manifest["recording"])
    video_folder = _safe_target(source, rel).parent
    video_name = Path(manifest["video"])
    out_dir = _safe_target(output, manifest["output"]) if manifest.get("output") else None

    def taken(stem):
        # The video and its output folder share a name, so both must be free
        return (any((video_folder / (stem + ext)).exists() for ext in VIDEO_EXTENSIONS)
                or (out_dir is not None and (out_dir.parent / stem).exists()))

    stem, n = rel.stem, 1
    while taken(stem):
        stem = f"{rel.stem} (restored)" + (f" ({n})" if n > 1 else "")
        n += 1
    video = video_folder / (stem + video_name.suffix)
    if out_dir is not None:
        out_dir = out_dir.parent / stem
    with zipfile.ZipFile(zip_path) as z:
        if z.testzip() is not None:
            raise ArchiveError(f"{zip_path.name} is damaged; nothing was restored.")
        names = z.namelist()
        video_folder.mkdir(parents=True, exist_ok=True)
        for name in names:
            if name.endswith("/") or name == MANIFEST:
                continue
            if name.startswith("video/"):
                inner = name[len("video/"):]
                if inner == video_name.name:
                    target = _safe_target(video_folder, video.name)
                elif inner.endswith(recorder.EVENTS_SUFFIX):
                    target = _safe_target(video_folder, recorder.events_path(video).name)
                else:
                    continue
            elif name.startswith("output/") and out_dir is not None:
                target = _safe_target(out_dir, name[len("output/"):])
            else:
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with z.open(name) as src, open(target, "wb") as dst:
                shutil.copyfileobj(src, dst)
    if out_dir is not None and (out_dir / stepdoc.INDEX_NAME).is_file():
        # Point the steps at the restored video (used to open it in VLC)
        doc = stepdoc.load(out_dir)
        doc["source_path"] = str(video.resolve())
        stepdoc.save(out_dir, doc)
    zip_path.unlink()
    return video, out_dir
