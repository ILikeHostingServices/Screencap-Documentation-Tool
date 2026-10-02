#!/usr/bin/env python3
#
# test_screencap.py
# 2026-10-02
# Version: v1.0.0
#
# PURPOSE:
# End-to-end tests for the detection engine and step document. Each run
# builds a short synthetic "installer" recording with FFmpeg, processes it,
# and checks the real output files. Skipped automatically when FFmpeg is
# not installed.
#
# Run from the repository root:
#   python -m unittest discover -s tests -v

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import screencap as sc  # noqa: E402
import stepdoc  # noqa: E402

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


@unittest.skipUnless(FFMPEG and FFPROBE, "FFmpeg is not installed")
class EngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="screencap_test_"))
        cls.source = cls.tmp / "source"
        cls.source.mkdir()
        make_video(cls.source / "Demo.mp4")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def process(self, name, *extra):
        out = self.tmp / name
        rc = sc.main(["-s", str(self.source), "-o", str(out), *extra])
        self.assertEqual(rc, 0)
        return out / "Demo"

    def test_process_keeps_originals_and_renders_steps(self):
        out = self.process("basic")
        doc = stepdoc.load(out)
        self.assertEqual(doc["schema"], stepdoc.SCHEMA)
        self.assertGreaterEqual(len(doc["steps"]), 3)
        for step in doc["steps"]:
            self.assertTrue((out / step["original"]).is_file(), step["original"])
            self.assertTrue((out / step["file"]).is_file(), step["file"])
        md = (out / "steps.md").read_text(encoding="utf-8")
        self.assertIn("## Step 1", md)

    def test_edit_round_trip(self):
        out = self.process("edit")
        doc = stepdoc.load(out)
        first_time = doc["steps"][0]["time"]
        doc["steps"][0]["caption"] = "Open the installer."
        stepdoc.move_step(doc, 0, 1)
        removed = stepdoc.delete_step(doc, len(doc["steps"]) - 1)
        stepdoc.render(out, doc, FFMPEG)

        doc = stepdoc.load(out)
        self.assertEqual(doc["steps"][1]["time"], first_time)
        self.assertEqual(doc["steps"][1]["caption"], "Open the installer.")
        self.assertEqual(len(doc["deleted_steps"]), 1)
        self.assertTrue((out / removed["original"]).is_file(), "deleted step keeps its original")
        rendered = sorted(p.name for p in out.glob("step_*"))
        self.assertEqual(rendered, sorted(s["file"] for s in doc["steps"]))
        self.assertIn("Open the installer.", (out / "steps.md").read_text(encoding="utf-8"))

        stepdoc.restore_deleted(doc)
        self.assertEqual(doc["steps"][-1]["time"], removed["time"])
        self.assertEqual(doc["deleted_steps"], [])

    def test_hand_edited_markdown_is_backed_up(self):
        out = self.process("handedit")
        md = out / "steps.md"
        md.write_text(md.read_text(encoding="utf-8") + "\nMy own notes\n", encoding="utf-8")
        doc = stepdoc.load(out)
        stepdoc.save(out, doc)
        backups = list(out.glob("steps.hand-edited-*.md"))
        self.assertEqual(len(backups), 1)
        self.assertIn("My own notes", backups[0].read_text(encoding="utf-8"))

    def test_force_moves_previous_output_to_backup(self):
        out = self.process("force")
        doc = stepdoc.load(out)
        doc["steps"][0]["caption"] = "keep me"
        stepdoc.save(out, doc)
        self.process("force", "--force")
        backups = list(out.glob("previous-*"))
        self.assertEqual(len(backups), 1)
        old = json.loads((backups[0] / "steps.json").read_text(encoding="utf-8"))
        self.assertEqual(old["steps"][0]["caption"], "keep me")

    def test_migrates_v1_output(self):
        out = self.tmp / "v1" / "Demo"
        out.mkdir(parents=True)
        shutil.copy(self.process("v1src").parent / "Demo" / "originals" /
                    stepdoc.load(self.tmp / "v1src" / "Demo")["steps"][0]["original"].split("/")[1],
                    out / "step_001_00-00-03.750.png")
        (out / "steps.md").write_text("# old\n\nnotes I wrote\n", encoding="utf-8")
        (out / "steps.json").write_text(json.dumps({
            "tool_version": "1.1.0", "source_video": "Demo.mp4", "duration": 18,
            "settings": {"format": "png"},
            "steps": [{"time": 3.75, "file": "step_001_00-00-03.750.png", "still_from": 0,
                       "still_to": 4, "score": None, "reason": "start"}]}), encoding="utf-8")
        doc = stepdoc.load(out)
        self.assertEqual(doc["schema"], stepdoc.SCHEMA)
        self.assertTrue((out / doc["steps"][0]["original"]).is_file())
        self.assertEqual(len(list(out.glob("steps.pre-upgrade-*.md"))), 1)


if __name__ == "__main__":
    unittest.main()
