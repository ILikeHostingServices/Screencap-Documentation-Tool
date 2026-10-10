#!/usr/bin/env python3
#
# test_gui.py
# 2026-10-10
# Version: v1.2.0
#
# PURPOSE:
# Drives the real GUI window: processes a synthetic recording through the
# Videos list, then checks the Steps tab (arrow-key navigation, reordering,
# captions, saving, captions from narration), the version in the title, and
# the Help menu (help, About, links, update check). Skipped when Tkinter or a
# display is not available (on Linux CI it runs under xvfb-run).

import os
import shutil
import tempfile
import time
import unittest
from unittest import mock
from importlib.machinery import SourceFileLoader
from pathlib import Path

from helpers import FFMPEG, FFPROBE, ROOT, fake_whisper, make_video

try:
    import tkinter as tk
    from tkinter import messagebox, simpledialog
except ImportError:   # Python without Tcl/Tk
    tk = None

HAS_DISPLAY = os.name == "nt" or bool(os.environ.get("DISPLAY")) or os.uname().sysname == "Darwin"


@unittest.skipUnless(tk and HAS_DISPLAY and FFMPEG and FFPROBE,
                     "needs Tkinter, a display, and FFmpeg")
class GuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="screencap_gui_"))
        cls.source = cls.tmp / "source"
        cls.source.mkdir()
        make_video(cls.source / "Demo.mp4", audio="tone")
        # The folder is typed through a link, as on Windows where temp paths
        # are short (8.3) names: the GUI must still match up its videos
        cls.typed_source = cls.source
        if os.name != "nt":
            (cls.tmp / "link").symlink_to(cls.tmp, target_is_directory=True)
            cls.typed_source = cls.tmp / "link" / "source"
        # Keep GUI settings and presets out of the real user profile
        cls.saved_env = {k: os.environ.get(k) for k in ("APPDATA", "XDG_CONFIG_HOME",
                                                       "SCREENCAP_NO_UPDATE_CHECK")}
        os.environ["APPDATA"] = os.environ["XDG_CONFIG_HOME"] = str(cls.tmp / "profile")
        # No automatic update check (and no question about it) during tests
        os.environ["SCREENCAP_NO_UPDATE_CHECK"] = "1"
        # Dialogs would block an unattended run: answer them automatically
        cls.saved_dialogs = {}
        cls.dialogs = []      # (dialog, message) shown, to explain failures
        for mod, name, answer in ((messagebox, "askyesno", True),
                                  (messagebox, "askyesnocancel", True),
                                  (messagebox, "showinfo", None),
                                  (messagebox, "showwarning", None),
                                  (messagebox, "showerror", None),
                                  (simpledialog, "askstring", None)):
            cls.saved_dialogs[(mod, name)] = getattr(mod, name)
            setattr(mod, name, lambda *a, _answer=answer, _name=name, **k:
                    (cls.dialogs.append((_name, a[1] if len(a) > 1 else "")), _answer)[1])
        cls.gui = SourceFileLoader("screencap_gui", str(ROOT / "screencap_gui.pyw")).load_module()

    @classmethod
    def tearDownClass(cls):
        for (mod, name), fn in cls.saved_dialogs.items():
            setattr(mod, name, fn)
        for k, v in cls.saved_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def setUp(self):
        self.dialogs.clear()
        self.root = tk.Tk()
        # Bring the window to the front so it gets keyboard events (a CI
        # runner's window can otherwise stay in the background on Windows)
        self.root.attributes("-topmost", True)
        self.root.focus_force()
        self.app = self.gui.App(self.root)
        self.errors = []
        self.root.report_callback_exception = lambda *a: self.errors.append(a)
        self.app.open_path = lambda path: None        # do not launch other programs

    def tearDown(self):
        self.app.editor.dirty = False
        try:
            self.app.on_close()
        except tk.TclError:
            # A test that failed part way can leave Tk half torn down; that
            # must not hide the real failure behind a second error
            try:
                self.root.destroy()
            except tk.TclError:
                pass

    def bring_to_front(self):
        """Windows only lets the foreground app take the keyboard (the
        foreground lock), so on a desktop that someone is using the test
        window may not get focus straight away. Ask a few times."""
        for _ in range(10):
            self.root.lift()
            self.root.focus_force()
            self.pump(0.1)
            if self.root.focus_get() is not None:
                return

    def click(self, widget):
        widget.event_generate("<ButtonPress-1>", x=5, y=5)
        widget.event_generate("<ButtonRelease-1>", x=5, y=5)
        self.pump()

    def pump(self, seconds=0.3):
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            self.root.update()
            time.sleep(0.02)

    def wait_for_worker(self, timeout=180):
        end = time.monotonic() + timeout
        while self.app.worker and self.app.worker.is_alive():
            self.assertLess(time.monotonic(), end, "processing did not finish in time")
            self.pump(0.2)
        self.pump(0.5)

    def process(self, name):
        self.app.v_source.set(str(self.typed_source))
        self.app.v_output.set(str(self.tmp / name))
        self.app.refresh_videos()
        self.app.process_all()
        self.wait_for_worker()
        rows = [self.app.tree.set(i, "status") for i in self.app.tree.get_children()]
        self.assertEqual(rows, ["Done"], f"dialogs shown: {self.dialogs}")
        self.app.tree.selection_set(self.app.tree.get_children()[0])
        self.pump()
        self.app.show_steps()
        self.pump()
        return self.app.editor

    def shown_step(self, editor):
        return editor.current_index()

    def test_footer_and_title_show_release_version(self):
        import version
        self.assertIn(f"v{version.RELEASE}", self.root.title())

    def test_process_and_navigate_steps(self):
        ed = self.process("nav")
        steps = len(ed.doc["steps"])
        self.assertGreaterEqual(steps, 3)
        self.assertEqual(self.shown_step(ed), 0)

        # Clicking the picture takes the keyboard from the Videos list, then
        # Down pages through the steps
        self.app.tree.focus_force()
        self.pump()
        self.bring_to_front()
        self.click(ed.canvas)
        if self.root.focus_get() is not ed.canvas:
            self.bring_to_front()                 # lost the foreground: retry once
            self.click(ed.canvas)
        self.assertIs(self.root.focus_get(), ed.canvas)
        ed.canvas.event_generate("<Down>")
        self.pump()
        self.assertEqual(self.shown_step(ed), 1)

        ed.step_list.focus_set()
        ed.step_list.event_generate("<Down>")         # list keeps in step
        self.pump()
        self.assertEqual(self.shown_step(ed), 2)
        ed.step_list.event_generate("<Up>")
        self.pump()
        self.assertEqual(self.shown_step(ed), 1)

        moved = ed.doc["steps"][1]["time"]
        ed.move(-1)                                   # Move Step Up keeps it selected
        self.pump()
        self.assertEqual(self.shown_step(ed), 0)
        self.assertEqual(ed.doc["steps"][0]["time"], moved)
        self.assertEqual(self.errors, [])

    def test_caption_save_round_trip(self):
        ed = self.process("caption")
        ed.caption.insert("1.0", "Open the installer.")
        ed.caption.event_generate("<<Modified>>")
        self.pump()
        self.assertTrue(ed.dirty)
        self.assertTrue(ed.save(wait=True))
        self.pump()
        md = (self.tmp / "caption" / "Demo" / "steps.md").read_text(encoding="utf-8")
        self.assertIn("Open the installer.", md)
        self.assertEqual(self.errors, [])

    def test_captions_from_narration(self):
        ed = self.process("narration")
        ed.caption.insert("1.0", "Typed by hand.")
        ed.caption.event_generate("<<Modified>>")
        self.pump()
        second = ed.doc["steps"][1]
        start = second["still_from"] if second["still_from"] is not None else second["time"]
        segments = [{"start": 0.2, "end": 0.6, "text": "Spoken on the first screen."},
                    {"start": start + 0.2, "end": start + 0.6, "text": "Spoken on the second."}]
        with fake_whisper(self.tmp, segments):
            ed.captions_from_narration()
            end = time.monotonic() + 120
            while str(ed.btn_narration["state"]) == "disabled" and time.monotonic() < end:
                self.pump(0.2)
        self.pump()
        self.assertEqual(self.dialogs, [], "no error dialog expected")
        self.assertEqual(ed.doc["steps"][0]["caption"], "Typed by hand.")   # kept
        self.assertEqual(ed.doc["steps"][1]["caption"], "Spoken on the second.")
        self.assertTrue(ed.dirty)
        self.assertTrue((self.tmp / "narration" / "Demo" / "transcript.txt").is_file())
        self.assertEqual(self.errors, [])

    def menu_labels(self, menu):
        return [menu.entrycget(i, "label") for i in range(menu.index("end") + 1)
                if menu.type(i) not in ("separator", "tearoff")]

    def test_help_about_and_links(self):
        import updates
        import version
        opened = []
        self.app.open_url = opened.append
        self.assertEqual(self.menu_labels(self.app.menubar)[-1], "Help")
        labels = self.menu_labels(self.app.help_menu)
        for label in ("Help", "Report a Problem...", "Project on GitHub", "Check for Updates...",
                      "Check for Updates Automatically"):
            self.assertIn(label, labels)
        self.app.help_menu.invoke(self.entry_index("Report a Problem..."))
        self.assertEqual(opened, [updates.BUG_REPORT_URL])

        win = self.app.show_help("Presets")
        self.pump()
        self.assertIn("General desktop use", win.text.get("1.0", "end"))
        win.destroy()
        about = self.app.show_about()
        self.pump()
        self.assertIn(f"v{version.RELEASE}", about.details.get("1.0", "end"))
        about.copy()
        self.assertIn(version.RELEASE, self.root.clipboard_get())
        about.destroy()
        self.assertEqual(self.errors, [])

    def entry_index(self, label):
        menu = self.app.help_menu
        return next(i for i in range(menu.index("end") + 1)
                    if menu.type(i) not in ("separator", "tearoff")
                    and menu.entrycget(i, "label") == label)

    def run_update_check(self, latest):
        import updates
        opened = []
        self.app.open_url = opened.append
        with mock.patch.dict(os.environ, {"SCREENCAP_NO_UPDATE_CHECK": ""}), \
                mock.patch.object(updates, "check_latest", return_value=latest):
            self.app.check_for_updates(manual=True)
            end = time.monotonic() + 20
            while self.app.updater.running and time.monotonic() < end:
                self.pump(0.1)
        self.pump()
        return opened

    def test_update_check_offers_a_newer_version(self):
        latest = {"version": "99.0.0", "tag": "v99.0.0", "name": "v99.0.0",
                  "url": "https://example.test/release", "published": "2030-01-01",
                  "notes": "Big update", "assets": {}}
        opened = self.run_update_check(latest)
        self.assertEqual([d for d, _ in self.dialogs], ["askyesnocancel"])
        self.assertIn("99.0.0", self.dialogs[0][1])
        self.assertEqual(opened, ["https://example.test/release"])
        self.assertTrue(self.app.settings_extra.get("last_update_check"))
        self.assertEqual(self.errors, [])

    def test_update_check_when_up_to_date(self):
        import version
        latest = {"version": version.RELEASE, "tag": "v" + version.RELEASE, "name": "",
                  "url": "", "published": "", "notes": "", "assets": {}}
        opened = self.run_update_check(latest)
        self.assertEqual([d for d, _ in self.dialogs], ["showinfo"])
        self.assertIn("latest version", self.dialogs[0][1])
        self.assertEqual(opened, [])


if __name__ == "__main__":
    unittest.main()
