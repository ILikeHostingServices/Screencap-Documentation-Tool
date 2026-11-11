#!/usr/bin/env python3
#
# gui_archive.py
# 2026-11-11
# Version: v1.2.0
#
# PURPOSE:
# The GUI side of archive.py: File > Archive Selected Recordings (also on
# the right-click menu of the Recordings list) packs each selected
# recording, with its screenshots, captions, and exports, into one .zip in
# Output/Archived recordings and takes it off the list; the Archived
# Recordings window lists the archives and restores or deletes them. The
# work runs in the background; results come back through the app's queue.

import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

import archive
from i18n import N_, _
import region
import screencap as sc
import stepdoc
import version

SHRINK_KEY = "archive_shrink"


def size_text(n):
    for unit in ("bytes", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f} {unit}" if unit == "bytes" else f"{n:.1f} {unit}"
        n /= 1024


def folders(app):
    return (Path(app.v_source.get()).expanduser().resolve(),
            Path(app.v_output.get()).expanduser().resolve())


def archive_selected(app):
    """Ask, then archive the selected recordings in the background."""
    if app.worker and app.worker.is_alive():
        return
    sel = [i for i in app.tree.selection() if i in app.videos]
    if not sel:
        messagebox.showinfo(version.APP_NAME, _("Select one or more recordings to archive "
                            "(Ctrl+click or Shift+click for several)."), parent=app.root)
        return
    shrink = bool(app.settings_extra.get(SHRINK_KEY, True))
    which = (_('Archive "{name}"?').format(name=app.tree.item(sel[0], "text"))
             if len(sel) == 1 else _("Archive these {n} recordings?").format(n=len(sel)))
    if not messagebox.askyesno(
            version.APP_NAME,
            which + "\n\n"
            + _("The recording, its screenshots, captions, and exports are packed into one "
                "file in the \"{folder}\" folder in your output folder, and taken off the "
                "list.").format(folder=archive.ARCHIVE_DIR_NAME)
            + (" " + _("The video is re-encoded to take less space.") if shrink else "")
            + "\n\n" + _("Bring it back any time with File > Archived Recordings."),
            parent=app.root):
        return
    if app.editor_iid in sel and not app.editor.confirm_discard():
        return
    if app.editor_iid in sel:
        app.editor_iid = None
        app.editor.load(None, None)
    source, output = folders(app)
    jobs = [(iid, *app.videos[iid]) for iid in sel]
    ffmpeg = app.ffmpeg or sc.find_tool("ffmpeg")   # None: archive without shrinking
    app.cancel.clear()
    app.set_running(True)

    def run():
        done, failed = 0, []
        for n, (iid, video, out_dir) in enumerate(jobs):
            if app.cancel.is_set():
                break
            app.q.put(("row", iid, N_("Archiving"), None))
            try:
                archive.archive_recording(
                    video, out_dir, source, output, ffmpeg=ffmpeg, shrink=shrink,
                    cancel=app.cancel,
                    progress=lambda f, text, n=n: app.q.put(
                        ("status", text + " " + _("({n} of {total}, {percent}%)").format(
                            n=n + 1, total=len(jobs), percent=f"{f * 100:.0f}"))))
                done += 1
            except stepdoc.Cancelled:
                break
            except Exception as exc:   # report and go on with the next one
                failed.append(f"{video.name}: {exc}")
        app.q.put(("call", lambda: finished(app, done, failed)))

    app.worker = threading.Thread(target=run, daemon=True)
    app.worker.start()


def finished(app, done, failed):
    app.set_running(False)
    app.refresh_videos()
    app.set_status(_("Archived {n} recording(s).").format(n=done)
                   + (" " + _("{n} failed.").format(n=len(failed)) if failed else ""))
    if failed:
        messagebox.showerror(version.APP_NAME, _("Some recordings were not archived (nothing "
                                                 "of theirs was deleted):") + "\n\n"
                             + "\n".join(failed), parent=app.root)


class ArchiveWindow(tk.Toplevel):
    """The archived recordings, with Restore, Delete, and Open Folder."""

    def __init__(self, app):
        super().__init__(app.root)
        self.app = app
        self.title(_("Archived Recordings"))
        self.transient(app.root)
        self.minsize(560, 320)
        body = ttk.Frame(self, padding=(22, 18))
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=1)
        body.rowconfigure(2, weight=1)
        ttk.Label(body, text=_("Archived Recordings"), style="Heading.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w")
        self.v_where = tk.StringVar()
        ttk.Label(body, textvariable=self.v_where, style="Muted.TLabel", wraplength=520,
                  justify="left").grid(row=1, column=0, columnspan=2, sticky="w", pady=(2, 10))
        self.tree = ttk.Treeview(body, columns=("archived", "steps", "size"),
                                 selectmode="extended", height=10)
        for col, text, width, anchor in (("#0", _("Recording"), 220, "w"),
                                         ("archived", _("Archived"), 140, "w"),
                                         ("steps", _("Steps"), 60, "center"),
                                         ("size", _("Size"), 80, "e")):
            self.tree.heading(col, text=text, anchor=anchor)
            self.tree.column(col, width=width, anchor=anchor, stretch=(col == "#0"))
        self.tree.grid(row=2, column=0, sticky="nsew")
        sb = ttk.Scrollbar(body, orient="vertical", command=self.tree.yview)
        sb.grid(row=2, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.bind("<Double-1>", lambda e: self.restore())

        self.v_shrink = tk.BooleanVar(value=bool(app.settings_extra.get(SHRINK_KEY, True)))
        ttk.Checkbutton(body, text=_("Shrink videos when archiving (smaller files, slightly "
                                   "lower picture quality)"), variable=self.v_shrink,
                        command=self.save_shrink).grid(row=3, column=0, columnspan=2,
                                                       sticky="w", pady=(10, 0))
        btns = ttk.Frame(body)
        btns.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(14, 0))
        ttk.Button(btns, text=_("Open Folder"), command=self.open_folder).pack(side="left")
        ttk.Button(btns, text=_("Delete..."), command=self.delete).pack(side="left", padx=(8, 0))
        ttk.Button(btns, text=_("Close"), command=self.destroy).pack(side="right")
        self.btn_restore = ttk.Button(btns, text=_("Restore"), style="Accent.TButton",
                                      command=self.restore)
        self.btn_restore.pack(side="right", padx=(0, 8))
        self.bind("<Escape>", lambda e: self.destroy())
        if hasattr(app, "theme"):
            app.theme.style_widgets(self)
        self.load()
        self.update_idletasks()     # centered over the main window
        root = app.root
        x = root.winfo_rootx() + (root.winfo_width() - self.winfo_reqwidth()) // 2
        y = root.winfo_rooty() + (root.winfo_height() - self.winfo_reqheight()) // 3
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")

    def folder(self):
        return archive.archive_dir(folders(self.app)[1])

    def load(self):
        self.tree.delete(*self.tree.get_children())
        self.archives = {}
        found = archive.list_archives(self.folder()) if self.folder().is_dir() else []
        for path, manifest in found:
            iid = self.tree.insert("", "end", text=manifest.get("recording", path.stem),
                                   values=(region.format_stored(manifest.get("archived", "")),
                                           manifest.get("steps", ""),
                                           size_text(path.stat().st_size)))
            self.archives[iid] = path
        total = sum(p.stat().st_size for p in self.archives.values())
        self.v_where.set(
            _("{n} archive(s), {size}, in {folder}. Restore puts the recording and its "
              "screenshots back in your recordings and output folders.").format(
                n=len(found), size=size_text(total), folder=self.folder()) if found else
            _("Nothing archived yet. Archive recordings from the File menu or by "
              "right-clicking them in the list. They are kept in {folder}.").format(
                folder=self.folder()))

    def selected(self):
        return [self.archives[i] for i in self.tree.selection() if i in self.archives]

    def save_shrink(self):
        self.app.settings_extra[SHRINK_KEY] = self.v_shrink.get()
        self.app.save_settings()

    def open_folder(self):
        self.folder().mkdir(parents=True, exist_ok=True)
        self.app.open_path(self.folder())

    def restore(self):
        paths = self.selected()
        if not paths or (self.app.worker and self.app.worker.is_alive()):
            return
        source, output = folders(self.app)
        self.configure(cursor="watch")
        self.btn_restore.configure(state="disabled")

        def run():
            restored, failed = [], []
            for p in paths:
                try:
                    restored.append(archive.restore_recording(p, source, output)[0])
                except Exception as exc:
                    failed.append(f"{p.name}: {exc}")
            self.app.q.put(("call", lambda: self.restored(restored, failed)))

        self.app.worker = threading.Thread(target=run, daemon=True)
        self.app.worker.start()

    def restored(self, restored, failed):
        if self.winfo_exists():
            self.configure(cursor="")
            self.btn_restore.configure(state="normal")
            self.load()
        self.app.refresh_videos()
        self.app.set_status(_("Restored {n} recording(s).").format(n=len(restored)))
        if failed:
            messagebox.showerror(self.version.APP_NAME, _("Some archives were not restored:")
                                 + "\n\n" + "\n".join(failed), parent=self)

    def delete(self):
        paths = self.selected()
        if not paths:
            return
        if not messagebox.askyesno(
                self.version.APP_NAME,
                _("Delete {n} archive(s) for good?\n\nThe recordings, screenshots, and captions "
                  "in them cannot be brought back.").format(n=len(paths)), icon="warning", parent=self):
            return
        for p in paths:
            p.unlink(missing_ok=True)
        self.load()
