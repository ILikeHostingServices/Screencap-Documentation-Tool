#!/usr/bin/env python3
#
# test_archive.py
# 2026-11-04
# Version: v1.0.1
#
# PURPOSE:
# Tests for archive.py: archiving a processed recording packs the video,
# its click log, and its output folder into one checked .zip and removes
# the originals; restoring puts everything back where it was. Skipped
# automatically when FFmpeg is not installed.
#
# Run from the repository root:
#   python -m unittest discover -s tests -v

import json
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

from helpers import DEMO_FILTER, FFMPEG, make_video  # noqa: E402

import archive  # noqa: E402
import recorder  # noqa: E402
import screencap as sc  # noqa: E402
import stepdoc  # noqa: E402


@unittest.skipUnless(FFMPEG, "FFmpeg is not installed")
class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="screencap_archive_"))
        self.source = self.tmp / "Recordings"
        self.output = self.tmp / "Output"
        (self.source / "team").mkdir(parents=True)
        self.video = self.source / "team" / "Demo.mkv"
        # At high quality, as the built-in recorder saves (so shrinking helps)
        res = sc.run([FFMPEG, "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi",
                      "-i", "color=white:s=1280x720:r=30:d=18", "-vf", DEMO_FILTER + ",noise=alls=6",
                      "-c:v", "libx264", "-qp", "0", "-pix_fmt", "yuv420p", str(self.video)])
        self.assertEqual(res.returncode, 0, res.stderr)
        recorder.events_path(self.video).write_text(json.dumps({"events": []}))
        self.assertEqual(sc.main(["-s", str(self.source), "-o", str(self.output), "-r"]), 0)
        self.out_dir = sc.output_dir_for(self.video, self.source, self.output, [self.video])
        doc = stepdoc.load(self.out_dir)
        doc["steps"][0]["caption"] = "Open the installer."
        stepdoc.save(self.out_dir, doc)
        self.steps = len(doc["steps"])
        self.files = sorted(p.relative_to(self.out_dir).as_posix()
                            for p in self.out_dir.rglob("*") if p.is_file())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def archive(self, **kw):
        return archive.archive_recording(self.video, self.out_dir, self.source, self.output,
                                         ffmpeg=FFMPEG, **kw)

    def test_archive_packs_everything_and_removes_the_originals(self):
        size = self.video.stat().st_size
        zip_path = self.archive()
        self.assertEqual(zip_path, self.output / "Archived recordings" / "Demo.zip")
        self.assertFalse(self.video.exists())
        self.assertFalse(recorder.events_path(self.video).exists())
        self.assertFalse(self.out_dir.exists())
        with zipfile.ZipFile(zip_path) as z:
            self.assertIsNone(z.testzip())
            names = set(z.namelist())
            manifest = json.loads(z.read("archive.json"))
            self.assertTrue(manifest["video_shrunk"])
            self.assertLess(z.getinfo(f"video/{manifest['video']}").file_size, size)
        self.assertIn("video/Demo.events.json", names)
        for f in self.files:
            self.assertIn(f"output/{f}", names)
        self.assertEqual(manifest["recording"], "team/Demo.mkv")
        self.assertEqual(manifest["steps"], self.steps)
        self.assertEqual([m["title"] for _, m in archive.list_archives(zip_path.parent)],
                         ["Demo"])

    def test_restore_puts_everything_back(self):
        zip_path = self.archive(shrink=False)
        video, out_dir = archive.restore_recording(zip_path, self.source, self.output)
        # Resolved: Windows can name the temp folder in short (8.3) form
        self.assertEqual(video.resolve(), self.video.resolve())
        self.assertEqual(out_dir.resolve(), self.out_dir.resolve())
        self.assertFalse(zip_path.exists())
        self.assertTrue(recorder.events_path(video).is_file())
        self.assertEqual(sorted(p.relative_to(out_dir).as_posix()
                                for p in out_dir.rglob("*") if p.is_file()), self.files)
        doc = stepdoc.load(out_dir)
        self.assertEqual(doc["steps"][0]["caption"], "Open the installer.")
        self.assertEqual(Path(doc["source_path"]), video.resolve())

    def test_restore_never_overwrites(self):
        zip_path = self.archive()
        make_video(self.video, duration=6)            # a new recording with the same name
        video, out_dir = archive.restore_recording(zip_path, self.source, self.output)
        self.assertEqual(video.name, "Demo (restored).mp4")   # shrunk to MP4
        self.assertTrue(self.video.is_file())

    def test_unsafe_names_are_refused(self):
        zip_path = self.archive()
        with zipfile.ZipFile(zip_path, "a") as z:
            z.writestr("output/../../evil.txt", "x")
        with self.assertRaises(archive.ArchiveError):
            archive.restore_recording(zip_path, self.source, self.output)
        self.assertFalse((self.tmp / "evil.txt").exists())

    def test_missing_video_is_an_error(self):
        self.video.unlink()
        with self.assertRaises(archive.ArchiveError):
            self.archive()
        self.assertTrue(self.out_dir.is_dir(), "nothing is deleted when archiving fails")


if __name__ == "__main__":
    unittest.main()
