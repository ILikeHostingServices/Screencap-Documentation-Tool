#!/usr/bin/env python3
#
# gui_recorder.py
# 2026-10-16
# Version: v1.1.0
#
# PURPOSE:
# The GUI side of the built-in recorder (recorder.py): the Record window
# with the recording options, and the small Recording window with the
# timer, Stop, and Discard that stays on top while the screen is recorded.
# The main window is minimized during the recording. When the recording is
# stopped it is saved in the Recordings folder, selected in the list, and
# (if chosen) processed straight away.

import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

import recorder
import version

NO_MIC = "No microphone"
KEYS_KEY, PROCESS_KEY, MIC_KEY = "record_keys", "record_process", "record_microphone"
START_DELAY_MS = 600     # lets the main window finish minimizing first
DOT_ON, DOT_OFF = "#E53935", "#F8A5A3"   # the blinking red dot


def platform_note():
    plat = recorder.platform_name()
    if plat == "macos":
        return ("macOS asks for permission the first time: allow this app (or Terminal) "
                "under System Settings > Privacy & Security > Screen Recording, and "
                "Input Monitoring for keys. The main display is recorded.")
    if plat == "windows":
        return ("All monitors are recorded. The small Recording window is left out of "
                "the recording.")
    return ("The whole X11 screen is recorded. The small Recording window shows in "
            "the recording; it sits in the bottom-right corner.")


class RecordDialog(tk.Toplevel):
    """Recording options. Calls on_start(microphone, keys, process)."""

    def __init__(self, app, on_start):
        super().__init__(app.root)
        self.app, self.on_start = app, on_start
        self.title("Record Screen")
        self.resizable(False, False)
        self.transient(app.root)
        extra = app.settings_extra
        body = ttk.Frame(self, padding=(22, 18))
        body.pack(fill="both", expand=True)
        body.columnconfigure(1, weight=1)
        ttk.Label(body, text="Record Screen", style="Heading.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w")
        ttk.Label(body, text="Do the task as usual. Each click is noted, so the steps get a "
                             "red ring where you clicked and a first-draft caption such as "
                             "Click \"Next\". Stop when you are done.",
                  style="Muted.TLabel", wraplength=460, justify="left").grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(2, 14))

        ttk.Label(body, text="Microphone").grid(row=2, column=0, sticky="w", padx=(0, 10))
        self.mics = [(NO_MIC, None)]
        try:
            self.mics += recorder.list_microphones(app.ffmpeg)
        except OSError:
            pass
        self.v_mic = tk.StringVar(value=extra.get(MIC_KEY) if extra.get(MIC_KEY) in
                                  [m[0] for m in self.mics] else NO_MIC)
        ttk.Combobox(body, textvariable=self.v_mic, state="readonly", width=38,
                     values=[m[0] for m in self.mics]).grid(row=2, column=1, sticky="ew")
        ttk.Label(body, text="Talk through the steps to turn your words into captions later "
                             "(Captions From Narration in the Steps tab).",
                  style="Muted.TLabel", wraplength=460, justify="left").grid(
            row=3, column=0, columnspan=2, sticky="w", pady=(2, 10))

        self.keys_policy = recorder.keys_disabled_by_policy()
        self.v_keys = tk.BooleanVar(value=False if self.keys_policy else extra.get(KEYS_KEY, True))
        keys_text = ("Note keys pressed (Enter, Tab, shortcuts such as Ctrl+S). "
                     "Typed text is never saved.")
        if self.keys_policy:
            keys_text = "Noting keys pressed is switched off by your administrator."
        ttk.Checkbutton(body, text=keys_text, variable=self.v_keys,
                        state="disabled" if self.keys_policy else "normal").grid(
            row=4, column=0, columnspan=2, sticky="w")
        self.v_process = tk.BooleanVar(value=extra.get(PROCESS_KEY, True))
        ttk.Checkbutton(body, text="Make the screenshots when I stop",
                        variable=self.v_process).grid(row=5, column=0, columnspan=2,
                                                      sticky="w", pady=(4, 0))
        ttk.Label(body, text=platform_note(), style="Muted.TLabel", wraplength=460,
                  justify="left").grid(row=6, column=0, columnspan=2, sticky="w", pady=(12, 0))

        btns = ttk.Frame(body)
        btns.grid(row=7, column=0, columnspan=2, sticky="e", pady=(16, 0))
        ttk.Button(btns, text="Cancel", command=self.destroy).pack(side="right")
        start = ttk.Button(btns, text="Start Recording", style="Accent.TButton",
                           command=self.start)
        start.pack(side="right", padx=(0, 8))
        self.bind("<Return>", lambda e: self.start())
        self.bind("<Escape>", lambda e: self.destroy())
        start.focus_set()
        self.update_idletasks()     # centered over the main window
        root = app.root
        x = root.winfo_rootx() + (root.winfo_width() - self.winfo_reqwidth()) // 2
        y = root.winfo_rooty() + (root.winfo_height() - self.winfo_reqheight()) // 3
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")

    def start(self):
        label = self.v_mic.get()
        mic = dict(self.mics).get(label)
        extra = self.app.settings_extra
        extra[MIC_KEY] = label
        if not self.keys_policy:      # keep the user's own choice for later
            extra[KEYS_KEY] = bool(self.v_keys.get())
        extra[PROCESS_KEY] = bool(self.v_process.get())
        self.app.save_settings()
        self.destroy()
        self.on_start(mic, bool(self.v_keys.get()), bool(self.v_process.get()))


class RecordingBar(tk.Toplevel):
    """The small window shown while recording: a timer, Stop, and Discard."""

    def __init__(self, root, on_stop, on_discard):
        super().__init__(root)
        self.title("Recording")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.protocol("WM_DELETE_WINDOW", on_stop)
        frame = ttk.Frame(self, padding=(12, 8))
        frame.pack(fill="both", expand=True)
        self.dot = ttk.Label(frame, text="\u25cf", foreground=DOT_ON, font=("TkDefaultFont", 14))
        self.dot.pack(side="left")
        self.v_text = tk.StringVar(value="Starting...")
        ttk.Label(frame, textvariable=self.v_text, width=16).pack(side="left", padx=(6, 10))
        self.btn_stop = ttk.Button(frame, text="Stop", style="Accent.TButton", command=on_stop)
        self.btn_stop.pack(side="left")
        self.btn_discard = ttk.Button(frame, text="Discard", command=on_discard)
        self.btn_discard.pack(side="left", padx=(6, 0))
        self.update_idletasks()
        w, h = self.winfo_reqwidth(), self.winfo_reqheight()
        x = self.winfo_screenwidth() - w - 24
        y = self.winfo_screenheight() - h - 72      # above a bottom taskbar
        self.geometry(f"+{x}+{y}")

    def rect(self):
        self.update_idletasks()
        return [self.winfo_rootx(), self.winfo_rooty(), self.winfo_width(),
                self.winfo_height()]

    def set_time(self, seconds):
        m, s = divmod(int(seconds), 60)
        self.v_text.set(f"Recording {m:02d}:{s:02d}")
        self.dot.configure(foreground=DOT_ON if int(seconds * 2) % 2 == 0 else DOT_OFF)

    def busy(self, text):
        self.v_text.set(text)
        self.btn_stop.configure(state="disabled")
        self.btn_discard.configure(state="disabled")


class RecordingSession:
    """One recording, from the Record window to the saved file."""

    def __init__(self, app):
        self.app = app
        self.rec = None
        self.bar = None
        self.job = None
        self.process = True
        self.done = False

    def open(self):
        reason = recorder.unsupported_reason()
        if reason:
            messagebox.showinfo(version.APP_NAME, reason, parent=self.app.root)
            return False
        if not self.app.ffmpeg:
            self.app.check_ffmpeg()
            return False
        RecordDialog(self.app, self.begin)
        return True

    def begin(self, microphone, keys, process):
        app = self.app
        source = Path(app.v_source.get()).expanduser()
        try:
            source.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            messagebox.showerror(version.APP_NAME, f"The Recordings folder cannot be used: "
                                 f"{exc}", parent=app.root)
            return
        self.process = process
        self.rec = recorder.Recorder(app.ffmpeg, source / recorder.default_name(),
                                     microphone=microphone, keys=keys, log=app.log)
        self.bar = RecordingBar(app.root, self.stop, self.discard)
        recorder.hide_from_capture(self.bar.winfo_id())
        app.recording = self
        app.root.iconify()
        self.job = app.root.after(START_DELAY_MS, self._start)

    def _start(self):
        try:
            self.rec.start()
            self.rec.set_ignore_window(self.bar.winfo_id(), self.bar.rect())
        except (recorder.RecorderError, OSError) as exc:
            self._fail(str(exc))
            return
        self.started = time.monotonic()
        self.job = self.app.root.after(200, self._tick)

    def _tick(self):
        rec = self.rec
        if not rec.running():
            self._fail("The recording stopped by itself. FFmpeg said:\n" + rec.error_text())
            return
        if rec.recording():
            self.bar.set_time(rec.elapsed())
        elif time.monotonic() - self.started > 20:
            rec.cancel()
            self._fail("FFmpeg did not start recording. It said:\n" + rec.error_text())
            return
        self.job = self.app.root.after(250, self._tick)

    def _cancel_job(self):
        if self.job:
            try:
                self.app.root.after_cancel(self.job)
            except tk.TclError:
                pass
            self.job = None

    def stop(self):
        if self.done or self.rec is None:
            return
        self.done = True
        self._cancel_job()
        self.bar.busy("Saving...")
        result = {}

        def work():
            try:
                result["path"] = self.rec.stop()
            except (recorder.RecorderError, OSError) as exc:
                result["error"] = str(exc)
        worker = threading.Thread(target=work, daemon=True)
        worker.start()
        self._wait(worker, result)

    def _wait(self, worker, result):
        if worker.is_alive():
            self.job = self.app.root.after(100, lambda: self._wait(worker, result))
            return
        self._close()
        if "error" in result:
            self.app.log.error("Recording failed: %s", result["error"])
            messagebox.showerror(version.APP_NAME, "The recording could not be saved.\n\n" +
                                 result["error"], parent=self.app.root)
            return
        self.app.on_recorded(result["path"], self.process)

    def discard(self):
        if self.done or self.rec is None:
            return
        self.done = True
        self._cancel_job()
        self.bar.busy("Discarding...")
        self.bar.update_idletasks()
        self.rec.cancel()
        self._close()
        self.app.set_status("Recording discarded.")

    def cancel_quietly(self):
        """The app is closing: stop and keep what was recorded so far."""
        if not self.done and self.rec is not None:
            self.done = True
            self._cancel_job()
            try:
                self.rec.stop()
            except (recorder.RecorderError, OSError):
                pass

    def _fail(self, text):
        self.done = True
        self._cancel_job()
        if self.rec is not None and self.rec.running():
            self.rec.cancel()
        self._close()
        self.app.log.error("Recording failed: %s", text)
        messagebox.showerror(version.APP_NAME, "Recording did not work.\n\n" + text,
                             parent=self.app.root)

    def _close(self):
        if self.bar is not None:
            try:
                self.bar.destroy()
            except tk.TclError:
                pass
            self.bar = None
        self.app.recording = None
        try:
            self.app.root.deiconify()
            self.app.root.lift()
        except tk.TclError:
            pass
