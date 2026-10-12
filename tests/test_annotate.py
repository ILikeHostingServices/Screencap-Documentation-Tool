#!/usr/bin/env python3
#
# test_annotate.py
# 2026-10-12
# Version: v1.0.0
#
# PURPOSE:
# Tests for annotations (arrows, numbered markers, text labels): drawing
# the shapes, escaping for FFmpeg, picking them with the mouse, and
# rendering them into real screenshots, including in a folder whose name
# has characters FFmpeg treats specially.
#
# Run from the repository root:
#   python -m unittest discover -s tests -v

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from helpers import FFMPEG, FFPROBE, make_video  # noqa: E402

import annotate  # noqa: E402
import screencap as sc  # noqa: E402
import stepdoc  # noqa: E402


def pixel(path, x, y):
    """(r, g, b) of one pixel of an image, read with FFmpeg."""
    res = subprocess.run([FFMPEG, "-hide_banner", "-loglevel", "error", "-i", str(path),
                          "-vf", f"crop=1:1:{x}:{y},format=rgb24", "-f", "rawvideo", "-"],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res.returncode != 0 or len(res.stdout) != 3:
        raise RuntimeError(res.stderr.decode(errors="replace"))
    return tuple(res.stdout)


def is_red(rgb):
    r, g, b = rgb
    return r > 180 and g < 110 and b < 110


def has_drawtext():
    res = subprocess.run([FFMPEG, "-hide_banner", "-filters"], stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, errors="replace")
    return " drawtext " in res.stdout


class AnnotationUnitTests(unittest.TestCase):
    def test_shapes_are_drawn_red_with_a_white_edge(self):
        w, h = 400, 300
        rgba = annotate.draw_rgba(w, h, [{"kind": "arrow", "from": [50, 150], "to": [350, 150]},
                                         {"kind": "number", "at": [200, 60], "n": 1}])

        def at(x, y):
            i = (y * w + x) * 4
            return tuple(rgba[i:i + 4])

        self.assertEqual(at(150, 150), (0xE5, 0x39, 0x35, 255))     # on the shaft
        self.assertEqual(at(200, 60), (0xE5, 0x39, 0x35, 255))      # marker center
        self.assertEqual(at(150, 40)[3], 0)                          # empty area
        line = annotate.sizes(w)["line"]
        edge = at(150, 150 - line // 2 - 2)                          # just above the shaft
        self.assertGreater(edge[3], 200)
        self.assertGreater(min(edge[:3]), 200)                       # white
        self.assertEqual(at(349, 150)[3], 255)                       # the tip reaches its point

    def test_tiny_or_broken_annotations_are_ignored(self):
        step = {"annotations": [{"kind": "arrow", "from": [5, 5], "to": [5, 5]},
                                {"kind": "text", "at": [1, 1], "text": "   "},
                                {"kind": "number"}, {"kind": "circle", "at": [1, 1]},
                                {"kind": "number", "at": [9, 9], "n": 4}]}
        self.assertEqual(len(annotate.step_annotations(step)), 2)
        self.assertEqual(annotate.next_number(step), 5)
        self.assertEqual(annotate.next_number({}), 1)
        rgba = annotate.draw_rgba(20, 20, step["annotations"][:1])
        self.assertFalse(any(rgba))

    def test_filter_values_are_escaped(self):
        self.assertEqual(annotate.filter_value("a:b"), "a\\\\:b")
        self.assertEqual(annotate.filter_value("x,y;[z]"), "x\\,y\\;\\[z\\]")
        self.assertEqual(annotate.filter_path(r"C:\Fonts\a.ttf"), "C\\\\:/Fonts/a.ttf")

    def test_hit_finds_the_nearest_annotation(self):
        arrow = {"kind": "arrow", "from": [0, 0], "to": [100, 0]}
        label = {"kind": "text", "at": [300, 300], "text": "Hello"}
        self.assertIsNotNone(annotate.hit(arrow, 50, 3, 1280))
        self.assertIsNone(annotate.hit(arrow, 50, 200, 1280))
        self.assertEqual(annotate.hit(label, 305, 305, 1280), 0)

    def test_no_font_gives_a_clear_error(self):
        step = {"annotations": [{"kind": "text", "at": [1, 1], "text": "Hi"}]}
        saved = annotate._font_cache.copy()
        try:
            annotate._font_cache["font"] = None
            with self.assertRaises(RuntimeError) as cm:
                annotate.filters(step, 1280, 720, tempfile.gettempdir())
            self.assertIn("SCREENCAP_FONT", str(cm.exception))
        finally:
            annotate._font_cache.clear()
            annotate._font_cache.update(saved)


@unittest.skipUnless(FFMPEG and FFPROBE, "FFmpeg is not installed")
class AnnotationRenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # FFmpeg filter syntax gives ' , [ ] ; and % a meaning; the paths must
        # be escaped for them (":" too, but Windows does not allow it in names)
        cls.tmp = Path(tempfile.mkdtemp(prefix="screencap_annotate_")) / "Bob's [test], 100%; ok"
        cls.source = cls.tmp / "source"
        cls.source.mkdir(parents=True)
        make_video(cls.source / "Demo.mp4")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp.parent, ignore_errors=True)

    def process(self, name):
        out = self.tmp / name
        self.assertEqual(sc.main(["-s", str(self.source), "-o", str(out), "--no-redact",
                                  "--no-highlight"]), 0)
        return out / "Demo"

    def test_arrows_and_markers_are_rendered_and_removable(self):
        out = self.process("shapes")
        doc = stepdoc.load(out)
        step = doc["steps"][0]
        step["annotations"] = [{"kind": "arrow", "from": [100, 600], "to": [500, 600]},
                               {"kind": "number", "at": [1000, 100], "n": 1}]
        stepdoc.render(out, doc, FFMPEG)
        shot, original = out / step["file"], out / step["original"]
        self.assertTrue(is_red(pixel(shot, 300, 600)))
        self.assertFalse(is_red(pixel(original, 300, 600)), "the original is never changed")
        self.assertEqual(len(list((out / annotate.OVERLAY_DIR).glob("*.pam"))), 1)
        self.assertEqual(stepdoc.load(out)["steps"][0]["annotations"], step["annotations"])

        step["annotations"] = []
        stepdoc.render(out, doc, FFMPEG)
        self.assertEqual(shot.read_bytes(), original.read_bytes())
        self.assertFalse((out / annotate.OVERLAY_DIR).exists(), "unused images are removed")

    def test_annotations_follow_the_crop(self):
        out = self.process("crop")
        doc = stepdoc.load(out)
        step = doc["steps"][0]
        step["crop"] = [200, 400, 640, 300]
        step["annotations"] = [{"kind": "arrow", "from": [250, 500], "to": [700, 500]}]
        stepdoc.render(out, doc, FFMPEG)
        self.assertTrue(is_red(pixel(out / step["file"], 300, 100)))   # 500 - 400

    @unittest.skipUnless(annotate.find_font(), "no font for annotation text")
    def test_labels_and_numbers_are_drawn(self):
        if not has_drawtext():
            self.skipTest("this FFmpeg has no drawtext filter")
        out = self.process("text")
        doc = stepdoc.load(out)
        step = doc["steps"][0]
        step["annotations"] = [{"kind": "text", "at": [100, 100],
                                "text": "Click Next: it's 50% [done], ok; \\ go"},
                               {"kind": "number", "at": [600, 100], "n": 12}]
        stepdoc.render(out, doc, FFMPEG)
        self.assertTrue(is_red(pixel(out / step["file"], 104, 104)))   # label background


if __name__ == "__main__":
    unittest.main()
