#!/usr/bin/env python3
#
# gui_help.py
# 2026-10-17
# Version: v1.5.1
#
# PURPOSE:
# The GUI's Help menu: a built-in help window (short guides, keyboard
# shortcuts, troubleshooting), the About window (version, license, links,
# and the details to paste into a problem report), and the update check
# (manual, or automatic once a day when the user turned it on), with
# Update Now for copies installed with the Windows installer.

import datetime
import platform
import queue
import sys
import threading
import webbrowser

import tkinter as tk
from tkinter import messagebox, ttk

import updates
import version

TOPICS = [
    ("Getting Started", """\
0. Record (optional). Click Record above the list of recordings (or press Ctrl+R) to record the screen with the built-in recorder. Each click is noted, so the steps get a red ring where you clicked and a first-draft caption such as Click "Next". See Recording the Screen.

1. Folders. Put your screen recordings (.mp4, .mov, or .mkv) in the source folder, or choose another folder with Browse. Screenshots go to the output folder, one subfolder per recording.

2. Preset. Pick the kind of recording, for example Installer Wizard, General Desktop Use, Web Console, or Terminal / Command Line. The preset fills in all the detection settings.

3. Process. Click Process All, or select some videos and click Process Selected. Progress shows at the bottom and in the Log tab.

4. Review. Select a processed video to open its steps in the Steps tab. Reorder, delete, crop, blur, and write a caption for each step, then click Save Changes.

5. Export. Fill in the document title, version, and author, then export to HTML, Word, PDF, or PowerPoint.

The original screenshots are always kept, so every edit can be changed again later.

More settings (timing, image format, extra blur patterns, dry run) are under View > Advanced Settings. View > Light Theme, Dark Theme, or System Theme changes the look."""),
    ("Recording The Screen", """\
Record (above the list of recordings, or File > Record Screen, Ctrl+R) records the screen like Windows Steps Recorder did, but as a video:

1. Choose a microphone if you want to talk through the steps (your words can become captions with Captions From Narration), and whether keys are noted.
2. Click Start Recording. The window minimizes and a small Recording window with Stop and Discard appears in the bottom-right corner.
3. Do the task as usual, then click Stop. The recording is saved in the Recordings folder and the screenshots are made straight away (unless you unticked that).

What gets noted: where and when you click (double-clicks, right-clicks, and drags too), and keys such as Enter, Tab, Esc, arrows, function keys, and shortcuts like Ctrl+S. Typed text is never saved: letters and digits only count as "type the text".

What it is used for: each click gets a red ring on its step (a drag gets an arrow), and empty captions get a first draft such as Click "Next", or Click next to "User name", type the text, then press Tab. The words of the clicked button are read with Tesseract OCR when it is installed; words that look sensitive are left out. Edit any caption as usual; Captions From Narration replaces drafts you have not edited.

Notes: on Windows all monitors are recorded, and the Recording window is left out of the video. On macOS allow Screen Recording (and Input Monitoring for keys) in System Settings > Privacy & Security. On Linux an X11 session is needed; Wayland desktops do not let other programs record the screen, so use the desktop's own recorder and put the file in the Recordings folder."""),
    ("Presets", """\
A preset is a named set of detection settings for one kind of recording:

- Installer Wizard: the defaults, for setup wizards and settings dialogs.
- General Desktop Use: opening apps, browsing files, and flipping through menus. No blurring and no red boxes.
- Web Console: admin portals and web apps; ignores spinners and slow pages.
- Terminal / Command Line: catches small text changes, merges typing.
- Remote Desktop / VM Console: ignores compression noise and lag.
- Forms and Spreadsheets: small field changes, one step per entry.
- Slideshow / Presentation: one screenshot per slide, no red boxes.
- Video Meeting / Screen Share: ignores webcam movement, keeps blurring.
- Fast Clicking: short pauses between actions.

Too many screenshots? Lower the sensitivity. Too few? Raise it. Save your own settings with Save as Preset under the settings; saved presets work on the command line too (--preset NAME, in any capitalization)."""),
    ("Editing Steps", """\
In the Steps tab:

- Up and Down page through the steps (from the picture or the buttons). Ctrl+Up and Ctrl+Down move the selected step. Delete removes it; Restore Deleted brings removed steps back.
- Caption: type what the reader should do in this step.
- Crop menu: drag a rectangle on the picture to keep only part of the screen, for all steps or just this one.
- Blur menu: add a blur box, or click a blurred area to switch it off or back on.
- Highlight menu: the red box shows what changed since the previous step, and the zoomed inset shows a small change up close in a corner. Animated Clip of This Step adds a short GIF of the step when you save. Switch either on or off for the whole recording (top right) or for one step (Highlight menu).
- Annotate menu: draw arrows, numbered markers, and text labels on the screenshot. Edit or Remove changes or removes one, including the click rings added by the recorder.
- Screenshot / Original frame compares the edited picture with the untouched capture.
- Open menu: the screenshot, steps.md, or the output and export folders.
- Export: HTML, Word, PDF, or PowerPoint. Logo and Template chooses a company logo and a Word template (its styles and page header and footer) for every export.
- Save Changes re-renders the screenshots and steps.md from the originals. Discard Changes goes back to the last save.
- Play in VLC opens the recording just before the selected step. Captions From Narration (next to Caption) fills empty captions from what you said."""),
    ("Blurring Sensitive Information", """\
With Tesseract OCR installed, the tool reads the text in each screenshot and blurs passwords, keys, IP addresses, and email addresses automatically. An unblurred copy of every screenshot is kept in the unredacted folder, so nothing is lost.

- Add Blur Box: drag a rectangle over anything else to hide.
- Un-blur / Re-blur: click a blurred area to switch it off (or back on).
- Also blur (View > Advanced Settings): your own patterns, for example a domain name or ticket prefix, separated by semicolons.
- Exports use the blurred screenshots unless you tick Unblurred copy.

Always look through the screenshots before sharing them: automatic blurring finds text it can read, not everything sensitive."""),
    ("Exporting", """\
Export turns the saved steps into one document:

- HTML: a single file with the screenshots built in. Works everywhere.
- Word (.docx): needs Pandoc.
- PDF: needs Microsoft Edge, Google Chrome, or Chromium.
- PowerPoint (.pptx): a title slide, then one widescreen slide per step with its screenshot and caption. Narration goes in the speaker notes, and animated clips get their own slide. Needs nothing else.

Files are written to the export folder inside the recording's output folder; Open Exports shows it. Unsaved edits are saved first."""),
    ("Keyboard Shortcuts", """\
Up / Down            Previous / next step (Steps tab)
Ctrl+Up / Ctrl+Down  Move the selected step up / down
Delete               Delete the selected step
Esc                  Cancel drawing a crop or blur box
Double-click a step  Open the screenshot
Double-click a video Open its output folder
Ctrl+R               Record the screen
Ctrl+1 / Ctrl+2      Steps tab / Log tab
F1                   This help"""),
    ("Troubleshooting", """\
- "FFmpeg not found": install it with winget install --id Gyan.FFmpeg -e, then restart the app. FFmpeg does all the video work and is required.
- No automatic blurring: install Tesseract OCR (winget install --id UB-Mannheim.TesseractOCR -e).
- Word export unavailable: install Pandoc (winget install --id JohnMacFarlane.Pandoc -e).
- Too many or too few screenshots: try another preset, or change Sensitivity.
- Something else: the Log tab and screencap.log in the output folder show what happened. Help > Report a Problem opens the issue form on GitHub; Help > About can copy the details it asks for.
- Update check: the right end of the status bar shows whether you have the latest version; click it to check again. On a copy installed with the Windows installer, Update Now in the update window downloads, checks, and installs the new version, then opens the app again."""),
]


def open_url(url):
    webbrowser.open(url, new=2)


class HelpWindow(tk.Toplevel):
    def __init__(self, app, topic=0):
        super().__init__(app.root)
        self.app = app
        self.title(f"{version.APP_NAME} Help")
        self.geometry("860x560")
        self.minsize(640, 400)
        self.transient(app.root)
        body = ttk.Frame(self, padding=10)
        body.pack(fill="both", expand=True)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)
        self.topics = ttk.Treeview(body, show="tree", selectmode="browse")
        self.topics.column("#0", width=260, stretch=False)
        for n, (name, _) in enumerate(TOPICS):
            self.topics.insert("", "end", iid=str(n), text=name)
        self.topics.grid(row=0, column=0, sticky="ns")
        self.text = tk.Text(body, wrap="word", padx=14, pady=12, relief="flat",
                            highlightthickness=0, cursor="arrow", font="TkDefaultFont",
                            spacing1=2, spacing3=2)
        self.text.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        sb = ttk.Scrollbar(body, orient="vertical", command=self.text.yview)
        sb.grid(row=0, column=2, sticky="ns")
        self.text.configure(yscrollcommand=sb.set)
        self.text.tag_configure("h", font=("TkHeadingFont", 13, "bold"), spacing3=10)
        self.text.tag_configure("mono", font="TkFixedFont")
        bar = ttk.Frame(body)
        bar.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(10, 0))
        ttk.Button(bar, text="Online Documentation",
                   command=lambda: app.open_url(updates.DOCS_URL)).pack(side="left")
        ttk.Button(bar, text="Report a Problem",
                   command=lambda: app.open_url(updates.BUG_REPORT_URL)).pack(side="left", padx=6)
        ttk.Button(bar, text="Close", command=self.destroy).pack(side="right")
        self.topics.bind("<<TreeviewSelect>>", lambda e: self.show(
            [int(i) for i in self.topics.selection()]))
        self.bind("<Escape>", lambda e: self.destroy())
        if hasattr(app, "theme"):
            app.theme.style_widgets(self)
        self.topics.selection_set(str(topic))
        self.topics.focus(str(topic))
        self.show((topic,))

    def show(self, selection):
        if not selection:
            return
        name, body = TOPICS[selection[0]]
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("end", name + "\n", "h")
        self.text.insert("end", body, "mono" if name == "Keyboard Shortcuts" else ())
        self.text.configure(state="disabled")


# Programs the app uses: (attribute on the app, name, what it is for)
TOOLS = (
    ("ffmpeg", "FFmpeg", "Required: reads the recordings"),
    ("tesseract", "Tesseract OCR", "Automatic blurring"),
    ("pandoc", "Pandoc", "Word export"),
    ("browser", "Edge, Chrome, or Chromium", "PDF export"),
    ("vlc", "VLC", "Play in VLC"),
    ("whisper_python", "faster-whisper", "Captions from narration"),
)


def system_rows(app):
    """(label, value) pairs about this copy of the app and the computer."""
    return [
        ("Version", f"{version.RELEASE} (built {version.RELEASE_DATE})"),
        ("Install type", updates.install_kind_name()),
        ("Operating system", platform.platform()),
        ("Python", f"{platform.python_version()} "
                   f"({'packaged' if getattr(sys, 'frozen', False) else 'installed'})"),
        ("Tk", str(tk.TkVersion)),
    ]


def details_text(app):
    """Version and environment details for problem reports. Paths are left
    out on purpose: they can contain the Windows user name."""
    lines = [f"{version.APP_NAME} v{version.RELEASE} (built {version.RELEASE_DATE})"]
    lines += [f"{label}: {value}" for label, value in system_rows(app)[1:]]
    lines.append("Programs:")
    lines += [f"  {name}: {'installed' if getattr(app, attr, None) else 'not installed'}"
              for attr, name, _ in TOOLS]
    return "\n".join(lines)


class AboutWindow(tk.Toplevel):
    WIDTH = 500   # text wraps at this width, so the window keeps one size

    def __init__(self, app):
        super().__init__(app.root)
        self.app = app
        self.title(f"About {version.APP_NAME}")
        self.resizable(False, False)
        self.transient(app.root)
        body = ttk.Frame(self, padding=(22, 20))
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=1)

        head = ttk.Frame(body)
        head.grid(row=0, column=0, sticky="ew")
        icon = getattr(app.root, "_about_icon", None)
        if icon is not None:
            ttk.Label(head, image=icon).grid(row=0, column=0, rowspan=2, sticky="w", padx=(0, 14))
        ttk.Label(head, text=version.APP_NAME, style="Title.TLabel").grid(
            row=0, column=1, sticky="sw")
        ttk.Label(head, text=f"Version {version.RELEASE}, built {version.RELEASE_DATE}",
                  style="Muted.TLabel").grid(row=1, column=1, sticky="nw")

        ttk.Label(body, wraplength=self.WIDTH, justify="left", text=(
            "Turns screen recordings into step-by-step screenshot documentation. Free and "
            "open source under the MIT License. Everything runs on this computer; nothing "
            "is sent anywhere unless you ask for it (exports you share, the update check).")
                  ).grid(row=1, column=0, sticky="w", pady=(14, 0))
        ttk.Label(body, wraplength=self.WIDTH, justify="left", style="Muted.TLabel", text=(
            "Copyright (c) 2026 ILHS Software, LLC. FFmpeg, Tesseract OCR, Pandoc, VLC, "
            "and faster-whisper are separate programs with their own licenses.")
                  ).grid(row=2, column=0, sticky="w", pady=(6, 0))

        links = ttk.Frame(body)
        links.grid(row=3, column=0, sticky="w", pady=(10, 0))
        for n, (text, url) in enumerate((
                ("Project on GitHub", updates.REPO_URL),
                ("Release Notes", updates.RELEASES_URL),
                ("License", f"{updates.REPO_URL}/blob/main/LICENSE"),
                ("Privacy", f"{updates.REPO_URL}/blob/main/CODE_SIGNING_POLICY.md#privacy"))):
            if n:
                ttk.Label(links, text="\u00b7", style="Muted.TLabel").pack(side="left", padx=8)
            ttk.Button(links, text=text, style="Link.TButton", takefocus=False,
                       command=lambda u=url: app.open_url(u)).pack(side="left")

        ttk.Separator(body, orient="horizontal").grid(row=4, column=0, sticky="ew", pady=16)

        ttk.Label(body, text="System", style="Heading.TLabel").grid(row=5, column=0, sticky="w")
        card = self.card(body, 6)
        for n, (label, value) in enumerate(system_rows(app)):
            ttk.Label(card, text=label, style="Card.Muted.TLabel").grid(
                row=n, column=0, sticky="nw", padx=(0, 18), pady=2)
            ttk.Label(card, text=value, style="Card.TLabel", wraplength=self.WIDTH - 180,
                      justify="left").grid(row=n, column=1, columnspan=2, sticky="w", pady=2)

        ttk.Label(body, text="Programs", style="Heading.TLabel").grid(
            row=7, column=0, sticky="w", pady=(14, 0))
        card = self.card(body, 8)
        self.tool_rows = {}
        for n, (attr, name, purpose) in enumerate(TOOLS):
            found = bool(getattr(app, attr, None))
            mark = ttk.Label(card, text="\u2713" if found else "\u2717",
                             style="Card.Ok.TLabel" if found else "Card.Error.TLabel")
            mark.grid(row=n, column=0, sticky="w", padx=(0, 10), pady=2)
            ttk.Label(card, text=name, style="Card.TLabel").grid(row=n, column=1, sticky="w", pady=2)
            ttk.Label(card, text=purpose, style="Card.Muted.TLabel").grid(
                row=n, column=2, sticky="w", padx=(18, 0), pady=2)
            ttk.Label(card, text="Installed" if found else "Not installed",
                      style="Card.Muted.TLabel" if found else "Card.Error.TLabel").grid(
                row=n, column=3, sticky="e", padx=(18, 0), pady=2)
            self.tool_rows[name] = found
        card.columnconfigure(2, weight=1)

        bar = ttk.Frame(body)
        bar.grid(row=9, column=0, sticky="ew", pady=(18, 0))
        ttk.Button(bar, text="Copy Details", command=self.copy).pack(side="left")
        ttk.Button(bar, text="Check for Updates",
                   command=lambda: app.check_for_updates(manual=True)).pack(side="left", padx=(8, 0))
        ttk.Button(bar, text="Close", style="Accent.TButton", command=self.destroy).pack(side="right")
        self.bind("<Escape>", lambda e: self.destroy())
        if hasattr(app, "theme"):
            app.theme.style_widgets(self)

    @staticmethod
    def card(parent, row):
        frame = ttk.Frame(parent, style="Card.TFrame", padding=(14, 10))
        frame.grid(row=row, column=0, sticky="ew", pady=(6, 0))
        frame.columnconfigure(1, weight=1)
        return frame

    def copy(self):
        self.clipboard_clear()
        self.clipboard_append(details_text(self.app))
        self.app.set_status("Copied the version details. Paste them into the problem report.")


class UpdateChecker:
    """Runs the GitHub check on a worker thread and reports back through
    the app's queue, so the window never freezes on a slow network."""

    def __init__(self, app):
        self.app = app
        self.running = False

    def start(self, manual):
        if self.running:
            return
        if updates.disabled_by_policy():
            if manual:
                messagebox.showinfo(version.APP_NAME, "Update checks are turned off on this PC "
                                    "by your administrator (SCREENCAP_NO_UPDATE_CHECK). "
                                    f"Releases: {updates.RELEASES_URL}", parent=self.app.root)
            return
        self.running = True
        self.app.set_update_state("checking")

        def work():
            try:
                result = updates.check_latest()
            except updates.UpdateError as exc:
                result = exc
            self.app.q.put(("update", result, manual))

        threading.Thread(target=work, daemon=True).start()

    def finished(self, result, manual):
        """On the Tk thread: tell the user what the check found."""
        self.running = False
        app = self.app
        app.settings_extra["last_update_check"] = datetime.date.today().isoformat()
        if isinstance(result, Exception):
            app.set_update_state("failed")
            if manual:
                messagebox.showwarning(version.APP_NAME, f"Could not check for updates.\n\n{result}",
                                       parent=app.root)
            return
        if not updates.is_newer(result["version"]):
            app.set_update_state("latest", result)
            if manual:
                messagebox.showinfo(version.APP_NAME, f"You have the latest version, "
                                    f"v{version.RELEASE}.", parent=app.root)
            return
        app.set_update_state("available", result)
        if not manual and app.settings_extra.get("skip_version") == result["version"]:
            return   # still shown in the status bar, just no pop-up
        self.offer(result)

    def offer(self, result):
        """Show the update window (also from the status bar)."""
        UpdateDialog(self.app, result)

    def startup(self):
        """Automatic check, at most once a day, only when the user turned it
        on. The first time, ask (the answer is remembered)."""
        if updates.disabled_by_policy():
            return
        extra = self.app.settings_extra
        if extra.get("check_updates") is None:
            choice = messagebox.askyesno(
                version.APP_NAME, "Check for new versions automatically?\n\nOnce a day, the app "
                "asks GitHub whether a newer release is out. Nothing about this PC or your "
                "files is sent. You can change this any time in the Help menu.",
                parent=self.app.root)
            extra["check_updates"] = bool(choice)
            self.app.v_auto_update.set(bool(choice))
        if extra.get("check_updates") and \
                extra.get("last_update_check") != datetime.date.today().isoformat():
            self.start(manual=False)


class UpdateDialog(tk.Toplevel):
    """A newer version is out: its notes, and Update Now (Windows installer
    copies: download, check, install, reopen) or how to update this kind of
    install, with the command to copy."""
    WIDTH = 520

    def __init__(self, app, result):
        super().__init__(app.root)
        self.app, self.result = app, result
        self.kind = updates.install_kind()
        self.cancel = threading.Event()
        self.events = queue.Queue()
        self.busy = False
        self.title("Update Available")
        self.resizable(False, False)
        self.transient(app.root)
        body = ttk.Frame(self, padding=(22, 18))
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=1)
        ttk.Label(body, text=f"Version {result['version']} is available",
                  style="Heading.TLabel").grid(row=0, column=0, sticky="w")
        released = f"Released {result['published']}. " if result.get("published") else ""
        ttk.Label(body, text=f"{released}You have version {version.RELEASE}.",
                  style="Muted.TLabel").grid(row=1, column=0, sticky="w", pady=(2, 10))

        notes = tk.Text(body, width=64, height=10, wrap="word", relief="flat",
                        padx=10, pady=8, takefocus=False, font="TkDefaultFont")
        notes.insert("1.0", updates.release_notes_excerpt(result["notes"]) or
                     "See the release notes on GitHub.")
        notes.configure(state="disabled")
        notes.grid(row=2, column=0, sticky="ew")
        ttk.Button(body, text="Full release notes", style="Link.TButton", takefocus=False,
                   command=lambda: app.open_url(result["url"])).grid(row=3, column=0, sticky="w")

        self.installable = updates.can_install(self.kind)
        if self.installable:
            how = ("Update Now downloads the new installer, checks it, and installs it. "
                   "This window closes while it updates, then the app opens again. Your "
                   "settings, folders, and recordings are kept.")
            if updates.install_scope() == "ALLUSERS":
                how += " Windows asks for administrator permission, because this copy is " \
                       "installed for everyone."
        else:
            how = updates.how_to_update(self.kind)
        self.how = ttk.Label(body, text=how, wraplength=self.WIDTH, justify="left")
        self.how.grid(row=4, column=0, sticky="w", pady=(10, 0))

        self.command = None if self.installable else \
            updates.update_command(self.kind, result["version"])
        if self.command:
            row = ttk.Frame(body)
            row.grid(row=5, column=0, sticky="ew", pady=(8, 0))
            row.columnconfigure(0, weight=1)
            self.v_command = tk.StringVar(value=self.command)
            entry = ttk.Entry(row, textvariable=self.v_command, state="readonly")
            entry.grid(row=0, column=0, sticky="ew")
            ttk.Button(row, text="Copy", command=self.copy).grid(row=0, column=1, padx=(8, 0))

        self.progress = ttk.Progressbar(body, maximum=1000, length=self.WIDTH)
        self.v_status = tk.StringVar()
        self.status = ttk.Label(body, textvariable=self.v_status, style="Muted.TLabel")

        btns = ttk.Frame(body)
        btns.grid(row=8, column=0, sticky="ew", pady=(16, 0))
        self.btn_skip = ttk.Button(btns, text="Skip This Version", command=self.skip)
        self.btn_skip.pack(side="left")
        if self.installable:
            self.btn_main = ttk.Button(btns, text="Update Now", style="Accent.TButton",
                                       command=self.update_now)
        else:
            self.btn_main = ttk.Button(btns, text="Open Download", style="Accent.TButton",
                                       command=self.open_download)
        self.btn_main.pack(side="right")
        self.btn_later = ttk.Button(btns, text="Remind Me Later", command=self.close)
        self.btn_later.pack(side="right", padx=(0, 8))
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.bind("<Escape>", lambda e: self.close())
        if hasattr(app, "theme"):
            app.theme.style_widgets(self)
        self.btn_main.focus_set()
        self.update_idletasks()     # centered over the main window
        root = app.root
        x = root.winfo_rootx() + (root.winfo_width() - self.winfo_reqwidth()) // 2
        y = root.winfo_rooty() + (root.winfo_height() - self.winfo_reqheight()) // 3
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")

    # -- buttons

    def copy(self):
        self.clipboard_clear()
        self.clipboard_append(self.command)
        self.app.set_status("Copied the update command.")

    def open_download(self):
        self.app.open_url(updates.download_for(self.result, self.kind))
        self.destroy()

    def skip(self):
        self.app.settings_extra["skip_version"] = self.result["version"]
        self.destroy()

    def close(self):
        """Remind Me Later, or Cancel while downloading."""
        if self.busy:
            self.cancel.set()
            return
        self.destroy()

    def update_now(self):
        app = self.app
        if getattr(app, "recording", None) is not None or \
                (getattr(app, "worker", None) and app.worker.is_alive()):
            messagebox.showinfo(version.APP_NAME, "Finish or cancel the recording or the "
                                "processing first, then click Update Now again.", parent=self)
            return
        editor = getattr(app, "editor", None)
        if editor is not None and not editor.confirm_discard():
            return
        self.busy = True
        for b in (self.btn_main, self.btn_skip):
            b.configure(state="disabled")
        self.btn_later.configure(text="Cancel")
        self.progress.grid(row=6, column=0, sticky="ew", pady=(14, 0))
        self.status.grid(row=7, column=0, sticky="w", pady=(4, 0))
        self.v_status.set("Downloading the installer...")

        def work():
            try:
                path = updates.download_installer(
                    self.result, cancel=self.cancel,
                    progress=lambda done, total: self.events.put(("progress", done, total)))
                self.events.put(("done", path))
            except updates.UpdateError as exc:
                self.events.put(("error", exc))

        threading.Thread(target=work, daemon=True).start()
        self.after(100, self.poll)

    def poll(self):
        try:
            while True:
                event = self.events.get_nowait()
                if event[0] == "progress":
                    done, total = event[1], event[2]
                    if total:
                        self.progress["value"] = 1000 * done / total
                        self.v_status.set(f"Downloading the installer... "
                                          f"{done / 1048576:.1f} of {total / 1048576:.1f} MB")
                elif event[0] == "done":
                    self.install(event[1])
                    return
                else:
                    self.failed(event[1])
                    return
        except queue.Empty:
            pass
        self.after(100, self.poll)

    def install(self, path):
        self.v_status.set("Checked. Starting the installer...")
        self.progress["value"] = 1000
        try:
            updates.start_installer(path)
        except updates.UpdateError as exc:
            self.failed(exc)
            return
        self.app.close_for_update()

    def failed(self, exc):
        self.busy = False
        if isinstance(exc, updates.UpdateCancelled):
            self.destroy()
            return
        self.progress.grid_remove()
        self.status.grid_remove()
        self.btn_later.configure(text="Remind Me Later")
        for b in (self.btn_main, self.btn_skip):
            b.configure(state="normal")
        if messagebox.askyesno(version.APP_NAME, f"The update could not be installed.\n\n{exc}"
                               "\n\nOpen the download page instead?", parent=self):
            self.open_download()
