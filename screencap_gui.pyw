#!/usr/bin/env python3
#
# screencap_gui.pyw
# 2026-11-11
# Version: v2.10.0
#
# PURPOSE:
# Desktop GUI for screencap.py. Pick source/output folders, tune detection
# settings, record the screen with the built-in recorder (gui_recorder.py),
# process recordings with live progress, then review and edit the captured
# steps in the Steps tab (see gui_editor.py). The Help menu has
# built-in help, the About window, project links, and the update check
# (see gui_help.py). Light, dark, and system themes are in theme.py.
#
# Requires: Python 3.8+ with Tkinter (included with the python.org / winget
# Windows installer) and FFmpeg. The .pyw extension runs without a console
# window when double-clicked on Windows.

import json
import logging
import os
import queue
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import traceback
from pathlib import Path

import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

sys.path.insert(0, str(Path(__file__).resolve().parent))
import apppaths  # noqa: E402
import export  # noqa: E402
import player  # noqa: E402
import presets  # noqa: E402
import version  # noqa: E402
import i18n  # noqa: E402
from i18n import N_, _  # noqa: E402
import redact  # noqa: E402
import region  # noqa: E402
import screencap as sc  # noqa: E402
import transcribe  # noqa: E402
import gui_archive  # noqa: E402
import gui_help  # noqa: E402
import gui_recorder  # noqa: E402
import updates  # noqa: E402
import theme  # noqa: E402
from gui_editor import StepEditor  # noqa: E402

APP_NAME = version.APP_NAME
GUI_VERSION = "2.4.0"   # this file; the release version is in version.py
ASSETS_DIR = apppaths.BUNDLE_DIR / "assets"
# Unique taskbar identity so Windows shows this app's icon instead of grouping
# the window under the generic Python (pythonw.exe) icon. Convention for every
# app in this organization: ILHS.<AppName>.<Component>
APP_USER_MODEL_ID = "ILHS.ScreencapDocumentationTool.GUI"

# Shown translated: App.sensitivity and App.capture_points
SENSITIVITY_PRESETS = {
    N_("High (more shots)"): 0.002,
    N_("Normal (recommended)"): 0.005,
    N_("Low (fewer shots)"): 0.015,
    N_("Custom"): None,
}
CAPTURE_POINTS = {
    N_("Finished state (before next change)"): "end",
    N_("Right after each change"): "start",
}
THEME_LABELS = {"system": N_("System Theme"), "light": N_("Light Theme"),
                "dark": N_("Dark Theme")}

# Settings live in the user profile, not the repo, because they contain
# local folder paths (which can include the Windows user name).
SETTINGS_DIR = presets.settings_dir()
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
        self.recording = None     # gui_recorder.RecordingSession while recording
        self.log = sc.log
        self.temp_dir = Path(tempfile.mkdtemp(prefix="screencap_preview_"))
        self.ffmpeg = sc.find_tool("ffmpeg")
        self.ffprobe = sc.find_tool("ffprobe")
        self.tesseract = redact.find_tesseract()
        self.pandoc = export.find_pandoc()
        self.browser = export.find_browser()
        self.vlc = player.find_vlc()
        self.whisper_python = transcribe.find_python()
        self.defaults = sc.parse_args([])
        if apppaths.FROZEN or apppaths.PACKAGE_KIND:
            # Packaged app: make the default folders in Documents on first start
            for folder in (self.defaults.source, self.defaults.output):
                try:
                    folder.mkdir(parents=True, exist_ok=True)
                except OSError:
                    pass

        i18n.set_language(self.read_settings_file().get("language", i18n.SYSTEM))
        self.sensitivity = {_(k): v for k, v in SENSITIVITY_PRESETS.items()}
        self.capture_points = {_(k): v for k, v in CAPTURE_POINTS.items()}
        root.title(f"{APP_NAME} v{version.RELEASE}")
        root.geometry("1400x860")
        root.minsize(1180, 720)
        root.protocol("WM_DELETE_WINDOW", self.on_close)
        root.report_callback_exception = self.on_ui_error

        self.log_handler = QueueLogHandler(self.q)
        sc.log.addHandler(self.log_handler)
        sc.log.setLevel(logging.DEBUG)

        # Remembered between runs but not shown in the form: update check
        # choice, last check date, and a skipped version
        self.settings_extra = {}
        self.updater = gui_help.UpdateChecker(self)

        self.build_vars()
        self.build_styles()
        self.build_menu()
        self.build_ui()
        self.load_settings()
        self.theme.apply()
        self.refresh_videos()
        self.check_ffmpeg()
        self.poll_job = self.root.after(100, self.poll_queue)
        self.update_job = self.root.after(2500, self.updater.startup)
        updates.clean_downloads()     # installers left from an earlier update

    # ------------------------------------------------------------------ UI

    def build_vars(self):
        d = self.defaults
        self.v_source = tk.StringVar(value=str(d.source))
        self.v_output = tk.StringVar(value=str(d.output))
        self.v_recursive = tk.BooleanVar(value=False)
        self.v_preset = tk.StringVar(value=_("Normal (recommended)"))
        self.v_threshold = tk.StringVar(value=str(d.threshold))
        self.v_capture = tk.StringVar(value=list(self.capture_points)[0])
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
        self.v_redact = tk.BooleanVar(value=not d.no_redact)
        self.v_patterns = tk.StringVar(value="")
        self.v_transcribe = tk.BooleanVar(value=False)
        self.v_whisper_model = tk.StringVar(value=transcribe.DEFAULT_MODEL)
        self.v_profile = tk.StringVar(value=presets.DEFAULT)
        self.v_force = tk.BooleanVar(value=False)
        self.v_dry = tk.BooleanVar(value=False)
        self.v_status = tk.StringVar(value=_("Ready"))
        self.v_auto_update = tk.BooleanVar(value=False)
        self.v_preset_about = tk.StringVar(value=presets.describe(presets.DEFAULT))
        self.v_theme = tk.StringVar(value="system")
        self.v_date_format = tk.StringVar(value="system")   # a key of region.DATE_FORMATS
        self.v_clock = tk.StringVar(value="system")         # a key of region.CLOCKS
        for var in (self.v_date_format, self.v_clock):
            var.trace_add("write", lambda *_: region.configure(self.v_date_format.get(),
                                                               self.v_clock.get()))

    def build_styles(self):
        saved = self.read_settings_file()
        self.v_theme.set(saved.get("theme") if saved.get("theme") in theme.MODES else "system")
        self.theme = theme.Theme(self.root, self.v_theme.get())
        self.theme.listeners.append(self.on_theme_changed)
        try:   # the app icon, small, for the About window
            self.root._about_icon = tk.PhotoImage(
                file=str(ASSETS_DIR / "icon.png")).subsample(4)
        except tk.TclError:
            self.root._about_icon = None

    def set_theme(self, mode):
        self.v_theme.set(mode)
        self.theme.set_mode(mode)
        self.save_settings()

    def on_theme_changed(self):
        c = self.theme.colors
        if hasattr(self, "log_text"):
            self.log_text.tag_configure("error", foreground=c["error"])
            self.log_text.tag_configure("warn", foreground=c["warn"])
        if hasattr(self, "editor"):
            self.editor.on_theme_changed()

    def build_menu(self):
        """File, View, and Help. On macOS they go in the system menu bar. On
        Windows and Linux they are drawn inside the window: the native Windows
        menu bar cannot change color, so it stayed white in the dark theme."""
        self.native_menu = self.root.tk.call("tk", "windowingsystem") == "aqua"
        if self.native_menu:
            menubar = tk.Menu(self.root)
            self.root.configure(menu=menubar)
        else:
            menubar = ttk.Frame(self.root, style="Menubar.TFrame", padding=(6, 2))
            menubar.pack(side="top", fill="x")
            ttk.Separator(self.root, orient="horizontal").pack(side="top", fill="x")
        self.menubar = menubar
        self.menus = {}           # "File", "View", "Help" (in English) -> tk.Menu
        self.menu_buttons = {}    # same keys -> ttk.Menubutton (in-window bar only)
        used_keys = set()         # Alt+letter, unique in every language

        def cascade(key):
            label = _(key)
            under = next((i for i, ch in enumerate(label.lower())
                          if ch.isalpha() and ch not in used_keys), 0)
            used_keys.add(label[under].lower())
            if self.native_menu:
                menu = tk.Menu(menubar, tearoff=False)
                menubar.add_cascade(label=label, menu=menu)
            else:
                button = ttk.Menubutton(menubar, text=label, style="Menubar.TMenubutton",
                                        underline=under, takefocus=False)
                menu = tk.Menu(button, tearoff=False)
                button.configure(menu=menu)
                button.pack(side="left")
                self.menu_buttons[key] = button
                self.root.bind(f"<Alt-{label[under].lower()}>",
                               lambda e, b=button: self.post_menu(b))
            self.menus[key] = menu
            return menu

        file_menu = cascade(N_("File"))
        file_menu.add_command(label=_("Record Screen..."), accelerator="Ctrl+R",
                              command=self.start_recording)
        file_menu.add_separator()
        file_menu.add_command(label=_("Choose Source Folder..."),
                              command=lambda: self.browse(self.v_source))
        file_menu.add_command(label=_("Choose Output Folder..."),
                              command=lambda: self.browse(self.v_output))
        file_menu.add_separator()
        file_menu.add_command(label=_("Open Source Folder"),
                              command=lambda: self.open_folder(self.v_source))
        file_menu.add_command(label=_("Open Output Folder"),
                              command=lambda: self.open_folder(self.v_output))
        file_menu.add_separator()
        file_menu.add_command(label=_("Archive Selected Recordings..."),
                              command=lambda: gui_archive.archive_selected(self))
        file_menu.add_command(label=_("Archived Recordings..."),
                              command=lambda: gui_archive.ArchiveWindow(self))
        file_menu.add_separator()
        file_menu.add_command(label=_("Exit"), command=self.on_close)

        view_menu = cascade(N_("View"))
        for mode in theme.MODES:
            view_menu.add_radiobutton(label=_(THEME_LABELS[mode]), value=mode,
                                      variable=self.v_theme,
                                      command=lambda m=mode: self.set_theme(m))
        view_menu.add_separator()
        language_menu = tk.Menu(view_menu, tearoff=False)
        view_menu.add_cascade(label=_("Language"), menu=language_menu)
        self.v_language = tk.StringVar(value=self.read_settings_file().get("language",
                                                                            i18n.SYSTEM))
        language_menu.add_radiobutton(label=_("System Language"), value=i18n.SYSTEM,
                                      variable=self.v_language, command=self.set_language)
        language_menu.add_separator()
        for code, name in i18n.LANGUAGES.items():
            language_menu.add_radiobutton(label=name, value=code, variable=self.v_language,
                                          command=self.set_language)
        self.language_menu = language_menu
        view_menu.add_command(label=_("Advanced Settings..."), command=self.open_advanced)
        view_menu.add_command(label=_("Steps"), accelerator="Ctrl+1",
                              command=lambda: self.notebook.select(0))
        view_menu.add_command(label=_("Log"), accelerator="Ctrl+2",
                              command=lambda: self.notebook.select(1))
        self.view_menu = view_menu
        self.root.bind("<Control-r>", lambda e: self.start_recording())
        self.root.bind("<Control-Key-1>", lambda e: self.notebook.select(0))
        self.root.bind("<Control-Key-2>", lambda e: self.notebook.select(1))

        help_menu = cascade(N_("Help"))
        help_menu.add_command(label=_("Help"), accelerator="F1", command=self.show_help)
        help_menu.add_command(label=_("Keyboard Shortcuts"),
                              command=lambda: self.show_help("Keyboard Shortcuts"))
        help_menu.add_command(label=_("Online Documentation"),
                              command=lambda: self.open_url(updates.DOCS_URL))
        help_menu.add_separator()
        help_menu.add_command(label=_("Report a Problem..."),
                              command=lambda: self.open_url(updates.BUG_REPORT_URL))
        help_menu.add_command(label=_("Suggest an Idea..."),
                              command=lambda: self.open_url(updates.IDEA_URL))
        help_menu.add_command(label=_("Project on GitHub"),
                              command=lambda: self.open_url(updates.REPO_URL))
        help_menu.add_command(label=_("Release Notes"),
                              command=lambda: self.open_url(updates.RELEASES_URL))
        help_menu.add_separator()
        help_menu.add_command(label=_("Check for Updates..."),
                              command=lambda: self.check_for_updates(manual=True))
        help_menu.add_checkbutton(label=_("Check for Updates Automatically"),
                                  variable=self.v_auto_update,
                                  command=self.on_auto_update_toggled)
        help_menu.add_separator()
        help_menu.add_command(label=_("About {app}").format(app=APP_NAME), command=self.show_about)
        self.help_menu = help_menu
        self.root.bind("<F1>", lambda e: self.show_help())

    def post_menu(self, button):
        """Alt+F, Alt+V, Alt+H: open that menu of the in-window menu bar."""
        menu = self.root.nametowidget(str(button.cget("menu")))
        try:
            menu.tk_popup(button.winfo_rootx(), button.winfo_rooty() + button.winfo_height())
        finally:
            menu.grab_release()
        return "break"

    # ---------------------------------------------------------------- help

    def show_help(self, topic=None):
        names = [name for name, _ in gui_help.TOPICS]
        return gui_help.HelpWindow(self, names.index(topic) if topic in names else 0)

    def show_about(self):
        return gui_help.AboutWindow(self)

    def open_url(self, url):
        gui_help.open_url(url)

    def check_for_updates(self, manual=True):
        self.updater.start(manual)

    def on_auto_update_toggled(self):
        self.settings_extra["check_updates"] = bool(self.v_auto_update.get())
        if self.v_auto_update.get():
            self.updater.start(manual=False)
        self.save_settings()

    def build_ui(self):
        main = ttk.Frame(self.root)
        main.pack(fill="both", expand=True)
        main.columnconfigure(0, weight=1)
        main.rowconfigure(1, weight=1)

        # Folders: a compact bar across the top
        folders = ttk.Frame(main, style="Bar.TFrame", padding=(14, 10, 14, 10))
        folders.grid(row=0, column=0, sticky="ew")
        folders.columnconfigure(1, weight=1)
        for row, (label, var) in enumerate(((_("Recordings"), self.v_source),
                                            (_("Output"), self.v_output))):
            ttk.Label(folders, text=label, style="Bar.TLabel").grid(
                row=row, column=0, sticky="w", padx=(0, 10), pady=3)
            ttk.Entry(folders, textvariable=var).grid(row=row, column=1, sticky="ew", pady=3)
            ttk.Button(folders, text=_("Browse..."), command=lambda v=var: self.browse(v)).grid(
                row=row, column=2, padx=(8, 0), pady=3)
            ttk.Button(folders, text=_("Open"), command=lambda v=var: self.open_folder(v)).grid(
                row=row, column=3, padx=(6, 0), pady=3)
        ttk.Checkbutton(folders, text=_("Include subfolders"), variable=self.v_recursive,
                        style="Bar.TCheckbutton", command=self.refresh_videos).grid(
            row=0, column=4, sticky="w", padx=(14, 0))
        ttk.Separator(main, orient="horizontal").grid(row=0, column=0, sticky="sew")

        body = ttk.PanedWindow(main, orient="horizontal")
        body.grid(row=1, column=0, sticky="nsew", padx=12, pady=(12, 0))
        self.body = body
        self.sash_job = self.root.after(50, lambda: self.place_sash(body))

        # Left: recordings and settings
        side = ttk.Frame(body)
        self.side = side
        side.columnconfigure(0, weight=1)
        side.rowconfigure(0, weight=1)
        body.add(side, weight=0)

        vids = ttk.Frame(side, style="Card.TFrame", padding=12)
        vids.grid(row=0, column=0, sticky="nsew")
        vids.columnconfigure(0, weight=1)
        vids.rowconfigure(1, weight=1)
        head = ttk.Frame(vids, style="Card.TFrame")
        head.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        ttk.Label(head, text=_("Recordings"), style="Card.Heading.TLabel").pack(side="left")
        self.btn_refresh = ttk.Button(head, text=_("Refresh"), command=self.refresh_videos)
        self.btn_refresh.pack(side="right")
        self.btn_record = ttk.Button(head, text=_("\u25cf Record"), command=self.start_recording)
        self.btn_record.pack(side="right", padx=(0, 6))
        self.tree = ttk.Treeview(vids, columns=("status", "steps"), selectmode="extended",
                                 height=6)
        self.tree.heading("#0", text=_("Recording"), anchor="w")
        self.tree.heading("status", text=_("Status"), anchor="w")
        self.tree.heading("steps", text=_("Steps"))
        self.tree.column("#0", width=220, stretch=True)
        self.tree.column("status", width=110, stretch=False)
        self.tree.column("steps", width=64, anchor="center", stretch=False)
        self.tree.grid(row=1, column=0, sticky="nsew")
        sb = ttk.Scrollbar(vids, orient="vertical", command=self.tree.yview)
        sb.grid(row=1, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.bind("<<TreeviewSelect>>", lambda e: self.show_steps())
        self.tree.bind("<Return>", lambda e: self.show_steps())
        self.tree.bind("<Double-1>", lambda e: self.open_selected_output())
        self.tree_menu = tk.Menu(self.tree, tearoff=False)
        self.tree_menu.add_command(label=_("Process"), command=self.process_selected)
        self.tree_menu.add_command(label=_("Open Output Folder"),
                                   command=self.open_selected_output)
        self.tree_menu.add_separator()
        self.tree_menu.add_command(label=_("Archive..."),
                                   command=lambda: gui_archive.archive_selected(self))
        for button in ("<Button-3>", "<Button-2>" if sys.platform == "darwin" else None):
            if button:
                self.tree.bind(button, self.show_tree_menu)
        btns = ttk.Frame(vids, style="Card.TFrame")
        btns.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        self.btn_all = ttk.Button(btns, text=_("Process All"), style="Accent.TButton",
                                  command=self.process_all)
        self.btn_sel = ttk.Button(btns, text=_("Process Selected"), command=self.process_selected)
        self.btn_cancel = ttk.Button(btns, text=_("Cancel"), command=self.cancel_run,
                                     state="disabled")
        for b in (self.btn_all, self.btn_sel, self.btn_cancel):
            b.pack(side="left", padx=(0, 6))

        self.build_settings(side).grid(row=1, column=0, sticky="ew", pady=(12, 0))

        # Right: the step editor and the log
        nb = ttk.Notebook(body)
        body.add(nb, weight=1)
        self.notebook = nb
        self.editor = StepEditor(nb, self)
        nb.add(self.editor, text=_("Steps"))
        nb.add(self.build_log(nb), text=_("Log"))

        # Status bar: what the app is doing (left), progress, and on the right
        # the version with its update state (click it to check again)
        bar = ttk.Frame(main, style="Bar.TFrame", padding=(14, 6))
        bar.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        bar.columnconfigure(0, weight=1)
        ttk.Label(bar, textvariable=self.v_status, style="Bar.TLabel", anchor="w").grid(
            row=0, column=0, sticky="ew")
        self.progress = ttk.Progressbar(bar, maximum=1000, length=220)
        self.progress.grid(row=0, column=1, padx=(12, 16))
        ttk.Label(bar, text=_("Version {version}").format(version=version.RELEASE),
                  style="Bar.Muted.TLabel").grid(
            row=0, column=2, sticky="e")
        ttk.Label(bar, text="\u00b7", style="Bar.Muted.TLabel").grid(row=0, column=3, padx=6)
        self.lbl_update = ttk.Label(bar, style="Bar.Link.TLabel", cursor="hand2")
        self.lbl_update.grid(row=0, column=4, sticky="e")
        self.lbl_update.bind("<Button-1>", lambda e: self.on_update_label_clicked())
        self.update_result = None
        self.set_update_state("off" if updates.disabled_by_policy() else "unknown")

    UPDATE_STATES = {   # state -> (text, label style); {v} is the newer version
        "unknown": (N_("Check for updates"), "Bar.Link.TLabel"),
        "checking": (N_("Checking for updates..."), "Bar.Muted.TLabel"),
        "latest": (N_("\u2713 Up to date"), "Bar.Ok.TLabel"),
        "available": (N_("Update available: v{v}"), "Bar.Warn.TLabel"),
        "failed": (N_("Update check failed. Try again"), "Bar.Link.TLabel"),
        "off": (N_("Update checks turned off"), "Bar.Muted.TLabel"),
    }

    def set_update_state(self, state, result=None):
        """The update indicator in the status bar (bottom right)."""
        self.update_state = state
        if result is not None:
            self.update_result = result
        text, style = self.UPDATE_STATES[state]
        text = _(text)
        newer = (self.update_result or {}).get("version", "")
        self.lbl_update.configure(text=text.format(v=newer), style=style,
                                  cursor="" if state in ("checking", "off") else "hand2")

    def on_update_label_clicked(self):
        if self.update_state == "available" and self.update_result:
            self.updater.offer(self.update_result)
        elif self.update_state not in ("checking", "off"):
            self.check_for_updates(manual=True)

    def place_sash(self, body, width=470, tries=40):
        """Give the sidebar its starting width once the window has its size
        (before that, the panes have no room to divide). Wider when its text
        needs more room (longer words in another language), up to 640."""
        try:
            width = max(width, min(self.side.winfo_reqwidth(), 640))
            if body.winfo_width() < width + 300 and tries > 0:
                self.sash_job = self.root.after(
                    50, lambda: self.place_sash(body, width, tries - 1))
                return
            self.sash_job = None
            body.sashpos(0, width)
        except tk.TclError:
            pass

    def build_settings(self, parent):
        box = ttk.Frame(parent, style="Card.TFrame", padding=12)
        box.columnconfigure(1, weight=1)
        pad = {"padx": (0, 8), "pady": 3}
        ttk.Label(box, text=_("Settings"), style="Card.Heading.TLabel").grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 6))

        ttk.Label(box, text=_("Preset"), style="Card.TLabel").grid(row=1, column=0, sticky="w", **pad)
        self.cmb_profile = ttk.Combobox(box, textvariable=self.v_profile, state="readonly",
                                        values=presets.names(), width=28)
        self.cmb_profile.grid(row=1, column=1, columnspan=2, sticky="ew", pady=3)
        self.cmb_profile.bind("<<ComboboxSelected>>", lambda e: self.apply_profile())
        self.lbl_preset_about = ttk.Label(box, textvariable=self.v_preset_about,
                                          style="Card.Muted.TLabel", wraplength=380,
                                          justify="left")
        self.lbl_preset_about.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(2, 8))
        box.bind("<Configure>", lambda e: self.lbl_preset_about.configure(
            wraplength=max(240, e.width - 30)))

        ttk.Label(box, text=_("Sensitivity"), style="Card.TLabel").grid(row=3, column=0, sticky="w", **pad)
        sens = ttk.Frame(box, style="Card.TFrame")
        sens.grid(row=3, column=1, columnspan=2, sticky="w")
        preset = ttk.Combobox(sens, textvariable=self.v_preset, state="readonly",
                              values=list(self.sensitivity), width=22)
        preset.pack(side="left")
        preset.bind("<<ComboboxSelected>>", lambda e: self.apply_preset())
        th = ttk.Entry(sens, textvariable=self.v_threshold, width=7)
        th.pack(side="left", padx=(6, 0))
        th.bind("<KeyRelease>", lambda e: self.v_preset.set(self.preset_for_threshold()))
        ttk.Label(box, text=_("Screenshot taken"), style="Card.TLabel").grid(
            row=4, column=0, sticky="w", **pad)
        ttk.Combobox(box, textvariable=self.v_capture, state="readonly",
                     values=list(self.capture_points), width=34).grid(
            row=4, column=1, columnspan=2, sticky="w", pady=3)

        checks = ttk.Frame(box, style="Card.TFrame")
        checks.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(6, 0))
        for text, var in ((_("Highlight what changed in each step (red box)"), self.v_highlight),
                          (_("Blur passwords, keys, IP and email addresses"), self.v_redact),
                          (_("Remove duplicate screenshots"), self.v_dedup)):
            ttk.Checkbutton(checks, text=text, variable=var, style="Card.TCheckbutton").pack(
                anchor="w")
        narr = ttk.Frame(checks, style="Card.TFrame")
        narr.pack(anchor="w", fill="x")
        ttk.Checkbutton(narr, text=_("Captions from narration"), variable=self.v_transcribe,
                        style="Card.TCheckbutton").pack(side="left")
        ttk.Combobox(narr, textvariable=self.v_whisper_model, state="readonly",
                     values=transcribe.MODELS, width=9).pack(side="right")
        ttk.Label(narr, text=_("Model") if self.whisper_python else _("Model (not installed)"),
                  style="Card.Muted.TLabel").pack(side="right", padx=(0, 6))

        links = ttk.Frame(box, style="Card.TFrame")
        links.grid(row=6, column=0, columnspan=3, sticky="ew", pady=(8, 0))
        ttk.Button(links, text=_("Advanced Settings..."), style="Card.Link.TButton",
                   command=self.open_advanced).pack(side="left")
        ttk.Button(links, text=_("Delete Preset"), style="Card.Link.TButton",
                   command=self.delete_profile).pack(side="right")
        ttk.Button(links, text=_("Save as Preset..."), style="Card.Link.TButton",
                   command=self.save_profile).pack(side="right", padx=(0, 14))
        return box

    def open_advanced(self):
        """The timing and output settings, in their own window so the main
        window stays uncluttered. They change the same settings as the form."""
        win = getattr(self, "advanced_window", None)
        if win is not None and win.winfo_exists():
            win.deiconify()
            win.lift()
            win.focus_force()
            return win
        win = tk.Toplevel(self.root)
        win.title(_("Advanced Settings"))
        win.resizable(False, False)
        win.transient(self.root)
        self.advanced_window = win
        adv = ttk.Frame(win, padding=(20, 18))
        adv.pack(fill="both", expand=True)
        adv.columnconfigure(0, weight=1)
        ttk.Label(adv, text=_("Advanced Settings"), style="Heading.TLabel").grid(
            row=0, column=0, sticky="w")
        ttk.Label(adv, text=_("These apply to the next run. To keep them, save them as a preset "
                            "(Save as Preset in the main window)."),
                  style="Muted.TLabel", wraplength=470, justify="left").grid(
            row=1, column=0, sticky="w", pady=(2, 12))
        seconds = _("seconds")
        sections = (
            (_("Timing"), (
                (_("Merge changes closer than"), self.v_debounce, seconds),
                (_("Minimum time between screenshots"), self.v_min_gap, seconds),
                (_("Take a screenshot anyway after"), self.v_max_wait, seconds),
                (_("Screenshot before the next change"), self.v_lead, seconds),
                (_("Wait after a change (right-after mode)"), self.v_settle, seconds))),
            (_("Detection"), (
                (_("Frames checked per second"), self.v_fps, _("0 = every frame")),
                (_("Analysis width"), self.v_width, _("pixels, 0 = full size")),
                (_("Duplicate when it differs by at most"), self.v_dedup_thr, _("percent")))),
        )
        row, cards, labels = 2, [], []
        for title, fields in sections:
            card = self.advanced_card(adv, title, row)
            cards.append(card)
            for n, (text, var, unit) in enumerate(fields, start=1):
                labels.append(ttk.Label(card, text=text, style="Card.TLabel"))
                labels[-1].grid(row=n, column=0, sticky="w", padx=(0, 16), pady=2)
                ttk.Entry(card, textvariable=var, width=8, justify="right").grid(
                    row=n, column=1, sticky="w", pady=2)
                ttk.Label(card, text=unit, style="Card.Muted.TLabel").grid(
                    row=n, column=2, sticky="w", padx=(8, 0), pady=2)
            row += 1

        card = self.advanced_card(adv, _("Output"), row)
        cards.append(card)
        labels.append(ttk.Label(card, text=_("Image format"), style="Card.TLabel"))
        labels[-1].grid(row=1, column=0, sticky="w", padx=(0, 16), pady=2)
        ttk.Combobox(card, textvariable=self.v_format, state="readonly",
                     values=("png", "jpg"), width=6).grid(row=1, column=1, sticky="w", pady=2)
        ttk.Label(card, text=_("Also blur"), style="Card.TLabel").grid(
            row=2, column=0, sticky="w", padx=(0, 16), pady=(8, 3))
        ttk.Entry(card, textvariable=self.v_patterns).grid(
            row=2, column=1, columnspan=2, sticky="ew", pady=(8, 3))
        ttk.Label(card, text=_("Regular expressions, separated by semicolons; "
                             "for example corp\\.example\\.com;TICKET-\\d+"),
                  style="Card.Muted.TLabel", wraplength=300, justify="left").grid(
            row=3, column=1, columnspan=2, sticky="w")
        row += 1

        card = self.advanced_card(adv, _("Region"), row)
        cards.append(card)
        for n, (text, var, choices) in enumerate(
                ((_("Dates"), self.v_date_format,
                  {k: _(v[0]) for k, v in region.DATE_FORMATS.items()}),
                 (_("Times"), self.v_clock, {k: _(v) for k, v in region.CLOCKS.items()})),
                start=1):
            labels.append(ttk.Label(card, text=text, style="Card.TLabel"))
            labels[-1].grid(row=n, column=0, sticky="w", padx=(0, 16), pady=2)
            shown = tk.StringVar(value=choices.get(var.get(), choices["system"]))
            box = ttk.Combobox(card, textvariable=shown, state="readonly", width=30,
                               values=list(choices.values()))
            box.grid(row=n, column=1, columnspan=2, sticky="w", pady=2)
            box.bind("<<ComboboxSelected>>", lambda e, v=var, c=choices, s=shown:
                     v.set({lab: key for key, lab in c.items()}[s.get()]))
        ttk.Label(card, text=_("For the date on exported documents and the times the app "
                             "shows. System setting follows Windows, macOS, or Linux."),
                  style="Card.Muted.TLabel", wraplength=300, justify="left").grid(
            row=3, column=1, columnspan=2, sticky="w")
        row += 1

        card = self.advanced_card(adv, _("Run"), row)
        ttk.Checkbutton(card, text=_("Reprocess recordings that are already done"),
                        variable=self.v_force, style="Card.TCheckbutton").grid(
            row=1, column=0, columnspan=3, sticky="w", pady=2)
        ttk.Checkbutton(card, text=_("Dry run: count the steps only, save nothing"),
                        variable=self.v_dry, style="Card.TCheckbutton").grid(
            row=2, column=0, columnspan=3, sticky="w", pady=2)
        row += 1

        # The same label column width in every group, so all the boxes line up
        win.update_idletasks()
        widest = max(label.winfo_reqwidth() for label in labels) + 16
        for card in cards:
            card.columnconfigure(0, minsize=widest)

        bar = ttk.Frame(adv)
        bar.grid(row=row, column=0, sticky="ew", pady=(16, 0))
        ttk.Button(bar, text=_("Reset to Defaults"), command=self.reset_defaults).pack(side="left")
        ttk.Button(bar, text=_("Close"), style="Accent.TButton", command=win.destroy).pack(
            side="right")
        win.bind("<Escape>", lambda e: win.destroy())
        self.theme.style_widgets(win)
        return win

    @staticmethod
    def advanced_card(parent, title, row):
        """One titled group in the Advanced Settings window."""
        card = ttk.Frame(parent, style="Card.TFrame", padding=(14, 8))
        card.grid(row=row, column=0, sticky="ew", pady=(0, 8))
        card.columnconfigure(2, weight=1)
        ttk.Label(card, text=title, style="Card.Heading.TLabel").grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 4))
        return card

    def build_log(self, parent):
        frame = ttk.Frame(parent, padding=10)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        self.log_text = tk.Text(frame, height=10, state="disabled", wrap="word",
                                padx=10, pady=8)
        self.log_text.grid(row=0, column=0, sticky="nsew")
        sb = ttk.Scrollbar(frame, orient="vertical", command=self.log_text.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=sb.set)
        ttk.Button(frame, text=_("Clear"), command=self.clear_log).grid(
            row=1, column=0, columnspan=2, sticky="e", pady=(8, 0))
        return frame

    # ------------------------------------------------------------ settings

    def preset_for_threshold(self):
        try:
            t = float(self.v_threshold.get())
        except ValueError:
            return _("Custom")
        for name, value in self.sensitivity.items():
            if value is not None and abs(value - t) < 1e-9:
                return name
        return _("Custom")

    def apply_preset(self):
        value = self.sensitivity.get(self.v_preset.get())
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
        self.v_redact.set(not d.no_redact)
        self.v_capture.set(list(self.capture_points)[0])
        self.v_preset.set(self.preset_for_threshold())
        self.v_patterns.set("")
        self.v_transcribe.set(False)
        self.v_whisper_model.set(transcribe.DEFAULT_MODEL)
        self.v_profile.set(presets.DEFAULT)
        self.v_preset_about.set(presets.describe(presets.DEFAULT))

    # ------------------------------------------------------------ presets

    def profile_vars(self):
        """Preset key -> (Tk variable, to_form, from_form) converters."""
        cap_rev = {v: k for k, v in self.capture_points.items()}
        num = (str, lambda v: v)
        neg = (lambda v: not v, lambda v: not v)
        return {
            "threshold": (self.v_threshold,) + num, "debounce": (self.v_debounce,) + num,
            "settle": (self.v_settle,) + num, "lead": (self.v_lead,) + num,
            "max_wait": (self.v_max_wait,) + num, "min_gap": (self.v_min_gap,) + num,
            "analyze_fps": (self.v_fps,) + num, "analyze_width": (self.v_width,) + num,
            "dedup_threshold": (self.v_dedup_thr,) + num, "format": (self.v_format,) + num,
            "capture_point": (self.v_capture, lambda v: cap_rev.get(v, list(self.capture_points)[0]),
                              lambda v: v),
            "no_dedup": (self.v_dedup,) + neg, "no_highlight": (self.v_highlight,) + neg,
            "no_redact": (self.v_redact,) + neg,
            "redact_pattern": (self.v_patterns, lambda v: "; ".join(v or []), lambda v: v),
        }

    def apply_profile(self):
        """Fill the form from the chosen preset. Settings the preset does not
        mention go back to their defaults."""
        name = self.v_profile.get()
        values = presets.get(name)
        if values is None:
            return
        d = self.defaults
        for key, (var, to_form, _from_form) in self.profile_vars().items():
            var.set(to_form(values.get(key, getattr(d, key))))
        self.v_preset.set(self.preset_for_threshold())
        self.v_preset_about.set(presets.describe(name))
        self.set_status(_("Preset '{name}' applied.").format(name=name))

    def save_profile(self):
        try:
            args = self.build_args()
        except ValueError as exc:
            messagebox.showerror(APP_NAME, str(exc), parent=self.root)
            return
        name = simpledialog.askstring(APP_NAME, _("Name for this preset:"), parent=self.root,
                                      initialvalue="" if presets.is_builtin(self.v_profile.get())
                                      else self.v_profile.get())
        if not name:
            return
        if name.strip() in presets.load_user() and not messagebox.askyesno(
                APP_NAME, _('Replace the preset "{name}"?').format(name=name.strip()),
                parent=self.root):
            return
        try:
            presets.save_user(name, {k: getattr(args, k) for k in presets.KEYS})
        except (ValueError, OSError) as exc:
            messagebox.showerror(APP_NAME, _("Could not save the preset:\n{error}").format(error=exc),
                                 parent=self.root)
            return
        self.cmb_profile.configure(values=presets.names())
        self.v_profile.set(name.strip())
        self.v_preset_about.set(presets.describe(name.strip()))
        self.set_status(_("Saved preset '{name}'.").format(name=name.strip()))

    def delete_profile(self):
        name = self.v_profile.get()
        if presets.is_builtin(name):
            messagebox.showinfo(APP_NAME, _("Built-in presets cannot be deleted."), parent=self.root)
            return
        if messagebox.askyesno(APP_NAME, _('Delete the preset "{name}"?').format(name=name),
                               parent=self.root):
            presets.delete_user(name)
            self.cmb_profile.configure(values=presets.names())
            self.v_profile.set(presets.DEFAULT)
            self.v_preset_about.set(presets.describe(presets.DEFAULT))
            self.set_status(_("Deleted preset '{name}'.").format(name=name))

    def setting_vars(self):
        return {"source": self.v_source, "output": self.v_output,
                "recursive": self.v_recursive, "threshold": self.v_threshold,
                "capture": self.v_capture, "debounce": self.v_debounce,
                "min_gap": self.v_min_gap, "max_wait": self.v_max_wait,
                "lead": self.v_lead, "settle": self.v_settle, "fps": self.v_fps,
                "width": self.v_width, "format": self.v_format,
                "dedup": self.v_dedup, "dedup_threshold": self.v_dedup_thr,
                "highlight": self.v_highlight, "redact": self.v_redact,
                "redact_patterns": self.v_patterns, "preset": self.v_profile,
                "transcribe": self.v_transcribe, "whisper_model": self.v_whisper_model,
                "theme": self.v_theme, "date_format": self.v_date_format,
                "clock": self.v_clock}

    @staticmethod
    def read_settings_file():
        try:
            data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except (OSError, ValueError):
            return {}

    def load_settings(self):
        data = self.read_settings_file()
        if data:
            self.apply_saved_settings(data)
        self.apply_installer_folders()

    def apply_installer_folders(self):
        """Folders picked in the Windows installer replace the saved ones once,
        right after that install; changes made in the app afterwards stay."""
        chosen = apppaths.INSTALLER_FOLDERS
        if not chosen or not chosen.stamp or \
                self.settings_extra.get("installer_folders") == chosen.stamp:
            return
        self.v_source.set(str(chosen.source))
        self.v_output.set(str(chosen.output))
        self.settings_extra["installer_folders"] = chosen.stamp
        for folder in (chosen.source, chosen.output):
            try:
                folder.mkdir(parents=True, exist_ok=True)
            except OSError:
                pass
        self.save_settings()

    def apply_saved_settings(self, data):
        for key, var in self.setting_vars().items():
            if key in data:
                try:
                    var.set(data[key])
                except tk.TclError:
                    pass
        self.v_capture.set(self.capture_label(data.get("capture")))
        self.v_preset.set(self.preset_for_threshold())
        # canonical(): names saved before v1.23.0 were in sentence case
        self.v_profile.set(presets.canonical(self.v_profile.get()) or presets.DEFAULT)
        self.settings_extra = {k: data[k] for k in ("check_updates", "last_update_check",
                                                    "skip_version", "installer_folders",
                                                    "export_logo", "export_template",
                                                    *gui_recorder.SETTINGS_KEYS,
                                                    gui_archive.SHRINK_KEY)
                               if k in data}
        self.v_auto_update.set(bool(self.settings_extra.get("check_updates")))
        if self.v_theme.get() not in theme.MODES:
            self.v_theme.set("system")
        self.v_preset_about.set(presets.describe(self.v_profile.get()))

    def save_settings(self):
        try:
            SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
            data = {k: v.get() for k, v in self.setting_vars().items()}
            data["capture"] = self.capture_points.get(data["capture"], "end")
            data["language"] = self.v_language.get()
            data.update(self.settings_extra)
            SETTINGS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except OSError:
            pass  # settings are a convenience; never block the user over them

    def capture_label(self, saved):
        """The capture choice as shown, from a saved code ("end"/"start"), or
        an English label as saved before v1.39.0."""
        code = CAPTURE_POINTS.get(saved, saved)
        return {v: k for k, v in self.capture_points.items()}.get(
            code, list(self.capture_points)[0])

    def set_language(self):
        """View > Language: saved now, used from the next start."""
        self.save_settings()
        code = self.v_language.get()
        name = (_("the system language") if code == i18n.SYSTEM
                else i18n.LANGUAGES.get(code, code))
        messagebox.showinfo(APP_NAME, _("{app} will use {language} the next time it "
                                        "starts.").format(app=APP_NAME, language=name),
                            parent=self.root)

    def build_args(self):
        """Validate the form and turn it into a screencap args namespace."""
        numbers = [(_("Threshold"), self.v_threshold, "-t", 0.0, 1.0, False),
                   (_("Merge changes within"), self.v_debounce, "--debounce", 0, None, True),
                   (_("Min gap"), self.v_min_gap, "--min-gap", 0, None, True),
                   (_("Force a shot after"), self.v_max_wait, "--max-wait", 0, None, True),
                   (_("Lead"), self.v_lead, "--lead", 0, None, True),
                   (_("Settle"), self.v_settle, "--settle", 0, None, True),
                   (_("Analyze fps"), self.v_fps, "--analyze-fps", 0, None, True),
                   (_("Analyze width"), self.v_width, "--analyze-width", 0, None, True),
                   (_("Duplicate tolerance"), self.v_dedup_thr, "--dedup-threshold", 0, 100,
                    True)]
        cli = ["-s", self.v_source.get().strip(), "-o", self.v_output.get().strip(),
               "-c", self.capture_points.get(self.v_capture.get(), "end"),
               "-f", self.v_format.get()]
        for name, var, flag, lo, hi, inclusive in numbers:
            raw = var.get().strip()
            try:
                value = int(raw) if flag == "--analyze-width" else float(raw)
            except ValueError:
                raise ValueError(_("{name} must be a number (got '{value}').").format(
                    name=name, value=raw))
            too_low = value < lo if inclusive else value <= lo
            if too_low or (hi is not None and value >= hi):
                msg = (_("{name} must be between {low} and {high} (got {value}).")
                       if hi is not None else _("{name} must be {low} or more (got {value})."))
                raise ValueError(msg.format(name=name, low=lo, high=hi, value=raw))
            cli += [flag, raw]
        if not self.v_source.get().strip() or not self.v_output.get().strip():
            raise ValueError(_("Choose both a source folder and an output folder."))
        if self.v_recursive.get():
            cli.append("-r")
        if not self.v_dedup.get():
            cli.append("--no-dedup")
        if not self.v_highlight.get():
            cli.append("--no-highlight")
        if not self.v_redact.get():
            cli.append("--no-redact")
        for rx in (p.strip() for p in self.v_patterns.get().split(";")):
            if rx:
                try:
                    re.compile(rx)
                except re.error as exc:
                    raise ValueError(_("'{pattern}' in Also blur is not a valid pattern: {error}")
                                     .format(pattern=rx, error=exc))
                cli += ["--redact-pattern", rx]
        if self.v_transcribe.get() and not self.v_dry.get():
            if not transcribe.find_python():
                raise ValueError(transcribe.WHISPER_MISSING_HELP + "\n\n"
                                 + _("Or untick Captions from narration."))
            cli += ["--transcribe", "--whisper-model", self.whisper_model()]
        if self.v_force.get():
            cli.append("--force")
        if self.v_dry.get():
            cli.append("--dry-run")
        try:
            return sc.parse_args(cli)
        except SystemExit:
            raise ValueError(_("One of the settings is invalid. Check the values and try "
                               "again."))

    # -------------------------------------------------------------- videos

    def browse(self, var):
        start = var.get() if Path(var.get()).is_dir() else str(apppaths.DATA_DIR)
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
            messagebox.showerror(APP_NAME, _("Could not open {path}:\n{error}").format(
                path=path, error=exc), parent=self.root)

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
        # Resolve like start() does, so a short (8.3), junction, or symlinked
        # path names the videos the same way in both places
        source = Path(self.v_source.get()).expanduser().resolve()
        output = Path(self.v_output.get()).expanduser().resolve()
        if not source.is_dir():
            self.set_status(_("Source folder does not exist yet: {folder}").format(folder=source))
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
        self.set_status(_("{n} recording(s) found in {folder}").format(n=len(found), folder=source)
                        if found else
                        _("No .mp4, .mov, or .mkv files in {folder}").format(folder=source))
        self.show_steps()

    def update_row_from_disk(self, iid):
        _video, out_dir = self.videos[iid]
        manifest = self.read_manifest(out_dir)
        if manifest is not None:
            self.tree.set(iid, "status", _("Done"))
            self.tree.set(iid, "steps", len(manifest.get("steps", [])))
        else:
            self.tree.set(iid, "status", _("New"))
            self.tree.set(iid, "steps", "")

    @staticmethod
    def read_manifest(out_dir):
        try:
            return json.loads((out_dir / sc.MANIFEST_NAME).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None

    # ---------------------------------------------------------- processing

    def check_ffmpeg(self):
        sc.log.info("%s v%s (GUI v%s, engine screencap.py v%s)", APP_NAME, version.RELEASE,
                    GUI_VERSION, sc.VERSION)
        if self.ffmpeg and self.ffprobe:
            sc.log.info("Using FFmpeg: %s", self.ffmpeg)
            if self.tesseract:
                sc.log.info("Using Tesseract OCR: %s", self.tesseract)
            else:
                sc.log.warning(redact.TESSERACT_MISSING_HELP)
            if not self.pandoc:
                sc.log.info("Pandoc not found: Word export unavailable (HTML and PDF still work).")
            if not self.browser:
                sc.log.info("Edge/Chrome/Chromium not found: PDF export unavailable.")
            if not self.vlc:
                sc.log.info("VLC not found: Play in VLC unavailable.")
            if self.whisper_python:
                sc.log.info("Using speech recognition (faster-whisper): %s", self.whisper_python)
            else:
                sc.log.info("Speech recognition not installed: Captions from narration "
                            "unavailable (optional, see README).")
            return True
        sc.log.error(sc.FFMPEG_MISSING_HELP)
        messagebox.showwarning(APP_NAME, sc.FFMPEG_MISSING_HELP, parent=self.root)
        return False

    def whisper_model(self):
        model = self.v_whisper_model.get().strip()
        return model if model in transcribe.MODELS else transcribe.DEFAULT_MODEL

    def process_all(self):
        self.start(list(self.videos))

    def process_selected(self):
        sel = [i for i in self.tree.selection() if i in self.videos]
        if not sel:
            messagebox.showinfo(APP_NAME, _("Select one or more videos first "
                                "(Ctrl+click or Shift+click for several)."), parent=self.root)
            return
        done = [i for i in sel if self.videos[i][1] is not None
                and (self.videos[i][1] / sc.INDEX_NAME).is_file()]
        force = False
        if done and not self.v_force.get():
            which = (_("This recording is already processed.") if len(sel) == 1 else
                     _("{n} of the selected recordings are already processed.").format(
                         n=len(done)))
            answer = messagebox.askyesnocancel(
                APP_NAME, which + "\n\n" + _(
                    "Process again with the current settings? The previous screenshots, "
                    "captions, and exports are kept in a previous-<date> folder next to the "
                    "new ones.\n\nNo skips the finished ones."),
                parent=self.root)
            if answer is None:
                return
            force = answer
        self.start(sel, force=force)

    def start(self, iids, force=False):
        if self.worker and self.worker.is_alive():
            return
        if not iids:
            messagebox.showinfo(APP_NAME, _("No videos to process. Put recordings in the "
                                "source folder, then click Refresh."), parent=self.root)
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
        args.force = args.force or force
        if self.editor_iid in iids and not self.editor.confirm_discard():
            return
        self.save_settings()
        for iid in iids:
            self.tree.set(iid, "status", _("Queued"))
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
            messagebox.showinfo(APP_NAME, _("The source folder changed. Click Refresh "
                                "to reload the video list, then try again."), parent=self.root)
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
                    self.q.put(("row", iid, N_("Cancelled"), None))
                    results["cancelled"] += 1
                    continue

                def progress(frac, text, iid=iid, n=n, name=video.name):
                    self.q.put(("progress", iid, (n + frac) / total, frac,
                                f"[{n + 1}/{total}] {name}: {text}"))

                self.q.put(("row", iid, N_("Processing"), None))
                try:
                    status, count = sc.process_video(self.ffmpeg, self.ffprobe, video,
                                                     out_dir, args, progress, self.cancel)
                    results[status] += 1
                    label = {"skipped": N_("Done (skipped)")}.get(
                        status, N_("Dry run") if args.dry_run else N_("Done"))
                    if args.transcribe and not args.dry_run:
                        self.q.put(("row", iid, N_("Transcribing"), None))
                        if sc.transcribe_video(video, out_dir, args, self.ffmpeg,
                                               cancel=self.cancel):
                            results["failed"] += 1
                            label = N_("Done (captions failed)")
                    self.q.put(("row", iid, label, count))
                except sc.Cancelled:
                    results["cancelled"] += 1
                    sc.log.warning("Cancelled %s", video.name)
                    self.q.put(("row", iid, N_("Cancelled"), None))
                except Exception as exc:  # report and continue with the next video
                    results["failed"] += 1
                    sc.log.error("FAILED %s: %s", video.name, exc)
                    sc.log.debug("Details", exc_info=True)
                    self.q.put(("row", iid, N_("Failed"), None))
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
            self.set_status(_("Cancelling..."))

    def set_running(self, running):
        state = "disabled" if running else "normal"
        for b in (self.btn_all, self.btn_sel, self.btn_refresh, self.btn_record):
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
                    _kind, iid, overall, frac, text = msg
                    self.progress["value"] = overall * 1000
                    self.tree.set(iid, "status", _("Processing {percent}%").format(
                        percent=f"{frac * 100:.0f}"))
                    self.set_status(text)
                elif kind == "status":
                    self.set_status(msg[1])
                elif kind == "row":
                    _kind, iid, status, count = msg
                    if iid in self.videos:
                        self.tree.set(iid, "status", _(status))
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
                elif kind == "call":           # finish background work on this thread
                    msg[1]()
                elif kind == "update":
                    self.updater.finished(msg[1], msg[2])
                    self.save_settings()
        except queue.Empty:
            pass
        self.poll_job = self.root.after(100, self.poll_queue)

    def on_done(self, results, dry_run):
        self.set_running(False)
        self.progress["value"] = 0
        summary = _("Finished: {ok} processed, {skipped} skipped, {failed} failed").format(
            ok=results["ok"], skipped=results["skipped"], failed=results["failed"])
        if results["cancelled"]:
            summary += _(", {n} cancelled").format(n=results["cancelled"])
        self.set_status(summary)
        if results["failed"]:
            messagebox.showwarning(APP_NAME, summary + ".\n\n" + _(
                "See the Log tab or screencap.log in the output folder for details."),
                                   parent=self.root)
        elif results["ok"] and not dry_run:
            self.notebook.select(0)
            self.editor_iid = None
            self.show_steps()

    # --------------------------------------------------------------- steps

    # ----------------------------------------------------------- recording

    def start_recording(self):
        if self.recording is not None or (self.worker and self.worker.is_alive()):
            return
        if not self.editor.confirm_discard():
            return
        gui_recorder.RecordingSession(self).open()

    def on_recorded(self, path, process):
        """A recording was saved: show it in the list and, if asked, process it."""
        events = gui_recorder.recorder.load_events(path) or {}
        sc.log.info("Saved the recording to %s (%d click(s) and key(s) noted)", path,
                    len(events.get("events") or []))
        self.refresh_videos()
        iid = next((i for i, (v, _) in self.videos.items()
                    if v.resolve() == Path(path).resolve()), None)
        if iid is None:
            self.set_status(_("Saved {name}. It is not in the list because the Recordings "
                              "folder changed.").format(name=Path(path).name))
            return
        self.tree.selection_set(iid)
        self.tree.see(iid)
        if process:
            self.start([iid])
        else:
            self.set_status(_("Saved {name}. Click Process Selected to make the "
                              "screenshots.").format(name=Path(path).name))

    def show_tree_menu(self, event):
        """Right-click menu of the Recordings list, for the row clicked (added
        to the selection) or the current selection."""
        row = self.tree.identify_row(event.y)
        if row and row not in self.tree.selection():
            self.tree.selection_set(row)
        if self.tree.selection() and not (self.worker and self.worker.is_alive()):
            self.tree_menu.tk_popup(event.x_root, event.y_root)

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
            messagebox.showinfo(APP_NAME, _("This video has not been processed yet."),
                                parent=self.root)

    def on_steps_saved(self, out_dir):
        for iid, (_video, d) in self.videos.items():
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
        self.v_status.set(text if len(text) <= 140 else text[:137] + "...")

    def on_ui_error(self, exc_type, exc, tb):
        detail = "".join(traceback.format_exception(exc_type, exc, tb))
        sc.log.error("Unexpected error:\n%s", detail)
        messagebox.showerror(APP_NAME, _("Unexpected error: {error}\n\nDetails are in the Log tab.")
                             .format(error=exc),
                             parent=self.root)

    def close_for_update(self):
        """Update Now started the installer: close at once (unsaved edits
        were already handled), so it can replace this copy's files."""
        self.on_close(ask=False)

    def on_close(self, ask=True):
        if ask and not self.editor.confirm_discard():
            return
        if self.recording is not None:
            self.recording.cancel_quietly()
        if self.worker and self.worker.is_alive():
            if ask and not messagebox.askyesno(APP_NAME, _("Processing is still running. "
                                               "Cancel it and exit?"), parent=self.root):
                return
            self.cancel.set()
            self.worker.join(timeout=10)
        self.save_settings()
        self.theme.stop()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        # Cancel scheduled callbacks so none fire after the window is gone
        for job in (getattr(self, "poll_job", None), getattr(self, "update_job", None),
                    getattr(self, "sash_job", None), self.editor.preview_job):
            if job:
                try:
                    self.root.after_cancel(job)
                except tk.TclError:
                    pass
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
    smoke = "--smoke-test" in sys.argv[1:]
    if smoke:   # used by the package tests: no update question, close by itself
        os.environ["SCREENCAP_NO_UPDATE_CHECK"] = "1"
    app = App(root)
    if smoke:
        root.after(3000, lambda: (print(root.title(), flush=True), app.on_close()))
    root.mainloop()


if __name__ == "__main__":
    main()
