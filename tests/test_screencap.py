#!/usr/bin/env python3
#
# test_screencap.py
# 2026-10-02
# Version: v1.6.0
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

import export  # noqa: E402
import imaging  # noqa: E402
import player  # noqa: E402
import redact  # noqa: E402
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


class PlayerTests(unittest.TestCase):
    def test_start_time_shows_the_lead_up(self):
        self.assertEqual(player.start_time({"time": 7.75, "still_from": 4.0}), 1.0)
        self.assertEqual(player.start_time({"time": 1.0, "still_from": 0.0}), 0.0)
        self.assertEqual(player.start_time({"time": 9.0, "still_from": None}), 6.0)

    def test_vlc_command(self):
        cmd = player.vlc_command("vlc", Path("Demo.mp4"), 12.5)
        self.assertEqual(cmd, ["vlc", "--no-one-instance", "--start-time=12.50", "Demo.mp4"])


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
        self.assertEqual(Path(doc["source_path"]), (self.source / "Demo.mp4").resolve())
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

    def test_crop_applies_to_screenshots_not_originals(self):
        out = self.process("crop", "--crop", "250:150:701:401")
        doc = stepdoc.load(out)
        self.assertEqual(doc["crop"], [250, 150, 700, 400])   # even-sized
        step = doc["steps"][1]
        self.assertEqual(imaging.image_size(FFMPEG, out / step["file"]), (700, 400))
        self.assertEqual(imaging.image_size(FFMPEG, out / step["original"]), (1280, 720))

        step["crop"] = stepdoc.NO_CROP                 # this step uncropped
        doc["steps"][0]["crop"] = [0, 0, 320, 180]     # this step its own crop
        stepdoc.render(out, doc, FFMPEG)
        self.assertEqual(imaging.image_size(FFMPEG, out / step["file"]), (1280, 720))
        self.assertEqual(imaging.image_size(FFMPEG, out / doc["steps"][0]["file"]), (320, 180))

    def test_clamp_rect(self):
        self.assertEqual(stepdoc.clamp_rect([1200, 700, 500, 500], 1280, 720),
                         [1200, 700, 80, 20])
        self.assertEqual(stepdoc.clamp_rect([100, 100, -50, -40], 1280, 720),
                         [50, 60, 50, 40])

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


# The dialog opens (3 s), closes (6 s), and opens again (9 s); a small
# checkbox is ticked at 12 s and the mouse cursor moves the whole time.
REVISIT_FILTER = ("drawbox=x=300:y=200:w=600:h=300:color=gray:t=fill:"
                  "enable='between(t,3,6)+gte(t,9)',"
                  "drawbox=x=320:y=230:w=14:h=14:color=black:t=fill:enable='gte(t,12)',"
                  "drawbox=x='100+t*40':y=600:w=12:h=18:color=black:t=fill")


@unittest.skipUnless(FFMPEG and FFPROBE, "FFmpeg is not installed")
class DuplicateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="screencap_dedup_"))
        cls.source = cls.tmp / "source"
        cls.source.mkdir()
        make_video(cls.source / "Revisit.mp4", REVISIT_FILTER, duration=15)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_revisited_screen_is_removed_and_restorable(self):
        out = self.tmp / "dedup"
        self.assertEqual(sc.main(["-s", str(self.source), "-o", str(out)]), 0)
        doc = stepdoc.load(out / "Revisit")
        self.assertEqual(len(doc["deleted_steps"]), 1)
        dup = doc["deleted_steps"][0]
        self.assertEqual(dup["deleted_reason"], "duplicate")
        self.assertTrue((out / "Revisit" / dup["original"]).is_file())
        kept = len(doc["steps"])
        stepdoc.restore_deleted(doc)
        self.assertEqual(len(doc["steps"]), kept + 1)

    def test_small_change_is_not_a_duplicate(self):
        a = imaging.thumbnail(FFMPEG, self.frame(10.5))
        b = imaging.thumbnail(FFMPEG, self.frame(13.5))   # only the checkbox differs
        c = imaging.thumbnail(FFMPEG, self.frame(11.0))   # only the cursor moved
        self.assertIsNone(imaging.find_duplicate(b, [a], 0.01))
        self.assertEqual(imaging.find_duplicate(c, [a], 0.01), 0)

    def test_no_dedup_keeps_everything(self):
        out = self.tmp / "nodedup"
        self.assertEqual(sc.main(["-s", str(self.source), "-o", str(out), "--no-dedup"]), 0)
        self.assertEqual(stepdoc.load(out / "Revisit")["deleted_steps"], [])

    def test_highlight_box_surrounds_the_checkbox(self):
        prev = imaging.thumbnail(FFMPEG, self.frame(10.5), imaging.CHANGE_SIZE)
        cur = imaging.thumbnail(FFMPEG, self.frame(13.5), imaging.CHANGE_SIZE)
        x, y, w, h = imaging.change_box(prev, cur, 1280, 720)
        # checkbox drawn at 320,230 size 14x14; box must contain it and stay small
        self.assertLessEqual(x, 320)
        self.assertLessEqual(y, 230)
        self.assertGreaterEqual(x + w, 334)
        self.assertGreaterEqual(y + h, 244)
        self.assertLess(w * h, 60 * 60)

    def test_cursor_only_change_gets_no_box(self):
        prev = imaging.thumbnail(FFMPEG, self.frame(1.0), imaging.CHANGE_SIZE)
        cur = imaging.thumbnail(FFMPEG, self.frame(2.0), imaging.CHANGE_SIZE)
        box = imaging.change_box(prev, cur, 1280, 720)
        if box is not None:   # a cursor-sized box is acceptable, never a big one
            self.assertLess(box[2] * box[3], 60 * 60)

    def test_highlight_rendered_and_switchable(self):
        out = self.tmp / "hl"
        self.assertEqual(sc.main(["-s", str(self.source), "-o", str(out), "--no-dedup"]), 0)
        folder = out / "Revisit"
        doc = stepdoc.load(folder)
        boxed = [s for s in doc["steps"] if s.get("change_box")]
        self.assertTrue(boxed)
        step = boxed[0]
        self.assertNotEqual((folder / step["file"]).read_bytes(),
                            (folder / step["original"]).read_bytes())
        step["highlight"] = False
        stepdoc.render(folder, doc, FFMPEG)
        self.assertEqual((folder / step["file"]).read_bytes(),
                         (folder / step["original"]).read_bytes())

    def test_no_highlight_option(self):
        out = self.tmp / "nohl"
        self.assertEqual(sc.main(["-s", str(self.source), "-o", str(out), "--no-highlight"]), 0)
        doc = stepdoc.load(out / "Revisit")
        self.assertFalse(doc["highlight"])
        for step in doc["steps"]:
            self.assertEqual((out / "Revisit" / step["file"]).read_bytes(),
                             (out / "Revisit" / step["original"]).read_bytes())

    def frame(self, t):
        dest = self.tmp / f"frame_{t}.png"
        sc.run([FFMPEG, "-loglevel", "error", "-y", "-ss", str(t), "-i",
                str(self.source / "Revisit.mp4"), "-frames:v", "1", str(dest)])
        return dest


TESSERACT = redact.find_tesseract()


def font_file():
    for path in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                 "C:/Windows/Fonts/arial.ttf", "/Library/Fonts/Arial.ttf",
                 "/System/Library/Fonts/Supplemental/Arial.ttf"):
        if Path(path).is_file():
            return path
    return None


FONT = font_file()


def text_filter(lines, start=0):
    font = FONT.replace(":", "\\:")
    parts = []
    for i, text in enumerate(lines):
        parts.append(f"drawtext=fontfile='{font}':text='{text}':x=100:y={160 + 60 * i}:"
                     f"fontsize=24:fontcolor=black:enable='gte(t,{start})'")
    return ",".join(parts)


@unittest.skipUnless(FFMPEG and FFPROBE and TESSERACT and FONT,
                     "needs FFmpeg, Tesseract OCR, and a TrueType font")
class RedactionTests(unittest.TestCase):
    SECRET_LINES = ["Server IP\\: 192.168.10.25", "Password\\: Hunter2Secret!",
                    "Product key\\: ABCDE-12345-FGHIJ-67890-KLMNO",
                    "Contact admin@example.com", "Click Next to continue"]

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="screencap_redact_"))
        cls.source = cls.tmp / "source"
        cls.source.mkdir()
        make_video(cls.source / "Login.mp4", text_filter(cls.SECRET_LINES, start=4), duration=10)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_detects_secrets_but_not_ordinary_text(self):
        image = self.tmp / "frame.png"
        sc.run([FFMPEG, "-loglevel", "error", "-y", "-ss", "8", "-i",
                str(self.source / "Login.mp4"), "-frames:v", "1", str(image)])
        found = redact.scan_image(TESSERACT, image, 1280, 720)
        reasons = " ".join(r["reason"] for r in found)
        for expected in ("IP address", "Password", "license key", "email address"):
            self.assertIn(expected, reasons)
        # "Click Next to continue" (y = 400) must not be blurred
        self.assertFalse([r for r in found if r["box"][1] > 390])

    def test_custom_pattern(self):
        lines = [[("Join", [0, 0, 40, 20]), ("CORP-DOMAIN", [50, 0, 120, 20])]]
        self.assertFalse(redact.find_sensitive(lines, 1280, 720))
        self.assertTrue(redact.find_sensitive(lines, 1280, 720, ["corp-domain"]))

    def test_two_copies_and_switches(self):
        out = self.tmp / "out"
        self.assertEqual(sc.main(["-s", str(self.source), "-o", str(out)]), 0)
        folder = out / "Login"
        doc = stepdoc.load(folder)
        step = doc["steps"][-1]
        self.assertTrue(stepdoc.redaction_boxes(step, doc))
        blurred = folder / step["file"]
        plain = folder / stepdoc.UNREDACTED_DIR / step["file"]
        self.assertTrue(plain.is_file())
        self.assertNotEqual(blurred.read_bytes(), plain.read_bytes())
        self.assertIn("UNREDACTED COPY",
                      (folder / stepdoc.UNREDACTED_INDEX).read_text(encoding="utf-8"))

        for r in step["auto_redactions"]:      # un-blur everything detected
            r["ignored"] = True
        step["manual_redactions"] = [[100, 100, 200, 40]]
        stepdoc.render(folder, doc, FFMPEG, tesseract=TESSERACT)
        self.assertEqual(stepdoc.redaction_boxes(step, doc), [[100, 100, 200, 40]])

        doc["redact"] = False                  # redaction off: no second copy
        stepdoc.render(folder, doc, FFMPEG, tesseract=TESSERACT)
        self.assertFalse((folder / stepdoc.UNREDACTED_INDEX).exists())
        self.assertFalse(list((folder / stepdoc.UNREDACTED_DIR).glob("step_*"))
                         if (folder / stepdoc.UNREDACTED_DIR).exists() else [])

    def test_exports(self):
        out = self.tmp / "export"
        self.assertEqual(sc.main(["-s", str(self.source), "-o", str(out), "--export", "html",
                                  "--doc-author", "MVTS IT", "--doc-version", "v2.0.0"]), 0)
        folder = out / "Login"
        page = (folder / "export" / "Login.html").read_text(encoding="utf-8")
        self.assertIn("MVTS IT", page)
        self.assertIn("v2.0.0", page)
        doc = stepdoc.load(folder)
        self.assertEqual(page.count("data:image/png;base64,"), len(doc["steps"]))
        self.assertNotIn("UNREDACTED", page)

        doc["steps"][0]["caption"] = "Type <b>nothing</b> & wait"
        unredacted = export.export(folder, doc, "html", unredacted=True)
        self.assertIn("-UNREDACTED", unredacted.name)
        text = unredacted.read_text(encoding="utf-8")
        self.assertIn("UNREDACTED COPY", text)
        self.assertIn("Type &lt;b&gt;nothing&lt;/b&gt; &amp; wait", text)

        if export.find_pandoc():
            docx = export.export(folder, doc, "docx")
            self.assertGreater(docx.stat().st_size, 1000)
        browser = export.find_browser() or next(
            (p for p in ("/opt/pw-browsers/chromium",) if Path(p).is_file()), None)
        if browser:
            pdf = export.export(folder, doc, "pdf", browser=browser)
            self.assertTrue(pdf.read_bytes().startswith(b"%PDF"))

    def test_no_redact_option(self):
        out = self.tmp / "noredact"
        self.assertEqual(sc.main(["-s", str(self.source), "-o", str(out), "--no-redact"]), 0)
        self.assertFalse((out / "Login" / stepdoc.UNREDACTED_DIR).exists())


if __name__ == "__main__":
    unittest.main()
