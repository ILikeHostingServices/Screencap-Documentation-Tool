#!/usr/bin/env python3
#
# test_recorder.py
# 2026-10-20
# Version: v1.1.1
#
# PURPOSE:
# Tests for the built-in recorder and the use of its clicks: turning mouse
# and key samples into clicks, double-clicks, drags, keys, shortcuts, and
# typing (never the text typed); the FFmpeg command on each system; giving
# each action to the right step; the words of a clicked button; captions
# and click rings; and a real recording of a window that is clicked (X11
# on Linux, the desktop on Windows), processed into captioned steps.
#
# Run from the repository root:
#   python -m unittest discover -s tests -v

import ctypes.util
import os
import shutil
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from helpers import FFMPEG, FFPROBE, fake_click  # noqa: E402

import actions  # noqa: E402
import annotate  # noqa: E402
import recorder  # noqa: E402
import redact  # noqa: E402
import screencap as sc  # noqa: E402
import stepdoc  # noqa: E402
import transcribe  # noqa: E402

try:
    import tkinter as tk
except ImportError:   # Python without Tcl/Tk
    tk = None


class EventLogTests(unittest.TestCase):
    def feed(self, log, samples):
        for t, x, y, buttons, keys in samples:
            log.feed(t, x, y, set(buttons), set(keys))

    def test_clicks_double_clicks_and_drags(self):
        log = recorder.EventLog()
        self.feed(log, [(1.0, 10, 10, [], []), (1.1, 10, 10, ["left"], []),
                        (1.2, 11, 10, [], []),                    # click
                        (1.4, 11, 11, ["left"], []), (1.5, 11, 11, [], []),   # second click
                        (3.0, 50, 50, ["right"], []), (3.1, 50, 50, [], []),
                        (5.0, 100, 100, ["left"], []), (5.2, 300, 120, ["left"], []),
                        (5.3, 300, 120, [], [])])
        events = log.result()
        self.assertEqual([e["type"] for e in events], ["click", "click", "drag"])
        self.assertEqual(events[0]["count"], 2, "two quick clicks are a double-click")
        self.assertEqual((events[1]["button"], events[1]["x"]), ("right", 50))
        self.assertEqual((events[2]["x2"], events[2]["y2"]), (300, 120))
        self.assertNotIn("t_last", events[0])

    def test_keys_are_named_and_typing_is_only_counted(self):
        log = recorder.EventLog()
        seq = [(1.0, "A"), (1.1, "B"), (1.2, "char:59"), (1.3, "1"), (2.0, "Tab"),
               (2.5, "Down"), (2.8, "Down"), (6.0, "Enter")]
        t_prev = 0
        for t, key in seq:
            log.feed(t, 0, 0, set(), {key})
            log.feed(t + 0.05, 0, 0, set(), set())
            t_prev = t
        log.feed(t_prev + 1, 0, 0, set(), {"Ctrl"})
        log.feed(t_prev + 1.1, 0, 0, set(), {"Ctrl", "Shift", "S"})
        log.feed(t_prev + 1.2, 0, 0, set(), {"Shift"})
        log.feed(t_prev + 1.3, 0, 0, set(), {"Shift", "Tab"})
        events = log.result()
        self.assertEqual(events[0], {"t": 1.0, "type": "typing", "count": 4})
        self.assertEqual([(e["type"], e.get("key") or e.get("keys"), e.get("count"))
                          for e in events[1:]],
                         [("key", "Tab", 1), ("key", "Down", 2), ("key", "Enter", 1),
                          ("shortcut", "Ctrl+Shift+S", None), ("key", "Shift+Tab", 1)])
        text = repr(events)
        self.assertNotIn("'A'", text)
        self.assertNotIn("char", text)

    def test_altgr_and_mac_option_characters_are_only_counted(self):
        # AltGr+Q types @ on a German keyboard and arrives as Ctrl+Alt+Q; on a
        # Mac, Option+L types @. Neither may be kept as a "shortcut".
        for log, held in ((recorder.EventLog(option_types=False), {"Ctrl", "Alt"}),
                          (recorder.EventLog(option_types=False), {"Ctrl", "Alt", "Shift"}),
                          (recorder.EventLog(option_types=True), {"Alt"})):
            log.feed(1.0, 0, 0, set(), set(held))
            log.feed(1.1, 0, 0, set(), set(held) | {"Q"})
            log.feed(1.2, 0, 0, set(), set())
            events = log.result()
            self.assertEqual([e["type"] for e in events], ["typing"], held)
            self.assertNotIn("Q", repr(events))
        # Real shortcuts are still named: Ctrl+Alt+Delete, Alt+F on Windows
        log = recorder.EventLog(option_types=False)
        log.feed(1.0, 0, 0, set(), {"Ctrl", "Alt", "Delete"})
        log.feed(1.1, 0, 0, set(), set())
        log.feed(2.0, 0, 0, set(), {"Alt", "F"})
        log.feed(2.1, 0, 0, set(), set())
        self.assertEqual([e.get("keys") for e in log.result()], ["Ctrl+Alt+Delete", "Alt+F"])

    def test_administrator_can_turn_off_noting_keys(self):
        with mock.patch.dict(os.environ, {"SCREENCAP_NO_KEYS": "1"}):
            self.assertTrue(recorder.keys_disabled_by_policy())
            self.assertFalse(recorder.Recorder("ffmpeg", "x.mp4", keys=True).keys)
        with mock.patch.dict(os.environ, {"SCREENCAP_NO_KEYS": ""}):
            self.assertTrue(recorder.Recorder("ffmpeg", "x.mp4", keys=True).keys)

    def test_own_window_clicks_and_times_outside_the_recording_are_dropped(self):
        log = recorder.EventLog()
        log.ignore = [900, 600, 200, 50]
        self.feed(log, [(1.0, 950, 620, ["left"], []), (1.1, 950, 620, [], []),
                        (2.0, 10, 10, ["left"], []), (2.1, 10, 10, [], []),
                        (9.0, 10, 10, ["left"], []), (9.1, 10, 10, [], [])])
        self.assertEqual([e["t"] for e in log.result(offset=1.5, until=8.0)], [0.5])


class CommandTests(unittest.TestCase):
    def test_each_system_records_its_screen_with_wall_clock_times(self):
        enc = ["-c:v", "libx264"]
        with mock.patch.object(recorder, "platform_name", return_value="windows"):
            cmd = recorder.command("ffmpeg", "out.mkv", enc, microphone="Mic (USB)")
        self.assertIn("gdigrab", cmd)
        self.assertIn("audio=Mic (USB)", cmd)
        self.assertEqual(cmd.count("-use_wallclock_as_timestamps"), 2)
        with mock.patch.object(recorder, "platform_name", return_value="macos"):
            cmd = recorder.command("ffmpeg", "out.mkv", enc, microphone="1", screen_index=3)
        self.assertIn("3:1", cmd)
        self.assertIn("0:a:0", cmd)
        with mock.patch.object(recorder, "platform_name", return_value="linux"):
            cmd = recorder.command("ffmpeg", "out.mkv", enc, microphone="pulse:default",
                                   display=":5")
        self.assertEqual(cmd[cmd.index(":5") - 1], "-i")
        self.assertIn("pulse", cmd)
        self.assertEqual(cmd[-1], "out.mkv")

    def test_wayland_is_explained(self):
        with mock.patch.object(recorder, "platform_name", return_value="linux"), \
                mock.patch.dict(os.environ, {"XDG_SESSION_TYPE": "wayland"}):
            self.assertIn("Wayland", recorder.unsupported_reason())

    @unittest.skipUnless(FFMPEG, "FFmpeg is not installed")
    def test_an_encoder_is_always_found(self):
        self.assertIn(recorder.pick_encoder(FFMPEG)[1], ("libx264", "libopenh264", "mpeg4"))


def ocr_line(*words, y=100, h=20):
    """An OCR line: words laid out left to right from x=100."""
    out, x = [], 100
    for w in words:
        width = len(w) * 10
        out.append((w, [x, y, width, h]))
        x += width + 8
    return out


class ActionTests(unittest.TestCase):
    def steps(self):
        return [{"time": 3.0, "still_from": 0.0, "still_to": 3.5, "caption": ""},
                {"time": 7.0, "still_from": 3.8, "still_to": 7.4, "caption": ""},
                {"time": 11.0, "still_from": 7.6, "still_to": 12.0, "caption": "Mine"}]

    def test_actions_go_to_the_screen_they_were_done_on(self):
        steps = self.steps()
        events = [{"t": 3.4, "type": "click"}, {"t": 3.7, "type": "key"},
                  {"t": 5.0, "type": "typing"}, {"t": 30.0, "type": "click"}]
        per = actions.assign(steps, events)
        self.assertEqual([len(per[id(s)]) for s in steps], [2, 1, 1])

    def test_captions(self):
        click = {"type": "click", "button": "left", "count": 1, "x": 0, "y": 0}
        self.assertEqual(actions.caption([dict(click, label="Next")]), 'Click "Next".')
        self.assertEqual(actions.caption([dict(click, count=2, label="Report.docx")]),
                         'Double-click "Report.docx".')
        self.assertEqual(actions.caption([dict(click, near="User name"),
                                          {"type": "typing", "count": 5},
                                          {"type": "key", "key": "Tab", "count": 1}]),
                         'Click next to "User name", type the text, then press Tab.')
        self.assertEqual(actions.caption([{"type": "shortcut", "keys": "Ctrl+S"},
                                          dict(click, button="right")]),
                         "Press Ctrl+S, then right-click the marked spot.")
        many = [dict(click, label=str(n) + "x") for n in range(6)]
        self.assertTrue(actions.caption(many).endswith(", and so on."))
        self.assertEqual(actions.caption([]), "")

    def test_words_under_and_beside_a_click(self):
        lines = [ocr_line("Save", "As...", y=100), ocr_line("User", "name:", y=200),
                 ocr_line("Cancel", y=300)]
        self.assertEqual(actions.click_label(lines, 130, 110, 1280), "Save As")
        self.assertIsNone(actions.click_label(lines, 700, 205, 1280))
        self.assertEqual(actions.nearby_label(lines, 400, 210, 1280), "User name")
        self.assertIsNone(actions.click_label([ocr_line("|", "~", y=100)], 105, 105, 1280))
        # a checkbox clicked on its box: the label is to the right
        self.assertEqual(actions.right_label([ocr_line("Create", "a", "shortcut", y=300)],
                                             80, 308, 1280), "Create a shortcut")
        # words a button-width away belong to the next control, not this one
        self.assertIsNone(actions.right_label([ocr_line("Cancel", y=300)], 10, 308, 1600))
        # button edges read as | do not join two buttons into one label
        buttons = [ocr_line("Back", "|", "Next", y=400)]
        self.assertEqual(actions.click_label(buttons, 170, 405, 1280), "Next")
        # a text cursor read as "I" is not the clicked word; the field label is
        field = [ocr_line("Product", "key:", y=500) + [("I", [380, 498, 6, 18])]]
        self.assertIsNone(actions.click_label(field, 382, 505, 1280))
        self.assertEqual(actions.nearby_label(field, 382, 505, 1280), "Product key")

    def test_light_text_on_a_colored_button_beats_the_next_button(self):
        # "Continue" (white on green) is only read from just the button, and
        # only a moment before the click, when the pointer is not on it yet;
        # "Cancel" to its right must not become the label
        click = {"type": "click", "t": 5.0, "x": 1019, "y": 705}

        def words(ffmpeg, tesseract, video, t, area, tmp, psm=11):
            if psm == 11:
                return [ocr_line("Go", "Back", y=697) + [("Cancel", [1109, 697, 50, 16])]]
            if area[2] > 200:                      # the button-sized area
                return []
            return [] if t == 5.0 else [[("Continue", [985, 697, 70, 16])]]
        with mock.patch.object(actions, "words_at", side_effect=words):
            actions.label_action(click, Path("v.mkv"), "ffmpeg", "tesseract", 1600, 972, (),
                                 Path("."))
        self.assertEqual(click.get("label"), "Continue")

    def test_words_spoiled_by_the_pointer_match_the_clean_reading(self):
        self.assertTrue(actions.same_words("Continue", "Confjpue"))
        self.assertTrue(actions.same_words("Next", "Ne"))
        self.assertTrue(actions.same_words("Done", "ck Done"))
        self.assertFalse(actions.same_words("Cancel", "Continue"))
        self.assertFalse(actions.same_words("Finish", "Back"))

    def test_sensitive_words_never_go_in_a_caption(self):
        self.assertIsNone(actions.safe_label("admin@example.com"))
        self.assertIsNone(actions.safe_label("10.0.0.12"))
        self.assertIsNone(actions.safe_label("Project Falcon", ["falcon"]))
        self.assertEqual(actions.safe_label("Install now"), "Install now")

    def test_apply_marks_clicks_and_keeps_typed_captions(self):
        doc = {"width": 1920, "height": 1080, "steps": self.steps()}
        doc["steps"][0]["annotations"] = [{"kind": "arrow", "from": [1, 1], "to": [9, 9]},
                                          {"kind": "click", "at": [5, 5], "auto": True}]
        events = {"screen": [0, 0, 960, 540], "events": [
            {"t": 3.3, "type": "click", "button": "left", "count": 1, "x": 480, "y": 270},
            {"t": 5.0, "type": "drag", "button": "left", "x": 10, "y": 10, "x2": 100,
             "y2": 50},
            {"t": 8.0, "type": "click", "button": "left", "count": 1, "x": 1, "y": 1}]}
        filled = actions.apply(Path("."), doc, events)
        first, second, third = doc["steps"]
        self.assertEqual(filled, 2)
        self.assertEqual(first["caption"], "Click the marked spot.")
        self.assertTrue(first["caption_auto"])
        self.assertEqual(first["annotations"],
                         [{"kind": "arrow", "from": [1, 1], "to": [9, 9]},
                          {"kind": "click", "at": [960, 540], "auto": True}],
                         "screen points are scaled to recording pixels; old rings replaced")
        self.assertEqual(second["annotations"][0]["kind"], "arrow")
        self.assertEqual(second["annotations"][0]["to"], [200, 100])
        self.assertEqual(third["caption"], "Mine", "a typed caption is kept")
        self.assertEqual(len(third["annotations"]), 1)

        # Narration replaces the draft but not a typed caption
        segs = [{"start": 1.0, "end": 2.0, "text": "Open the installer."},
                {"start": 9.0, "end": 10.0, "text": "Done."}]
        transcribe.apply(doc, segs)
        self.assertEqual(first["caption"], "Open the installer.")
        self.assertNotIn("caption_auto", first)
        self.assertEqual(third["caption"], "Mine")

    def test_click_ring_is_drawn_and_found(self):
        ann = {"kind": "click", "at": [100, 80], "auto": True}
        self.assertTrue(annotate.valid(ann))
        rgba = annotate.draw_rgba(200, 160, [ann])
        r = round(annotate.ring_radius(annotate.sizes(200)))
        self.assertEqual(rgba[(80 * 200 + 100) * 4 + 3], 0, "the middle stays clear")
        self.assertEqual(rgba[(80 * 200 + 100 + r) * 4 + 3], 255, "the ring is solid")
        self.assertIsNotNone(annotate.hit(ann, 101, 81, 200))


# ---------------------------------------------------------------------------
# A real recording
# ---------------------------------------------------------------------------

CAN_RECORD = (tk is not None and FFMPEG and FFPROBE and recorder.unsupported_reason() is None
              and (os.name == "nt" or ctypes.util.find_library("Xtst")))


@unittest.skipUnless(CAN_RECORD, "needs Tkinter, FFmpeg, and a desktop that can be recorded")
class LiveRecordingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="screencap_rec_"))
        self.root = tk.Tk()
        self.root.attributes("-topmost", True)
        self.root.geometry(f"{self.root.winfo_screenwidth()}x"
                           f"{self.root.winfo_screenheight()}+0+0")
        self.root.configure(bg="white")
        self.pages = 0

        def advance():
            self.pages += 1
            color = ("#cfe8ff", "#ffe0b2", "#d7f5d0")[self.pages % 3]
            self.root.configure(bg=color)
            self.title.configure(text=f"Page {self.pages + 1}", bg=color)
        self.title = tk.Label(self.root, text="Page 1", font=("TkDefaultFont", 36), bg="white")
        self.title.place(x=60, y=60)
        self.button = tk.Button(self.root, text="Next", font=("TkDefaultFont", 28),
                                command=advance)
        self.button.place(x=320, y=260, width=220, height=80)
        self.pump(1.0)

    def tearDown(self):
        self.root.destroy()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def pump(self, seconds):
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            self.root.update()
            time.sleep(0.02)

    def test_clicks_are_recorded_and_become_captions(self):
        source = self.tmp / "source"
        rec = recorder.Recorder(FFMPEG, source / recorder.default_name())
        rec.start()
        deadline = time.monotonic() + 20
        while not rec.recording():
            self.assertTrue(rec.running(), rec.error_text())
            self.assertLess(time.monotonic(), deadline, rec.error_text())
            self.pump(0.1)
        self.pump(3.0)
        bx = self.button.winfo_rootx() + self.button.winfo_width() // 2
        by = self.button.winfo_rooty() + self.button.winfo_height() // 2
        for _ in range(2):
            fake_click(bx, by)
            self.pump(3.0)
        video = rec.stop()
        self.assertEqual(self.pages, 2, "the window got the clicks")

        events = recorder.load_events(video)
        clicks = [e for e in events["events"] if e["type"] == "click"]
        self.assertEqual(len(clicks), 2, events)
        self.assertLess(abs(clicks[0]["t"] - 3.0), 1.5, "click times are in the recording")

        out = self.tmp / "out"
        self.assertEqual(sc.main(["-s", str(source), "-o", str(out), "--no-redact"]), 0)
        doc = stepdoc.load(out / video.stem)
        captions = [s["caption"] for s in doc["steps"]]
        rings = [a for s in doc["steps"] for a in s.get("annotations") or []
                 if a["kind"] == "click"]
        self.assertEqual(len(rings), 2, captions)
        kx = doc["width"] / events["screen"][2]
        self.assertLess(abs(rings[0]["at"][0] - (bx - events["screen"][0]) * kx), 8)
        expected = 'Click "Next".' if redact.find_tesseract() else "Click the marked spot."
        self.assertEqual(captions.count(expected), 2, captions)
        md = (out / video.stem / stepdoc.INDEX_NAME).read_text(encoding="utf-8")
        self.assertIn(expected, md)


if __name__ == "__main__":
    unittest.main()
