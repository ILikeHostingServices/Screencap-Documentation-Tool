#!/usr/bin/env python3
#
# gui_recorder.py
# 2026-11-11
# Version: v1.4.0
#
# PURPOSE:
# The GUI side of the built-in recorder (recorder.py): the Record window
# with the recording options, and the small Recording window with the
# timer, Stop, and Discard that stays on top while the screen is recorded.
# The main window is minimized during the recording. When the recording is
# stopped it is saved in the Recordings folder, selected in the list, and
# (if chosen) processed straight away.
#
# What to record: the whole screen, one window (picked by clicking it), or
# an area drawn with the mouse (AreaPicker, a see-through layer over the
# screen; on Linux a still picture of the screen, since a see-through window
# needs a compositing desktop there).

import os
import tempfile
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

import recorder
import version
from i18n import N_, _

NO_MIC = N_("No microphone")   # saved as is; shown translated
KEYS_KEY, PROCESS_KEY, MIC_KEY = "record_keys", "record_process", "record_microphone"
MODE_KEY, SOUND_KEY = "record_mode", "record_system_sound"
SETTINGS_KEYS = (KEYS_KEY, PROCESS_KEY, MIC_KEY, MODE_KEY, SOUND_KEY)
MODES = [("screen", N_("Whole screen")), ("window", N_("One window (click it after Start)")),
         ("area", N_("An area (draw it after Start)"))]
START_DELAY_MS = 600     # lets the main window finish minimizing first
DOT_ON, DOT_OFF = "#E53935", "#F8A5A3"   # the blinking red dot


def platform_note():
    plat = recorder.platform_name()
    if plat == "macos":
        return _("macOS asks for permission the first time: allow this app (or Terminal) "
                "under System Settings > Privacy & Security > Screen Recording, and "
                "Input Monitoring for keys. Whole screen is the main display.")
    if plat == "windows":
        return _("Whole screen is all monitors. The small Recording window is left out of "
                "the recording.")
    return _("Whole screen is the whole X11 screen. The small Recording window shows in "
            "the recording when it is inside the recorded area; it sits in the "
            "bottom-right corner.")


def modes():
    """The choices of what to record on this system (macOS cannot pick a
    window, only draw an area)."""
    shown = [(key, _(label)) for key, label in MODES]
    if recorder.platform_name() == "macos":
        return [m for m in shown if m[0] != "window"]
    return shown


def system_sound_help():
    """What to set up when no source of the computer's sound is found."""
    plat = recorder.platform_name()
    if plat == "windows":
        return _("To record the computer's sound, switch on \"Stereo Mix\" (Sound settings > "
                "More sound settings > Recording, right-click > Show Disabled Devices) "
                "or install a virtual audio cable, then open this window again.")
    if plat == "macos":
        return _("To record the computer's sound, install a loopback driver such as "
                "BlackHole and send the sound to it, then open this window again.")
    return _("To record the computer's sound, FFmpeg needs PulseAudio or PipeWire "
            "(pulse) support.")


class RecordDialog(tk.Toplevel):
    """Recording options. Calls on_start(microphone, keys, process, mode,
    system_audio)."""

    def __init__(self, app, on_start):
        super().__init__(app.root)
        self.app, self.on_start = app, on_start
        self.title(_("Record Screen"))
        self.resizable(False, False)
        self.transient(app.root)
        extra = app.settings_extra
        body = ttk.Frame(self, padding=(22, 18))
        body.pack(fill="both", expand=True)
        body.columnconfigure(1, weight=1)
        ttk.Label(body, text=_("Record Screen"), style="Heading.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w")
        ttk.Label(body, text=_("Do the task as usual. Each click is noted, so the steps get a "
                             "red ring where you clicked and a first-draft caption such as "
                             "Click \"Next\". Stop when you are done."),
                  style="Muted.TLabel", wraplength=460, justify="left").grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(2, 14))

        ttk.Label(body, text=_("Record")).grid(row=2, column=0, sticky="w", padx=(0, 10))
        self.modes = modes()
        labels = dict(self.modes)
        self.v_mode = tk.StringVar(value=labels.get(extra.get(MODE_KEY), labels["screen"]))
        ttk.Combobox(body, textvariable=self.v_mode, state="readonly", width=38,
                     values=[m[1] for m in self.modes]).grid(row=2, column=1, sticky="ew",
                                                             pady=(0, 10))
        body_rows = ttk.Frame(body)
        body_rows.grid(row=3, column=0, columnspan=2, sticky="ew")
        body_rows.columnconfigure(1, weight=1)
        self._fill_sound(body_rows, extra, app)

        self.keys_policy = recorder.keys_disabled_by_policy()
        self.v_keys = tk.BooleanVar(value=False if self.keys_policy else extra.get(KEYS_KEY, True))
        keys_text = _("Note keys pressed (Enter, Tab, shortcuts such as Ctrl+S). "
                     "Typed text is never saved.")
        if self.keys_policy:
            keys_text = _("Noting keys pressed is switched off by your administrator.")
        ttk.Checkbutton(body, text=keys_text, variable=self.v_keys,
                        state="disabled" if self.keys_policy else "normal").grid(
            row=5, column=0, columnspan=2, sticky="w", pady=(6, 0))
        self.v_process = tk.BooleanVar(value=extra.get(PROCESS_KEY, True))
        ttk.Checkbutton(body, text=_("Make the screenshots when I stop"),
                        variable=self.v_process).grid(row=6, column=0, columnspan=2,
                                                      sticky="w", pady=(4, 0))
        ttk.Label(body, text=platform_note(), style="Muted.TLabel", wraplength=460,
                  justify="left").grid(row=7, column=0, columnspan=2, sticky="w", pady=(12, 0))

        btns = ttk.Frame(body)
        btns.grid(row=8, column=0, columnspan=2, sticky="e", pady=(16, 0))
        ttk.Button(btns, text=_("Cancel"), command=self.destroy).pack(side="right")
        start = ttk.Button(btns, text=_("Start Recording"), style="Accent.TButton",
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

    def _fill_sound(self, frame, extra, app):
        """The Microphone and computer sound rows."""
        ttk.Label(frame, text=_("Microphone")).grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.mics = [(_(NO_MIC), None)]
        try:
            self.mics += recorder.list_microphones(app.ffmpeg)
        except OSError:
            pass
        self.v_mic = tk.StringVar(value=extra.get(MIC_KEY) if extra.get(MIC_KEY) in
                                  [m[0] for m in self.mics] else _(NO_MIC))
        ttk.Combobox(frame, textvariable=self.v_mic, state="readonly", width=38,
                     values=[m[0] for m in self.mics]).grid(row=0, column=1, sticky="ew")
        ttk.Label(frame, text=_("Talk through the steps to turn your words into captions later "
                              "(Captions From Narration in the Steps tab)."),
                  style="Muted.TLabel", wraplength=460, justify="left").grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(2, 8))
        try:
            self.system = recorder.list_system_audio(app.ffmpeg)
        except OSError:
            self.system = []
        self.v_system = tk.BooleanVar(value=bool(self.system) and extra.get(SOUND_KEY, False))
        ttk.Checkbutton(frame, text=_("Also record the computer's sound (videos, alerts)"),
                        variable=self.v_system,
                        state="normal" if self.system else "disabled").grid(
            row=2, column=0, columnspan=2, sticky="w")
        if not self.system:
            ttk.Label(frame, text=system_sound_help(), style="Muted.TLabel", wraplength=460,
                      justify="left").grid(row=3, column=0, columnspan=2, sticky="w",
                                           pady=(2, 0))

    def start(self):
        label = self.v_mic.get()
        mic = dict(self.mics).get(label)
        mode = {v: k for k, v in self.modes}.get(self.v_mode.get(), "screen")
        system = self.system[0][1] if self.system and self.v_system.get() else None
        extra = self.app.settings_extra
        extra[MIC_KEY] = label
        extra[MODE_KEY] = mode
        if self.system:
            extra[SOUND_KEY] = bool(self.v_system.get())
        if not self.keys_policy:      # keep the user's own choice for later
            extra[KEYS_KEY] = bool(self.v_keys.get())
        extra[PROCESS_KEY] = bool(self.v_process.get())
        self.app.save_settings()
        self.destroy()
        self.on_start(mic, bool(self.v_keys.get()), bool(self.v_process.get()), mode, system)


class AreaPicker(tk.Toplevel):
    """A layer over the whole screen to pick what to record: drag a
    rectangle (mode "area") or click a window (mode "window"). Calls
    on_done(rect) with [x, y, width, height] in screen coordinates, or
    on_done(None) when cancelled (Esc or right-click)."""

    def __init__(self, root, mode, on_done, ffmpeg=None):
        super().__init__(root)
        self.mode, self.on_done = mode, on_done
        self.start_pt = None
        self.rect_id = None
        self.shot = None
        full = recorder.screen_rect() or [0, 0, root.winfo_screenwidth(),
                                          root.winfo_screenheight()]
        self.origin = full[:2]
        self.overrideredirect(True)
        self.geometry(f"{full[2]}x{full[3]}{full[0]:+d}{full[1]:+d}")
        self.attributes("-topmost", True)
        self.canvas = tk.Canvas(self, highlightthickness=0, cursor="crosshair", bg="#202020")
        self.canvas.pack(fill="both", expand=True)
        if recorder.platform_name() == "linux":
            self.shot = self._screenshot(ffmpeg, full)
        if self.shot is not None:
            self.canvas.create_image(0, 0, image=self.shot, anchor="nw")
            self.canvas.create_rectangle(0, 0, full[2], full[3], fill="#000000",
                                         stipple="gray25", outline="")
        else:
            try:
                self.attributes("-alpha", 0.35)
            except tk.TclError:
                pass
        hint = (_("Drag over the area to record. Esc cancels.") if mode == "area" else
                _("Click the window to record. Esc cancels."))
        self.canvas.create_text(full[2] // 2, 60, text=hint, fill="white",
                                font=("TkDefaultFont", 20, "bold"))
        self.canvas.bind("<ButtonPress-1>", self._press)
        self.canvas.bind("<B1-Motion>", self._drag)
        self.canvas.bind("<ButtonRelease-1>", self._release)
        self.canvas.bind("<ButtonPress-3>", lambda e: self._finish(None))
        self.bind("<Escape>", lambda e: self._finish(None))
        self.lift()
        self.focus_force()
        self.after(100, self._grab)

    def _grab(self):
        try:
            self.grab_set()
            self.focus_force()
        except tk.TclError:
            pass

    @staticmethod
    def _screenshot(ffmpeg, full):
        """A still picture of the X11 screen, or None."""
        if not ffmpeg:
            return None
        path = Path(tempfile.gettempdir()) / f"screencap_pick_{os.getpid()}.png"
        try:
            recorder._run([ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-f", "x11grab",
                           "-video_size", f"{full[2]}x{full[3]}", "-i",
                           os.environ.get("DISPLAY", ":0"), "-frames:v", "1", str(path)])
            return tk.PhotoImage(file=str(path)) if path.is_file() else None
        except (OSError, tk.TclError):
            return None
        finally:
            try:
                path.unlink()
            except OSError:
                pass

    def _press(self, event):
        self.start_pt = (event.x, event.y)
        if self.mode == "window":
            x, y = event.x_root, event.y_root
            self.withdraw()     # the window under the point, not this layer
            self.after(200, lambda: self._finish(recorder.window_at(x, y), window=True))

    def _drag(self, event):
        if self.mode != "area" or self.start_pt is None:
            return
        if self.rect_id is not None:
            self.canvas.delete(self.rect_id)
        x0, y0 = self.start_pt
        self.rect_id = self.canvas.create_rectangle(x0, y0, event.x, event.y,
                                                    outline="#E53935", width=3)

    def _release(self, event):
        if self.mode != "area" or self.start_pt is None:
            return
        x0, y0 = self.start_pt
        x1, y1 = event.x, event.y
        w, h = abs(x1 - x0), abs(y1 - y0)
        if w < recorder.MIN_AREA or h < recorder.MIN_AREA:     # a click: try again
            self.start_pt = None
            return
        ox, oy = self.origin
        self._finish([min(x0, x1) + ox, min(y0, y1) + oy, w, h])

    def _finish(self, rect, window=False):
        if window and rect is None:
            messagebox.showinfo(version.APP_NAME, _("That window could not be found. Choose "
                                "Whole screen or An area instead."), parent=self.master)
        try:
            self.grab_release()
            self.destroy()
        except tk.TclError:
            pass
        self.on_done(rect)


class RecordingBar(tk.Toplevel):
    """The small window shown while recording: a timer, Stop, and Discard."""

    def __init__(self, root, on_stop, on_discard):
        super().__init__(root)
        self.title(_("Recording"))
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.protocol("WM_DELETE_WINDOW", on_stop)
        frame = ttk.Frame(self, padding=(12, 8))
        frame.pack(fill="both", expand=True)
        self.dot = ttk.Label(frame, text="\u25cf", foreground=DOT_ON, font=("TkDefaultFont", 14))
        self.dot.pack(side="left")
        self.v_text = tk.StringVar(value=_("Starting..."))
        ttk.Label(frame, textvariable=self.v_text, width=20).pack(side="left", padx=(6, 10))
        self.btn_stop = ttk.Button(frame, text=_("Stop"), style="Accent.TButton", command=on_stop)
        self.btn_stop.pack(side="left")
        self.btn_discard = ttk.Button(frame, text=_("Discard"), command=on_discard)
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
        self.v_text.set(_("Recording {time}").format(time=f"{m:02d}:{s:02d}"))
        self.dot.configure(foreground=DOT_ON if int(seconds * 2) % 2 == 0 else DOT_OFF)

    def set_paused(self):
        """Windows is showing an administrator prompt or the lock screen,
        which cannot be recorded; recording carries on when it closes."""
        self.v_text.set(_("Paused (admin prompt)"))
        self.dot.configure(foreground=DOT_OFF)

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

    def begin(self, microphone, keys, process, mode="screen", system_audio=None):
        app = self.app
        source = Path(app.v_source.get()).expanduser()
        try:
            source.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            messagebox.showerror(version.APP_NAME, _("The Recordings folder cannot be used: "
                                                     "{error}").format(error=exc),
                                 parent=app.root)
            return
        self.process = process
        options = dict(microphone=microphone, keys=keys, system_audio=system_audio, mode=mode)
        app.recording = self
        app.root.iconify()
        if mode == "screen":
            self._create(source, options, None)
            return

        def picked(rect):
            if rect is None:        # cancelled
                app.recording = None
                app.root.deiconify()
                return
            self._create(source, options, rect)
        app.root.after(START_DELAY_MS, lambda: AreaPicker(app.root, mode, picked, app.ffmpeg))

    def _create(self, source, options, area):
        app = self.app
        self.rec = recorder.Recorder(app.ffmpeg, source / recorder.default_name(),
                                     log=app.log, area=area, **options)
        self.bar = RecordingBar(app.root, self.stop, self.discard)
        recorder.hide_from_capture(self.bar.winfo_id())
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
        try:
            state = rec.keep_going()
        except recorder.RecorderError as exc:
            self._fail(str(exc))
            return
        if state == "paused":
            self.bar.set_paused()
        elif rec.recording():
            self.bar.set_time(rec.elapsed())
        elif time.monotonic() - self.started > 20:
            rec.cancel()
            self._fail(_("FFmpeg did not start recording. It said:") + "\n"
                       + rec.error_text())
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
        self.bar.busy(_("Saving..."))
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
            messagebox.showerror(version.APP_NAME, _("The recording could not be saved.") + "\n\n" +
                                 result["error"], parent=self.app.root)
            return
        self.app.on_recorded(result["path"], self.process)
        pauses = getattr(self.rec, "pauses", 0)
        if pauses:
            self.app.log.warning("The recording paused %d time(s) while Windows showed an "
                                 "administrator prompt or the lock screen, which cannot be "
                                 "recorded. The rest was joined into one video.", pauses)

    def discard(self):
        if self.done or self.rec is None:
            return
        self.done = True
        self._cancel_job()
        self.bar.busy(_("Discarding..."))
        self.bar.update_idletasks()
        self.rec.cancel()
        self._close()
        self.app.set_status(_("Recording discarded."))

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
        messagebox.showerror(version.APP_NAME, _("Recording did not work.") + "\n\n" + text,
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
