#!/usr/bin/env python3
#
# screencap_gui.pyw
# 2026-10-02
# Version: v1.5.0
#
# PURPOSE:
# Desktop GUI for screencap.py. Pick source/output folders, tune detection
# settings, process recordings with live progress, then review and edit the
# captured steps in the Steps tab (see gui_editor.py).
#
# Requires: Python 3.8+ with Tkinter (included with the python.org / winget
# Windows installer) and FFmpeg. The .pyw extension runs without a console
# window when double-clicked on Windows.

import json
import logging
import os
import queue
import shutil
import subprocess
import sys
import tempfile
import threading
import traceback
from pathlib import Path

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

sys.path.insert(0, str(Path(__file__).resolve().parent))
import screencap as sc  # noqa: E402
from gui_editor import StepEditor  # noqa: E402

APP_NAME = "Screencap Documentation Tool"
GUI_VERSION = "1.5.0"
ASSETS_DIR = Path(__file__).resolve().parent / "assets"
# Unique taskbar identity so Windows shows this app's icon instead of grouping
# the window under the generic Python (pythonw.exe) icon
APP_USER_MODEL_ID = "MVTS.ScreencapDocumentationTool.GUI"
BUILD_DATE = "2026-10-02"

SENSITIVITY_PRESETS = {
    "High (more shots)": 0.002,
    "Normal (recommended)": 0.005,
    "Low (fewer shots)": 0.015,
    "Custom": None,
}
CAPTURE_POINTS = {
    "Finished state (before next change)": "end",
    "Right after each change": "start",
}

# Settings live in the user profile, not the repo, because they contain
# local folder paths (which can include the Windows user name).
if os.name == "nt":
    SETTINGS_DIR = Path(os.environ.get("APPDATA", Path.home())) / "ScreencapDocTool"
else:
    SETTINGS_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) \
        / "screencap-doc-tool"
SETTINGS_FILE = SETTINGS_DIR / "gui_settings.json"


def open_path(path):
    """Open a file or folder with the system default application."""
    path = str(path)
    if os.name == "nt":
        os.startfile(path)  # noqa: S606 (local path chosen by the user)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])


class QueueLogHandler(logging.Handler):
    """Forward screencap log records to the GUI thread."""

    def __init__(self, q):
        super().__init__(logging.INFO)
        self.q = q
        self.setFormatter(logging.Formatter("%(message)s"))

    def emit(self, record):
        self.q.put(("log", self.format(record), record.levelno))


class App:
    name = APP_NAME
    is_windows = os.name == "nt"

    def __init__(self, root):
        self.root = root
        self.q = queue.Queue()
        self.worker = None
        self.cancel = threading.Event()
        self.videos = {}          # tree iid -> (video Path, output dir Path)
        self.editor_iid = None    # video currently open in the Steps tab
        self.temp_dir = Path(tempfile.mkdtemp(prefix="screencap_preview_"))
        self.ffmpeg = sc.find_tool("ffmpeg")
        self.ffprobe = sc.find_tool("ffprobe")
        self.defaults = sc.parse_args([])

        root.title(f"{APP_NAME} v{GUI_VERSION}")
        root.geometry("1440x880")
        root.minsize(1180, 720)
        root.protocol("WM_DELETE_WINDOW", self.on_close)
        root.report_callback_exception = self.on_ui_error

        self.log_handler = QueueLogHandler(self.q)
        sc.log.addHandler(self.log_handler)
        sc.log.setLevel(logging.DEBUG)

        self.build_vars()
        self.build_ui()
        self.load_settings()
        self.refresh_videos()
        self.check_ffmpeg()
        self.root.after(100, self.poll_queue)

    # ------------------------------------------------------------------ UI

    def build_vars(self):
        d = self.defaults
        self.v_source = tk.StringVar(value=str(d.source))
        self.v_output = tk.StringVar(value=str(d.output))
        self.v_recursive = tk.BooleanVar(value=False)
        self.v_preset = tk.StringVar(value="Normal (recommended)")
        self.v_threshold = tk.StringVar(value=str(d.threshold))
        self.v_capture = tk.StringVar(value=list(CAPTURE_POINTS)[0])
        self.v_debounce = tk.StringVar(value=str(d.debounce))
        self.v_min_gap = tk.StringVar(value=str(d.min_gap))
        self.v_max_wait = tk.StringVar(value=str(d.max_wait))
        self.v_lead = tk.StringVar(value=str(d.lead))
        self.v_settle = tk.StringVar(value=str(d.settle))
        self.v_fps = tk.StringVar(value=str(d.analyze_fps))
        self.v_width = tk.StringVar(value=str(d.analyze_width))
        self.v_format = tk.StringVar(value=d.format)
        self.v_dedup = tk.BooleanVar(value=not d.no_dedup)
        self.v_dedup_thr = tk.StringVar(value=str(d.dedup_threshold))
        self.v_highlight = tk.BooleanVar(value=not d.no_highlight)
        self.v_force = tk.BooleanVar(value=False)
        self.v_dry = tk.BooleanVar(value=False)
        self.v_status = tk.StringVar(value="Ready")

    def build_ui(self):
        pad = {"padx": 6, "pady": 4}
        main = ttk.Frame(self.root, padding=8)
        main.pack(fill="both", expand=True)
        # Left column takes the width its controls need; preview gets the rest
        main.columnconfigure(0, weight=0)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(1, weight=1)

        # Folders
        folders = ttk.LabelFrame(main, text="Folders", padding=6)
        folders.grid(row=0, column=0, columnspan=2, sticky="ew")
        folders.columnconfigure(1, weight=1)
        for row, (label, var) in enumerate((("Source videos:", self.v_source),
                                            ("Screenshot output:", self.v_output))):
            ttk.Label(folders, text=label).grid(row=row, column=0, sticky="w", **pad)
            ttk.Entry(folders, textvariable=var).grid(row=row, column=1, sticky="ew", **pad)
            ttk.Button(folders, text="Browse...",
                       command=lambda v=var: self.browse(v)).grid(row=row, column=2, **pad)
            ttk.Button(folders, text="Open",
                       command=lambda v=var: self.open_folder(v)).grid(row=row, column=3, **pad)
        ttk.Checkbutton(folders, text="Include subfolders", variable=self.v_recursive,
                        command=self.refresh_videos).grid(row=0, column=4, sticky="w", **pad)

        # Left column: videos + settings
        left = ttk.Frame(main)
        left.grid(row=1, column=0, sticky="nsew", pady=(8, 0))
        left.columnconfigure(0, weight=1)
        left.rowconfigure(0, weight=1)

        vids = ttk.LabelFrame(left, text="Videos", padding=6)
        vids.grid(row=0, column=0, sticky="nsew")
        vids.columnconfigure(0, weight=1)
        vids.rowconfigure(0, weight=1)
        self.tree = ttk.Treeview(vids, columns=("status", "steps"), selectmode="extended")
        self.tree.heading("#0", text="Video")
        self.tree.heading("status", text="Status")
        self.tree.heading("steps", text="Steps")
        self.tree.column("#0", width=260, stretch=True)
        self.tree.column("status", width=130, stretch=False)
        self.tree.column("steps", width=50, anchor="center", stretch=False)
        self.tree.grid(row=0, column=0, sticky="nsew")
        sb = ttk.Scrollbar(vids, orient="vertical", command=self.tree.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.bind("<<TreeviewSelect>>", lambda e: self.show_steps())
        self.tree.bind("<Return>", lambda e: self.show_steps())
        self.tree.bind("<Double-1>", lambda e: self.open_selected_output())

        btns = ttk.Frame(vids)
        btns.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        self.btn_all = ttk.Button(btns, text="Process All", command=self.process_all)
        self.btn_sel = ttk.Button(btns, text="Process Selected", command=self.process_selected)
        self.btn_cancel = ttk.Button(btns, text="Cancel", command=self.cancel_run,
                                     state="disabled")
        self.btn_refresh = ttk.Button(btns, text="Refresh", command=self.refresh_videos)
        for b in (self.btn_all, self.btn_sel, self.btn_cancel, self.btn_refresh):
            b.pack(side="left", padx=(0, 6))

        self.build_settings(left).grid(row=1, column=0, sticky="ew", pady=(8, 0))

        # Right column: preview + log
        nb = ttk.Notebook(main)
        nb.grid(row=1, column=1, sticky="nsew", padx=(8, 0), pady=(8, 0))
        self.notebook = nb
        self.editor = StepEditor(nb, self)
        nb.add(self.editor, text="Steps")
        nb.add(self.build_log(nb), text="Log")

        # Progress + footer
        bottom = ttk.Frame(main)
        bottom.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        bottom.columnconfigure(1, weight=1)
        ttk.Label(bottom, textvariable=self.v_status, width=55,
                  anchor="w").grid(row=0, column=0, sticky="w")
        self.progress = ttk.Progressbar(bottom, maximum=1000)
        self.progress.grid(row=0, column=1, sticky="ew", padx=(6, 0))
        ttk.Label(main, text=f"{APP_NAME} - v{GUI_VERSION} - Built {BUILD_DATE}",
                  foreground="gray").grid(row=3, column=0, columnspan=2, pady=(6, 0))

    def build_settings(self, parent):
        box = ttk.LabelFrame(parent, text="Detection Settings", padding=6)
        pad = {"padx": 4, "pady": 3}

        def label(text, r, c):
            ttk.Label(box, text=text).grid(row=r, column=c, sticky="w", **pad)

        def entry(var, r, c):
            ttk.Entry(box, textvariable=var, width=8).grid(row=r, column=c, sticky="w", **pad)

        label("Sensitivity:", 0, 0)
        preset = ttk.Combobox(box, textvariable=self.v_preset, state="readonly",
                              values=list(SENSITIVITY_PRESETS), width=22)
        preset.grid(row=0, column=1, columnspan=2, sticky="w", **pad)
        preset.bind("<<ComboboxSelected>>", lambda e: self.apply_preset())
        th = ttk.Entry(box, textvariable=self.v_threshold, width=8)
        th.grid(row=0, column=3, sticky="w", **pad)
        th.bind("<KeyRelease>", lambda e: self.v_preset.set(self.preset_for_threshold()))

        label("Screenshot taken:", 1, 0)
        ttk.Combobox(box, textvariable=self.v_capture, state="readonly",
                     values=list(CAPTURE_POINTS), width=34).grid(
            row=1, column=1, columnspan=3, sticky="w", **pad)

        label("Merge changes within (s):", 2, 0)
        entry(self.v_debounce, 2, 1)
        label("Min gap between shots (s):", 2, 2)
        entry(self.v_min_gap, 2, 3)
        label("Force a shot after (s):", 3, 0)
        entry(self.v_max_wait, 3, 1)
        label("Image format:", 3, 2)
        ttk.Combobox(box, textvariable=self.v_format, state="readonly",
                     values=("png", "jpg"), width=6).grid(row=3, column=3, sticky="w", **pad)

        label("Shot before change (s):", 4, 0)
        entry(self.v_lead, 4, 1)
        label("Settle after change (s):", 4, 2)
        entry(self.v_settle, 4, 3)
        label("Analyze fps:", 5, 0)
        entry(self.v_fps, 5, 1)
        label("Analyze width (px):", 5, 2)
        entry(self.v_width, 5, 3)

        ttk.Checkbutton(box, text="Remove duplicate screenshots",
                        variable=self.v_dedup).grid(row=6, column=0, columnspan=2, sticky="w", **pad)
        label("Duplicate if differs by (%):", 6, 2)
        entry(self.v_dedup_thr, 6, 3)

        ttk.Checkbutton(box, text="Highlight what changed in each step (red box)",
                        variable=self.v_highlight).grid(row=7, column=0, columnspan=4,
                                                        sticky="w", **pad)

        opts = ttk.Frame(box)
        opts.grid(row=8, column=0, columnspan=4, sticky="ew", pady=(4, 0))
        ttk.Checkbutton(opts, text="Reprocess videos that are already done",
                        variable=self.v_force).grid(row=0, column=0, sticky="w", padx=4)
        ttk.Checkbutton(opts, text="Dry run (count steps only, save nothing)",
                        variable=self.v_dry).grid(row=1, column=0, sticky="w", padx=4)
        opts.columnconfigure(1, weight=1)
        ttk.Button(opts, text="Reset Defaults", command=self.reset_defaults).grid(
            row=0, column=1, rowspan=2, sticky="e", padx=4)
        return box

    def build_log(self, parent):
        frame = ttk.Frame(parent, padding=6)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        self.log_text = ScrolledText(frame, height=10, state="disabled", wrap="word")
        self.log_text.grid(row=0, column=0, sticky="nsew")
        self.log_text.tag_configure("error", foreground="#c00000")
        self.log_text.tag_configure("warn", foreground="#b06000")
        ttk.Button(frame, text="Clear", command=self.clear_log).grid(
            row=1, column=0, sticky="e", pady=(6, 0))
        return frame

    # ------------------------------------------------------------ settings

    def preset_for_threshold(self):
        try:
            t = float(self.v_threshold.get())
        except ValueError:
            return "Custom"
        for name, value in SENSITIVITY_PRESETS.items():
            if value is not None and abs(value - t) < 1e-9:
                return name
        return "Custom"

    def apply_preset(self):
        value = SENSITIVITY_PRESETS.get(self.v_preset.get())
        if value is not None:
            self.v_threshold.set(str(value))

    def reset_defaults(self):
        d = self.defaults
        for var, value in ((self.v_threshold, d.threshold), (self.v_debounce, d.debounce),
                           (self.v_min_gap, d.min_gap), (self.v_max_wait, d.max_wait),
                           (self.v_lead, d.lead), (self.v_settle, d.settle),
                           (self.v_fps, d.analyze_fps), (self.v_width, d.analyze_width),
                           (self.v_format, d.format), (self.v_dedup_thr, d.dedup_threshold)):
            var.set(str(value))
        self.v_dedup.set(not d.no_dedup)
        self.v_highlight.set(not d.no_highlight)
        self.v_capture.set(list(CAPTURE_POINTS)[0])
        self.v_preset.set(self.preset_for_threshold())

    def setting_vars(self):
        return {"source": self.v_source, "output": self.v_output,
                "recursive": self.v_recursive, "threshold": self.v_threshold,
                "capture": self.v_capture, "debounce": self.v_debounce,
                "min_gap": self.v_min_gap, "max_wait": self.v_max_wait,
                "lead": self.v_lead, "settle": self.v_settle, "fps": self.v_fps,
                "width": self.v_width, "format": self.v_format,
                "dedup": self.v_dedup, "dedup_threshold": self.v_dedup_thr,
                "highlight": self.v_highlight}

    def load_settings(self):
        try:
            data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return
        for key, var in self.setting_vars().items():
            if key in data:
                try:
                    var.set(data[key])
                except tk.TclError:
                    pass
        self.v_preset.set(self.preset_for_threshold())

    def save_settings(self):
        try:
            SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
            data = {k: v.get() for k, v in self.setting_vars().items()}
            SETTINGS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except OSError:
            pass  # settings are a convenience; never block the user over them

    def build_args(self):
        """Validate the form and turn it into a screencap args namespace."""
        numbers = [("Threshold", self.v_threshold, "-t", 0.0, 1.0, False),
                   ("Merge changes within", self.v_debounce, "--debounce", 0, None, True),
                   ("Min gap", self.v_min_gap, "--min-gap", 0, None, True),
                   ("Force a shot after", self.v_max_wait, "--max-wait", 0, None, True),
                   ("Lead", self.v_lead, "--lead", 0, None, True),
                   ("Settle", self.v_settle, "--settle", 0, None, True),
                   ("Analyze fps", self.v_fps, "--analyze-fps", 0, None, True),
                   ("Analyze width", self.v_width, "--analyze-width", 0, None, True),
                   ("Duplicate tolerance", self.v_dedup_thr, "--dedup-threshold", 0, 100,
                    True)]
        cli = ["-s", self.v_source.get().strip(), "-o", self.v_output.get().strip(),
               "-c", CAPTURE_POINTS.get(self.v_capture.get(), "end"),
               "-f", self.v_format.get()]
        for name, var, flag, lo, hi, inclusive in numbers:
            raw = var.get().strip()
            try:
                value = int(raw) if flag == "--analyze-width" else float(raw)
            except ValueError:
                raise ValueError(f"{name} must be a number (got '{raw}').")
            too_low = value < lo if inclusive else value <= lo
            if too_low or (hi is not None and value >= hi):
                rng = f"between {lo} and {hi}" if hi is not None else f"{lo} or more"
                raise ValueError(f"{name} must be {rng} (got {raw}).")
            cli += [flag, raw]
        if not self.v_source.get().strip() or not self.v_output.get().strip():
            raise ValueError("Choose both a source folder and an output folder.")
        if self.v_recursive.get():
            cli.append("-r")
        if not self.v_dedup.get():
            cli.append("--no-dedup")
        if not self.v_highlight.get():
            cli.append("--no-highlight")
        if self.v_force.get():
            cli.append("--force")
        if self.v_dry.get():
            cli.append("--dry-run")
        try:
            return sc.parse_args(cli)
        except SystemExit:
            raise ValueError("One of the settings is invalid. Check the values and try again.")

    # -------------------------------------------------------------- videos

    def browse(self, var):
        start = var.get() if Path(var.get()).is_dir() else str(sc.SCRIPT_DIR)
        chosen = filedialog.askdirectory(initialdir=start, parent=self.root)
        if chosen:
            var.set(str(Path(chosen)))
            self.refresh_videos()

    def open_folder(self, var):
        path = Path(var.get())
        try:
            path.mkdir(parents=True, exist_ok=True)
            open_path(path)
        except OSError as exc:
            messagebox.showerror(APP_NAME, f"Could not open {path}:\n{exc}", parent=self.root)

    def refresh_videos(self):
        if self.worker and self.worker.is_alive():
            return
        if not self.editor.confirm_discard():
            return
        self.editor_iid = None
        self.editor.load(None, None)
        selected = {self.videos[i][0] for i in self.tree.selection() if i in self.videos}
        self.tree.delete(*self.tree.get_children())
        self.videos.clear()
        source = Path(self.v_source.get()).expanduser()
        output = Path(self.v_output.get()).expanduser()
        if not source.is_dir():
            self.set_status(f"Source folder does not exist yet: {source}")
            self.show_steps()
            return
        found = sc.discover_videos(source, self.v_recursive.get())
        for video in found:
            out_dir = sc.output_dir_for(video, source, output, found)
            iid = self.tree.insert("", "end", text=str(video.relative_to(source)))
            self.videos[iid] = (video, out_dir)
            self.update_row_from_disk(iid)
            if video in selected:
                self.tree.selection_add(iid)
        self.set_status(f"{len(found)} video(s) found in {source}" if found else
                        f"No .mp4, .mov, or .mkv files in {source}")
        self.show_steps()

    def update_row_from_disk(self, iid):
        _, out_dir = self.videos[iid]
        manifest = self.read_manifest(out_dir)
        if manifest is not None:
            self.tree.set(iid, "status", "Done")
            self.tree.set(iid, "steps", len(manifest.get("steps", [])))
        else:
            self.tree.set(iid, "status", "New")
            self.tree.set(iid, "steps", "")

    @staticmethod
    def read_manifest(out_dir):
        try:
            return json.loads((out_dir / sc.MANIFEST_NAME).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None

    # ---------------------------------------------------------- processing

    def check_ffmpeg(self):
        if self.ffmpeg and self.ffprobe:
            sc.log.info("Using FFmpeg: %s", self.ffmpeg)
            return True
        sc.log.error(sc.FFMPEG_MISSING_HELP)
        messagebox.showwarning(APP_NAME, sc.FFMPEG_MISSING_HELP, parent=self.root)
        return False

    def process_all(self):
        self.start(list(self.videos))

    def process_selected(self):
        sel = [i for i in self.tree.selection() if i in self.videos]
        if not sel:
            messagebox.showinfo(APP_NAME, "Select one or more videos first "
                                "(Ctrl+click or Shift+click for several).", parent=self.root)
            return
        self.start(sel)

    def start(self, iids):
        if self.worker and self.worker.is_alive():
            return
        if not iids:
            messagebox.showinfo(APP_NAME, "No videos to process. Put recordings in the "
                                "source folder, then click Refresh.", parent=self.root)
            return
        if not (self.ffmpeg and self.ffprobe):
            self.ffmpeg, self.ffprobe = sc.find_tool("ffmpeg"), sc.find_tool("ffprobe")
            if not self.check_ffmpeg():
                return
        try:
            args = self.build_args()
        except ValueError as exc:
            messagebox.showerror(APP_NAME, str(exc), parent=self.root)
            return
        if self.editor_iid in iids and not self.editor.confirm_discard():
            return
        self.save_settings()
        for iid in iids:
            self.tree.set(iid, "status", "Queued")
        # Recompute output folders in case the output path was edited after
        # the last refresh
        source = args.source.expanduser().resolve()
        output = args.output.expanduser().resolve()
        all_videos = [v for v, _ in self.videos.values()]
        jobs = []
        try:
            for iid in iids:
                video = self.videos[iid][0]
                jobs.append((iid, video, sc.output_dir_for(video, source, output,
                                                           all_videos)))
        except ValueError:
            messagebox.showinfo(APP_NAME, "The source folder changed. Click Refresh "
                                "to reload the video list, then try again.", parent=self.root)
            return
        for iid, video, out_dir in jobs:
            self.videos[iid] = (video, out_dir)
        self.cancel.clear()
        self.set_running(True)
        self.notebook.select(1)
        self.worker = threading.Thread(target=self.run_jobs, args=(jobs, args), daemon=True)
        self.worker.start()

    def run_jobs(self, jobs, args):
        """Worker thread. Never touches Tk widgets; talks to the UI via self.q."""
        file_log = sc.add_file_log(args.output.expanduser().resolve())
        results = {"ok": 0, "skipped": 0, "failed": 0, "cancelled": 0}
        total = len(jobs)
        sc.log.info("--- Run started: %d video(s), screencap.py v%s ---", total, sc.VERSION)
        try:
            for n, (iid, video, out_dir) in enumerate(jobs):
                if self.cancel.is_set():
                    self.q.put(("row", iid, "Cancelled", None))
                    results["cancelled"] += 1
                    continue

                def progress(frac, text, iid=iid, n=n, name=video.name):
                    self.q.put(("progress", iid, (n + frac) / total, frac,
                                f"[{n + 1}/{total}] {name}: {text}"))

                self.q.put(("row", iid, "Processing", None))
                try:
                    status, count = sc.process_video(self.ffmpeg, self.ffprobe, video,
                                                     out_dir, args, progress, self.cancel)
                    results[status] += 1
                    label = {"skipped": "Done (skipped)"}.get(
                        status, "Dry run" if args.dry_run else "Done")
                    self.q.put(("row", iid, label, count))
                except sc.Cancelled:
                    results["cancelled"] += 1
                    sc.log.warning("Cancelled %s", video.name)
                    self.q.put(("row", iid, "Cancelled", None))
                except Exception as exc:  # report and continue with the next video
                    results["failed"] += 1
                    sc.log.error("FAILED %s: %s", video.name, exc)
                    sc.log.debug("Details", exc_info=True)
                    self.q.put(("row", iid, "Failed", None))
        finally:
            sc.log.info("--- Run finished: processed=%d skipped=%d failed=%d cancelled=%d ---",
                        results["ok"], results["skipped"], results["failed"],
                        results["cancelled"])
            if file_log is not None:
                sc.log.removeHandler(file_log)
                file_log.close()
            self.q.put(("done", results, bool(args.dry_run)))

    def cancel_run(self):
        if self.worker and self.worker.is_alive():
            self.cancel.set()
            self.set_status("Cancelling...")

    def set_running(self, running):
        state = "disabled" if running else "normal"
        for b in (self.btn_all, self.btn_sel, self.btn_refresh):
            b.configure(state=state)
        self.btn_cancel.configure(state="normal" if running else "disabled")
        self.root.configure(cursor="watch" if running else "")

    def poll_queue(self):
        try:
            while True:
                msg = self.q.get_nowait()
                kind = msg[0]
                if kind == "log":
                    self.append_log(msg[1], msg[2])
                elif kind == "progress":
                    _, iid, overall, frac, text = msg
                    self.progress["value"] = overall * 1000
                    self.tree.set(iid, "status", f"Processing {frac * 100:.0f}%")
                    self.set_status(text)
                elif kind == "status":
                    self.set_status(msg[1])
                elif kind == "row":
                    _, iid, status, count = msg
                    if iid in self.videos:
                        self.tree.set(iid, "status", status)
                        if count is not None:
                            self.tree.set(iid, "steps", count)
                        if status.startswith("Done"):
                            self.update_row_from_disk(iid)
                            if iid == self.editor_iid:
                                self.editor.reload()
                        if iid in self.tree.selection():
                            self.show_steps()
                elif kind == "done":
                    self.on_done(msg[1], msg[2])
        except queue.Empty:
            pass
        self.root.after(100, self.poll_queue)

    def on_done(self, results, dry_run):
        self.set_running(False)
        self.progress["value"] = 0
        summary = (f"Finished: {results['ok']} processed, {results['skipped']} skipped, "
                   f"{results['failed']} failed")
        if results["cancelled"]:
            summary += f", {results['cancelled']} cancelled"
        self.set_status(summary)
        if results["failed"]:
            messagebox.showwarning(APP_NAME, summary + ".\n\nSee the Log tab or "
                                   "screencap.log in the output folder for details.",
                                   parent=self.root)
        elif results["ok"] and not dry_run:
            self.notebook.select(0)
            self.editor_iid = None
            self.show_steps()

    # --------------------------------------------------------------- steps

    def selected_video(self):
        sel = [i for i in self.tree.selection() if i in self.videos]
        return self.videos[sel[0]] if sel else None

    def show_steps(self):
        """Open the first selected video in the Steps tab. If it has unsaved
        edits and the user cancels, keep the current video selected."""
        sel = [i for i in self.tree.selection() if i in self.videos]
        iid = sel[0] if sel else None
        if iid == self.editor_iid and iid is not None:
            return
        video, out_dir = self.videos[iid] if iid else (None, None)
        if self.editor.load(video, out_dir):
            self.editor_iid = iid
        elif self.editor_iid in self.videos:
            self.tree.selection_set(self.editor_iid)

    def open_selected_output(self):
        current = self.selected_video()
        if current and current[1].is_dir():
            open_path(current[1])
        elif current:
            messagebox.showinfo(APP_NAME, "This video has not been processed yet.",
                                parent=self.root)

    def on_steps_saved(self, out_dir):
        for iid, (_, d) in self.videos.items():
            if d == out_dir:
                self.update_row_from_disk(iid)

    def run(self, cmd):
        return sc.run(cmd)

    def open_path(self, path):
        open_path(path)

    def log_error(self, text):
        sc.log.error(text)

    # ----------------------------------------------------------------- misc

    def append_log(self, text, level=logging.INFO):
        tag = "error" if level >= logging.ERROR else "warn" if level >= logging.WARNING else None
        self.log_text.configure(state="normal")
        self.log_text.insert("end", text + "\n", tag)
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def clear_log(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    def set_status(self, text):
        self.v_status.set(text if len(text) <= 90 else text[:87] + "...")

    def on_ui_error(self, exc_type, exc, tb):
        detail = "".join(traceback.format_exception(exc_type, exc, tb))
        sc.log.error("Unexpected error:\n%s", detail)
        messagebox.showerror(APP_NAME, f"Unexpected error: {exc}\n\nDetails are in the Log tab.",
                             parent=self.root)

    def on_close(self):
        if not self.editor.confirm_discard():
            return
        if self.worker and self.worker.is_alive():
            if not messagebox.askyesno(APP_NAME, "Processing is still running. "
                                       "Cancel it and exit?", parent=self.root):
                return
            self.cancel.set()
            self.worker.join(timeout=10)
        self.save_settings()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        self.root.destroy()


def set_window_icon(root):
    """Title bar, taskbar, Alt+Tab, and Dock icon. Missing icon files are not
    fatal; the window just keeps the default icon."""
    png = ASSETS_DIR / "icon.png"
    ico = ASSETS_DIR / "icon.ico"
    try:
        if os.name == "nt" and ico.is_file():
            # .ico holds every size, so Windows picks a crisp one for each spot
            root.iconbitmap(default=str(ico))
        elif png.is_file():
            root._icon_image = tk.PhotoImage(file=str(png))  # keep a reference
            root.iconphoto(True, root._icon_image)
    except tk.TclError:
        pass


def main():
    if os.name == "nt":
        import ctypes
        try:  # must be set before any window exists
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)
        except Exception:
            pass
        try:  # crisp text on high-DPI displays instead of blurry bitmap scaling
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass
    # className sets the Linux WM_CLASS used to match the .desktop menu entry
    root = tk.Tk(className="ScreencapDocTool")
    set_window_icon(root)
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
