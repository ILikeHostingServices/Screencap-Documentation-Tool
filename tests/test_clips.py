#!/usr/bin/env python3
#
# test_clips.py
# 2026-10-12
# Version: v1.0.0
#
# PURPOSE:
# Tests for animated GIF clips of single steps: which part of the
# recording a clip shows, making it (cropped and blurred like the
# screenshots), using it in steps.md and exports, keeping it when steps
# are reordered, removing it when switched off, and what happens when the
# recording is missing.
#
# Run from the repository root:
#   python -m unittest discover -s tests -v

import shutil
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

from helpers import FFMPEG, FFPROBE, make_video  # noqa: E402

import clips  # noqa: E402
import export  # noqa: E402
import screencap as sc  # noqa: E402
import stepdoc  # noqa: E402


def gif_info(path):
    """(width, height, frames) of a GIF."""
    res = subprocess.run([FFPROBE, "-v", "error", "-count_frames", "-select_streams", "v:0",
                          "-show_entries", "stream=width,height,nb_read_frames",
                          "-of", "csv=p=0", str(path)], stdout=subprocess.PIPE, text=True)
    w, h, n = res.stdout.strip().split(",")[:3]
    return int(w), int(h), int(n)


class ClipRangeTests(unittest.TestCase):
    def doc(self):
        steps = [{"time": 3.75, "still_from": 0.0}, {"time": 7.75, "still_from": 4.0},
                 {"time": 11.75, "still_from": 8.0}]
        return {"duration": 18.0, "steps": steps,
                "deleted_steps": [{"time": 15.75, "still_from": 13.0}]}

    def test_clip_runs_from_the_finished_screen_into_the_next(self):
        doc = self.doc()
        self.assertEqual(clips.clip_range(doc["steps"][0], doc), (2.25, 4.6))
        # a deleted step still marks where the screen changed
        self.assertEqual(clips.clip_range(doc["steps"][2], doc), (10.25, 13.6))

    def test_clip_length_is_limited(self):
        doc = self.doc()
        doc["steps"][1]["still_from"] = 7.7
        doc["steps"].insert(2, {"time": 7.8, "still_from": 30.0})
        start, end = clips.clip_range(doc["steps"][1], doc)
        self.assertGreaterEqual(end - start, clips.MIN_LENGTH)
        doc["steps"][2]["still_from"] = 7.9
        doc["duration"] = 18.0
        last = {"time": 17.9, "still_from": 17.0}
        doc["steps"].append(last)
        start, end = clips.clip_range(last, doc)
        self.assertLessEqual(end, 18.0)
        self.assertLessEqual(end - start, clips.MAX_LENGTH)

    def test_clip_is_blurred_cropped_and_scaled(self):
        vf = clips.gif_filter(1920, [100, 100, 800, 600],
                              stepdoc.blur_graph([[10, 10, 50, 20]]))
        self.assertLess(vf.index("boxblur"), vf.index("crop=800:600:100:100"))
        self.assertIn("scale=800:-2", vf)
        self.assertIn("scale=960:-2", clips.gif_filter(1920, None, ""))


@unittest.skipUnless(FFMPEG and FFPROBE, "FFmpeg is not installed")
class ClipRenderTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="screencap_clips_"))
        source = self.tmp / "source"
        source.mkdir()
        make_video(source / "Demo.mp4")
        self.assertEqual(sc.main(["-s", str(source), "-o", str(self.tmp / "out"),
                                  "--no-redact"]), 0)
        self.folder = self.tmp / "out" / "Demo"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_clip_is_made_used_kept_and_removed(self):
        doc = stepdoc.load(self.folder)
        step = doc["steps"][2]
        step["clip"] = True
        step["manual_redactions"] = [[320, 300, 200, 30]]
        step["redact"] = True
        stepdoc.render(self.folder, doc, FFMPEG)
        clip = clips.clip_path(self.folder, step)
        self.assertIsNotNone(clip)
        width, height, frames = gif_info(clip)
        self.assertEqual((width, height), (960, 540))
        start, end = clips.clip_range(step, doc)
        self.assertAlmostEqual(frames, (end - start) * clips.FPS, delta=3)
        md = (self.folder / stepdoc.INDEX_NAME).read_text(encoding="utf-8")
        self.assertIn(f"![Animated clip of step 3]({step['clip_file']})", md)
        page = export.build_html(self.folder, doc)
        self.assertEqual(page.count("data:image/gif;base64,"), 1)
        if export.find_pandoc():
            docx = export.export(self.folder, doc, "docx")
            with zipfile.ZipFile(docx) as z:
                self.assertTrue(any(n.endswith(".gif") for n in z.namelist()))

        made = clip.stat().st_mtime_ns          # reordering does not make it again
        stepdoc.move_step(doc, 2, -1)
        stepdoc.render(self.folder, doc, FFMPEG)
        self.assertEqual(clips.clip_path(self.folder, step).stat().st_mtime_ns, made)

        step["clip"] = False                    # switched off: removed
        stepdoc.render(self.folder, doc, FFMPEG)
        self.assertFalse((self.folder / clips.CLIP_DIR).exists())
        self.assertNotIn("Animated clip",
                         (self.folder / stepdoc.INDEX_NAME).read_text(encoding="utf-8"))

    def test_missing_recording_keeps_existing_clip_and_saves_the_rest(self):
        doc = stepdoc.load(self.folder)
        doc["steps"][0]["clip"] = True
        stepdoc.render(self.folder, doc, FFMPEG)
        self.assertIsNotNone(clips.clip_path(self.folder, doc["steps"][0]))
        Path(doc["source_path"]).rename(self.tmp / "moved.mp4")
        doc["steps"][1]["clip"] = True
        doc["steps"][1]["caption"] = "still saved"
        with self.assertLogs("screencap", level="WARNING") as logs:
            stepdoc.render(self.folder, doc, FFMPEG)
        self.assertIn("recording was not found", "\n".join(logs.output))
        self.assertIsNotNone(clips.clip_path(self.folder, doc["steps"][0]))
        self.assertIsNone(clips.clip_path(self.folder, doc["steps"][1]))
        self.assertIn("still saved", (self.folder / stepdoc.INDEX_NAME).read_text(
            encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
