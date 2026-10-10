#!/usr/bin/env python3
#
# gui_help.py
# 2026-10-10
# Version: v1.0.0
#
# PURPOSE:
# The GUI's Help menu: a built-in help window (short guides, keyboard
# shortcuts, troubleshooting), the About window (version, license, links,
# and the details to paste into a problem report), and the update check
# (manual, or automatic once a day when the user turned it on).

import datetime
import platform
import sys
import threading
import webbrowser

import tkinter as tk
from tkinter import messagebox, ttk

import updates
import version

TOPICS = [
    ("Getting started", """\
1. Folders. Put your screen recordings (.mp4, .mov, or .mkv) in the source folder, or choose another folder with Browse. Screenshots go to the output folder, one subfolder per recording.

2. Preset. Pick the kind of recording, for example Installer wizard, General desktop use, Web console, or Terminal. The preset fills in all the detection settings.

3. Process. Click Process All, or select some videos and click Process Selected. Progress shows at the bottom and in the Log tab.

4. Review. Select a processed video to open its steps in the Steps tab. Reorder, delete, crop, blur, and write a caption for each step, then click Save Changes.

5. Export. Fill in the document title, version, and author, then export to HTML, Word, or PDF.

The original screenshots are always kept, so every edit can be changed again later."""),
    ("Presets", """\
A preset is a named set of detection settings for one kind of recording:

- Installer wizard: the defaults, for setup wizards and settings dialogs.
- General desktop use: opening apps, browsing files, and flipping through menus. No blurring and no red boxes.
- Web console: admin portals and web apps; ignores spinners and slow pages.
- Terminal / command line: catches small text changes, merges typing.
- Remote desktop / VM console: ignores compression noise and lag.
- Forms and spreadsheets: small field changes, one step per entry.
- Slideshow / presentation: one screenshot per slide, no red boxes.
- Video meeting / screen share: ignores webcam movement, keeps blurring.
- Fast clicking: short pauses between actions.

Too many screenshots? Lower the sensitivity. Too few? Raise it. Save your own settings with Save As next to the preset list; saved presets work on the command line too (--preset NAME)."""),
    ("Editing steps", """\
In the Steps tab:

- Up and Down page through the steps (from the picture or the buttons). Ctrl+Up and Ctrl+Down move the selected step. Delete removes it; Restore Deleted brings removed steps back.
- Caption: type what the reader should do in this step.
- Crop: drag a rectangle on the picture to keep only part of the screen, for all steps or just this one.
- Highlight: the red box shows what changed since the previous step. Switch it off for the whole recording or for one step.
- Show Screenshot or Original frame to compare the edited picture with the untouched capture.
- Save Changes re-renders the screenshots and steps.md from the originals. Discard Changes goes back to the last save.
- Play in VLC opens the recording just before the selected step."""),
    ("Blurring sensitive information", """\
With Tesseract OCR installed, the tool reads the text in each screenshot and blurs passwords, keys, IP addresses, and email addresses automatically. An unblurred copy of every screenshot is kept in the unredacted folder, so nothing is lost.

- Add Blur Box: drag a rectangle over anything else to hide.
- Un-blur / Re-blur: click a blurred area to switch it off (or back on).
- Also blur (in the settings): your own patterns, for example a domain name or ticket prefix, separated by semicolons.
- Exports use the blurred screenshots unless you tick Unblurred copy.

Always look through the screenshots before sharing them: automatic blurring finds text it can read, not everything sensitive."""),
    ("Exporting", """\
Export turns the saved steps into one document:

- HTML: a single file with the screenshots built in. Works everywhere.
- Word (.docx): needs Pandoc.
- PDF: needs Microsoft Edge, Google Chrome, or Chromium.

Files are written to the export folder inside the recording's output folder; Open Exports shows it. Unsaved edits are saved first."""),
    ("Keyboard shortcuts", """\
Up / Down            Previous / next step (Steps tab)
Ctrl+Up / Ctrl+Down  Move the selected step up / down
Delete               Delete the selected step
Esc                  Cancel drawing a crop or blur box
Double-click a step  Open the screenshot
Double-click a video Open its output folder
F1                   This help"""),
    ("Troubleshooting", """\
- "FFmpeg not found": install it with winget install --id Gyan.FFmpeg -e, then restart the app. FFmpeg does all the video work and is required.
- No automatic blurring: install Tesseract OCR (winget install --id UB-Mannheim.TesseractOCR -e).
- Word export unavailable: install Pandoc (winget install --id JohnMacFarlane.Pandoc -e).
- Too many or too few screenshots: try another preset, or change Sensitivity.
- Something else: the Log tab and screencap.log in the output folder show what happened. Help > Report a Problem opens the issue form on GitHub; Help > About can copy the details it asks for."""),
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
        self.topics = tk.Listbox(body, width=28, exportselection=False, activestyle="none")
        for name, _ in TOPICS:
            self.topics.insert("end", name)
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
        self.topics.bind("<<ListboxSelect>>", lambda e: self.show(self.topics.curselection()))
        self.bind("<Escape>", lambda e: self.destroy())
        if hasattr(app, "theme"):
            app.theme.style_widgets(self)
        self.topics.selection_set(topic)
        self.show((topic,))

    def show(self, selection):
        if not selection:
            return
        name, body = TOPICS[selection[0]]
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("end", name + "\n", "h")
        self.text.insert("end", body, "mono" if name == "Keyboard shortcuts" else ())
        self.text.configure(state="disabled")


def details_text(app):
    """Version and environment details for problem reports. Paths are left
    out on purpose: they can contain the Windows user name."""
    def found(tool):
        return "found" if tool else "not found"
    lines = [
        f"{version.APP_NAME} v{version.RELEASE} (built {version.RELEASE_DATE})",
        f"Install type: {updates.install_kind()}",
        f"Operating system: {platform.platform()}",
        f"Python: {platform.python_version()} ({'packaged' if getattr(sys, 'frozen', False) else 'installed'})",
        f"Tk: {tk.TkVersion}",
        f"FFmpeg: {found(app.ffmpeg)}, Tesseract OCR: {found(app.tesseract)}, "
        f"Pandoc: {found(app.pandoc)}, PDF browser: {found(app.browser)}, VLC: {found(app.vlc)}, "
        f"Speech recognition: {found(app.whisper_python)}",
    ]
    return "\n".join(lines)


class AboutWindow(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app.root)
        self.app = app
        self.title(f"About {version.APP_NAME}")
        self.resizable(False, False)
        self.transient(app.root)
        body = ttk.Frame(self, padding=18)
        body.pack(fill="both", expand=True)
        icon = getattr(app.root, "_about_icon", None)
        if icon is not None:
            ttk.Label(body, image=icon).grid(row=0, column=0, rowspan=3, sticky="n", padx=(0, 16))
        ttk.Label(body, text=version.APP_NAME, style="Title.TLabel").grid(row=0, column=1, sticky="w")
        ttk.Label(body, text=f"Version {version.RELEASE}, built {version.RELEASE_DATE}",
                  style="Muted.TLabel").grid(row=1, column=1, sticky="w")
        ttk.Label(body, wraplength=420, justify="left", text=(
            "Turns screen recordings into step-by-step screenshot documentation. "
            "Free and open source under the MIT License. Everything runs on this PC; "
            "nothing is sent anywhere unless you ask for it (exports you share, the "
            "update check).\n\nCopyright (c) 2026 ILikeHostingServices. Uses FFmpeg, and "
            "optionally Tesseract OCR, Pandoc, VLC, and faster-whisper, which are separate "
            "programs with their own licenses.")).grid(row=2, column=1, sticky="w", pady=(10, 0))
        links = ttk.Frame(body)
        links.grid(row=3, column=0, columnspan=2, sticky="w", pady=(14, 0))
        for text, url in (("Project on GitHub", updates.REPO_URL),
                          ("Release Notes", updates.RELEASES_URL),
                          ("License", f"{updates.REPO_URL}/blob/main/LICENSE"),
                          ("Privacy", f"{updates.REPO_URL}/blob/main/CODE_SIGNING_POLICY.md#privacy")):
            ttk.Button(links, text=text, style="Link.TButton",
                       command=lambda u=url: app.open_url(u)).pack(side="left", padx=(0, 6))
        ttk.Label(body, text="Details for problem reports:").grid(
            row=4, column=0, columnspan=2, sticky="w", pady=(14, 2))
        self.details = tk.Text(body, height=6, width=70, wrap="word", relief="flat",
                               highlightthickness=1, padx=8, pady=6)
        self.details.insert("1.0", details_text(app))
        self.details.configure(state="disabled")
        self.details.grid(row=5, column=0, columnspan=2, sticky="ew")
        bar = ttk.Frame(body)
        bar.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        ttk.Button(bar, text="Copy Details", command=self.copy).pack(side="left")
        ttk.Button(bar, text="Check for Updates",
                   command=lambda: app.check_for_updates(manual=True)).pack(side="left", padx=6)
        ttk.Button(bar, text="Close", command=self.destroy).pack(side="right")
        self.bind("<Escape>", lambda e: self.destroy())
        if hasattr(app, "theme"):
            app.theme.style_widgets(self)

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
        if manual:
            self.app.set_status("Checking for updates...")

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
            app.set_status("Update check failed.")
            if manual:
                messagebox.showwarning(version.APP_NAME, f"Could not check for updates.\n\n{result}",
                                       parent=app.root)
            return
        if not updates.is_newer(result["version"]):
            app.set_status(f"You have the latest version (v{version.RELEASE}).")
            if manual:
                messagebox.showinfo(version.APP_NAME, f"You have the latest version, "
                                    f"v{version.RELEASE}.", parent=app.root)
            return
        if not manual and app.settings_extra.get("skip_version") == result["version"]:
            return
        app.set_status(f"Version {result['version']} is available.")
        notes = updates.release_notes_excerpt(result["notes"])
        answer = messagebox.askyesnocancel(
            version.APP_NAME,
            f"Version {result['version']} is available (released {result['published']}). "
            f"You have v{version.RELEASE}.\n\n{notes}\n\n{updates.how_to_update()}\n\n"
            "Open the download now?\n(Yes: download. No: remind me later. "
            "Cancel: skip this version.)", parent=app.root)
        if answer:
            app.open_url(updates.download_for(result))
        elif answer is None:
            app.settings_extra["skip_version"] = result["version"]

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
