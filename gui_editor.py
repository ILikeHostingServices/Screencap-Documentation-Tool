#!/usr/bin/env python3
#
# gui_editor.py
# 2026-10-03
# Version: v1.8.0
#
# PURPOSE:
# The "Steps" tab of the GUI: review and edit the steps of one processed
# recording. Reorder, delete (and restore) steps, write a caption for each
# one, then Save to re-render the screenshots and regenerate steps.md from
# the untouched originals. The red "what changed" box can be switched on or
# off for the whole recording or for a single step, screenshots can be
# cropped by dragging a rectangle on the original frame, and sensitive areas
# can be blurred (detected automatically, or drawn by hand) with an
# unblurred copy kept alongside. Finished steps export to HTML, Word, or PDF,
# Play in VLC opens the recording just before the selected step, and
# Captions From Narration fills empty captions from what was said.

import copy
import threading
from pathlib import Path

import tkinter as tk
from tkinter import messagebox, ttk

import export
import player
import redact
import stepdoc
import transcribe


class StepEditor(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=6)
        self.app = app              # main App: ffmpeg, temp_dir, root, open_path
        self.doc = None
        self.out_dir = None
        self.video = None
        self.dirty = False
        self.preview_image = None
        self.preview_job = None
        self.render_thread = None
        self.v_info = tk.StringVar(value="Select a processed video to edit its steps.")
        self.v_title = tk.StringVar(value="")
        self.v_view = tk.StringVar(value="final")
        self.v_dirty = tk.StringVar(value="")
        self.v_removed = tk.StringVar(value="")
        self.v_hl_doc = tk.BooleanVar(value=True)
        self.v_hl_step = tk.BooleanVar(value=True)
        self.v_redact_doc = tk.BooleanVar(value=True)
        self.v_redact_step = tk.BooleanVar(value=True)
        self.v_doc_title = tk.StringVar(value="")
        self.v_doc_version = tk.StringVar(value="")
        self.v_doc_author = tk.StringVar(value="")
        self.v_export_unredacted = tk.BooleanVar(value=False)
        self._loading_meta = False
        self._loading_caption = False
        self.view_map = None        # (scale, x offset, y offset) of the original-frame view
        self.draw = None            # active rectangle tool: dict(kind, scope, start, item)
        self.build()

    # ------------------------------------------------------------------ UI

    def build(self):
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        top = ttk.Frame(self)
        top.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        ttk.Label(top, textvariable=self.v_title, font=("TkDefaultFont", 10, "bold")).pack(side="left")
        ttk.Label(top, textvariable=self.v_dirty, foreground="#b06000").pack(side="left", padx=10)
        ttk.Label(top, textvariable=self.v_removed, foreground="gray").pack(side="left", padx=4)
        self.options_bar = ttk.Frame(top)   # per-recording toggles
        self.options_bar.pack(side="right")
        ttk.Checkbutton(self.options_bar, text="Blur sensitive info", variable=self.v_redact_doc,
                        command=self.toggle_doc_redact).pack(side="left", padx=4)
        ttk.Checkbutton(self.options_bar, text="Highlight changes", variable=self.v_hl_doc,
                        command=self.toggle_doc_highlight).pack(side="left", padx=4)

        left = ttk.Frame(self)
        left.grid(row=1, column=0, sticky="ns")
        left.rowconfigure(0, weight=1)
        self.step_list = tk.Listbox(left, width=30, exportselection=False, activestyle="none",
                                    font=("Consolas", 9) if self.app.is_windows else ("Courier", 9))
        self.step_list.grid(row=0, column=0, columnspan=2, sticky="ns")
        sb = ttk.Scrollbar(left, orient="vertical", command=self.step_list.yview)
        sb.grid(row=0, column=2, sticky="ns")
        self.step_list.configure(yscrollcommand=sb.set)
        self.step_list.bind("<<ListboxSelect>>", lambda e: self.on_select())
        self.step_list.bind("<Double-1>", lambda e: self.open_image())
        self.step_list.bind("<Delete>", lambda e: self.delete_step())
        # Ctrl+Up/Down reorder; plain Up/Down page through steps (see on_arrow)
        self.step_list.bind("<Control-Up>", lambda e: self.move(-1) or "break")
        self.step_list.bind("<Control-Down>", lambda e: self.move(1) or "break")
        top = self.winfo_toplevel()
        top.bind("<Up>", lambda e: self.on_arrow(e, -1), add="+")
        top.bind("<Down>", lambda e: self.on_arrow(e, 1), add="+")
        self.step_buttons = []
        for r, (text, cmd) in enumerate((("Move Step Up", lambda: self.move(-1)),
                                         ("Move Step Down", lambda: self.move(1)),
                                         ("Delete Step", self.delete_step),
                                         ("Restore Deleted", self.restore_deleted)), 1):
            b = ttk.Button(left, text=text, command=cmd)
            b.grid(row=(r + 1) // 2, column=(r + 1) % 2, sticky="ew", pady=(4, 0), padx=(0, 4))
            self.step_buttons.append(b)
        # Rows 1-2 hold the four buttons above; extra tools go from row 3
        self.tools_frame = ttk.Frame(left)
        self.tools_frame.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(6, 0))
        self.chk_hl_step = ttk.Checkbutton(self.tools_frame, text="Highlight this step",
                                           variable=self.v_hl_step,
                                           command=self.toggle_step_highlight)
        self.chk_hl_step.pack(anchor="w")
        ttk.Label(self.tools_frame, text="Crop (drag on the picture):").pack(anchor="w", pady=(8, 0))
        crop_row = ttk.Frame(self.tools_frame)
        crop_row.pack(fill="x")
        ttk.Button(crop_row, text="All Steps", command=lambda: self.begin_draw("crop", "all")
                   ).pack(side="left", fill="x", expand=True)
        ttk.Button(crop_row, text="This Step", command=lambda: self.begin_draw("crop", "step")
                   ).pack(side="left", fill="x", expand=True, padx=(4, 0))
        crop_row2 = ttk.Frame(self.tools_frame)
        crop_row2.pack(fill="x", pady=(4, 0))
        ttk.Button(crop_row2, text="No Crop Here", command=self.no_crop_step
                   ).pack(side="left", fill="x", expand=True)
        ttk.Button(crop_row2, text="Clear All Crops", command=self.clear_crops
                   ).pack(side="left", fill="x", expand=True, padx=(4, 0))
        ttk.Label(self.tools_frame, text="Blur (sensitive information):").pack(anchor="w", pady=(8, 0))
        ttk.Checkbutton(self.tools_frame, text="Blur this step", variable=self.v_redact_step,
                        command=self.toggle_step_redact).pack(anchor="w")
        blur_row = ttk.Frame(self.tools_frame)
        blur_row.pack(fill="x")
        ttk.Button(blur_row, text="Add Blur Box", command=lambda: self.begin_draw("blur", "step")
                   ).pack(side="left", fill="x", expand=True)
        ttk.Button(blur_row, text="Un-blur / Re-blur", command=self.begin_pick
                   ).pack(side="left", fill="x", expand=True, padx=(4, 0))
        ttk.Button(self.tools_frame, text="Re-scan All Steps for Sensitive Text",
                   command=self.rescan).pack(fill="x", pady=(4, 0))

        right = ttk.Frame(self)
        right.grid(row=1, column=1, sticky="nsew", padx=(6, 0))
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)
        viewbar = ttk.Frame(right)
        viewbar.grid(row=0, column=0, sticky="ew")
        ttk.Label(viewbar, text="Show:").pack(side="left")
        ttk.Radiobutton(viewbar, text="Screenshot", value="final", variable=self.v_view,
                        command=self.schedule_preview).pack(side="left", padx=4)
        ttk.Radiobutton(viewbar, text="Original frame", value="original", variable=self.v_view,
                        command=self.schedule_preview).pack(side="left", padx=4)
        self.viewbar = viewbar
        self.canvas = tk.Canvas(right, background="#202020", highlightthickness=0)
        self.canvas.grid(row=1, column=0, sticky="nsew", pady=(4, 0))
        self.canvas.bind("<Configure>", lambda e: self.schedule_preview())
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        # Clicking the picture takes the keyboard, so Up/Down page from there
        self.canvas.bind("<ButtonPress-1>", lambda e: self.canvas.focus_set(), add="+")
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.winfo_toplevel().bind("<Escape>", lambda e: self.cancel_draw(), add="+")

        info = ttk.Label(right, textvariable=self.v_info, anchor="w", justify="left")
        info.grid(row=2, column=0, sticky="ew", pady=(4, 0))
        right.bind("<Configure>", lambda e: info.configure(wraplength=max(200, e.width - 10)))
        cap = ttk.Frame(right)
        cap.grid(row=3, column=0, sticky="ew", pady=(4, 0))
        cap.columnconfigure(1, weight=1)
        ttk.Label(cap, text="Caption:").grid(row=0, column=0, sticky="nw", padx=(0, 6))
        self.caption = tk.Text(cap, height=3, wrap="word", undo=True)
        self.caption.grid(row=0, column=1, sticky="ew")
        self.caption.bind("<<Modified>>", self.on_caption_modified)

        docrow = ttk.Frame(right)
        docrow.grid(row=4, column=0, sticky="ew", pady=(6, 0))
        for col, (label, var, width) in enumerate((("Title:", self.v_doc_title, 24),
                                                   ("Version:", self.v_doc_version, 7),
                                                   ("Author:", self.v_doc_author, 12))):
            ttk.Label(docrow, text=label).pack(side="left", padx=(8 if col else 0, 2))
            ttk.Entry(docrow, textvariable=var, width=width).pack(side="left")
            var.trace_add("write", lambda *a: self.on_meta_changed())
        exprow = ttk.Frame(right)
        exprow.grid(row=5, column=0, sticky="ew", pady=(4, 0))
        ttk.Label(exprow, text="Export:").pack(side="left")
        self.export_buttons = []
        for fmt, text in (("html", "HTML"), ("docx", "Word"), ("pdf", "PDF")):
            b = ttk.Button(exprow, text=text, width=6, command=lambda f=fmt: self.export(f))
            b.pack(side="left", padx=(4, 0))
            self.export_buttons.append(b)
        ttk.Checkbutton(exprow, text="Unblurred copy",
                        variable=self.v_export_unredacted).pack(side="left", padx=6)
        ttk.Button(exprow, text="Open Exports", command=self.open_export_folder
                   ).pack(side="left", padx=(4, 0))

        bar = ttk.Frame(self)
        bar.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        ttk.Button(bar, text="< Prev", command=lambda: self.step_by(-1)).pack(side="left")
        ttk.Button(bar, text="Next >", command=lambda: self.step_by(1)).pack(side="left", padx=4)
        ttk.Button(bar, text="Open Image", command=self.open_image).pack(side="left", padx=4)
        self.action_bar = ttk.Frame(bar)
        self.action_bar.pack(side="left", padx=4)
        ttk.Button(self.action_bar, text="Play in VLC", command=self.play).pack(side="left")
        self.btn_narration = ttk.Button(self.action_bar, text="Captions From Narration",
                                        command=self.captions_from_narration)
        self.btn_narration.pack(side="left", padx=(4, 0))
        self.btn_save = ttk.Button(bar, text="Save Changes", command=self.save)
        self.btn_save.pack(side="right")
        ttk.Button(bar, text="Discard Changes", command=self.discard).pack(side="right", padx=4)
        ttk.Button(bar, text="steps.md", command=self.open_index).pack(side="right", padx=4)
        ttk.Button(bar, text="Folder", command=self.open_folder).pack(side="right")

    # ------------------------------------------------------------- loading

    def load(self, video, out_dir):
        """Show the steps of one recording. Returns False if the user chose to
        keep editing the current one instead."""
        if out_dir == self.out_dir and video == self.video:
            return True
        if not self.confirm_discard():
            return False
        self.video, self.out_dir = video, out_dir
        self.reload()
        return True

    def reload(self):
        self.doc = stepdoc.load(self.out_dir) if self.out_dir else None
        self.set_dirty(False)
        if self.doc is None:
            name = self.video.name if self.video else ""
            self.show_message(f"{name} has not been processed yet." if name else
                              "Select a processed video to edit its steps.")
            return
        self.v_title.set(self.doc.get("document", {}).get("title", ""))
        self.v_hl_doc.set(self.doc.get("highlight", True))
        self.v_redact_doc.set(self.doc.get("redact", True))
        meta = export.metadata(self.doc)
        self._loading_meta = True
        self.v_doc_title.set(meta["title"])
        self.v_doc_version.set(meta["version"])
        self.v_doc_author.set(meta["author"])
        self._loading_meta = False
        try:
            stepdoc.ensure_frame_size(self.out_dir, self.doc, self.app.ffmpeg)
        except Exception as exc:
            self.app.log_error(f"Could not read the frame size: {exc}")
        self.refresh_list(0)

    def show_message(self, text):
        self.doc = None
        self.v_title.set("")
        self.v_removed.set("")
        self.step_list.delete(0, "end")
        self.canvas.delete("all")
        self._set_caption("")
        self.v_info.set(text)

    def refresh_list(self, select=None):
        self.step_list.delete(0, "end")
        for i, step in enumerate(self.doc["steps"], 1):
            caption = (step.get("caption") or "").strip().replace("\n", " ")
            self.step_list.insert("end", f"{i:03d}  {stepdoc.fmt_ts(step['time'])}  {caption[:30]}")
        deleted = len(self.doc["deleted_steps"])
        if select is not None and self.doc["steps"]:
            select = max(0, min(select, len(self.doc["steps"]) - 1))
            self.step_list.selection_set(select)
            self.step_list.see(select)
            self.on_select()
        elif not self.doc["steps"]:
            self.canvas.delete("all")
            self._set_caption("")
            self.v_info.set("No steps. Use Restore Deleted to bring steps back.")
        dups = sum(1 for d in self.doc["deleted_steps"] if d.get("deleted_reason") == "duplicate")
        extra = f", {dups} duplicate(s)" if dups else ""
        self.v_removed.set(f"{deleted} removed{extra} (Restore Deleted brings them back)"
                           if deleted else "")

    # ------------------------------------------------------------ editing

    def current_index(self):
        sel = self.step_list.curselection()
        return sel[0] if sel and self.doc and sel[0] < len(self.doc["steps"]) else None

    def current_step(self):
        i = self.current_index()
        return self.doc["steps"][i] if i is not None else None

    def set_dirty(self, dirty=True):
        self.dirty = dirty
        self.v_dirty.set("Unsaved changes" if dirty else "")

    def on_select(self):
        step = self.current_step()
        if step is None:
            return
        i = self.current_index()
        # Keep the list's keyboard cursor on the selected step, so arrow keys
        # continue from here after a button or Prev/Next changed the step
        self.step_list.activate(i)
        info = f"Step {i + 1} of {len(self.doc['steps'])} at {stepdoc.fmt_ts(step['time'])}"
        if step.get("still_from") is not None and step.get("still_to") is not None:
            info += (f" | screen stable {stepdoc.fmt_ts(step['still_from'])} to "
                     f"{stepdoc.fmt_ts(step['still_to'])}")
        if "change_box" in step and not step["change_box"]:
            info += " | no highlight (first step, nothing changed, or whole screen changed)"
        crop = stepdoc.effective_crop(step, self.doc)
        if crop:
            own = " (this step only)" if isinstance(step.get("crop"), list) else ""
            info += f" | cropped to {crop[2]}x{crop[3]}{own}"
        if stepdoc.effective(step, self.doc, "redact"):
            self.scan_if_needed(step)
            n = len(stepdoc.redaction_boxes(step, self.doc))
            if n:
                info += f" | {n} area(s) blurred"
        self.v_redact_step.set(bool(stepdoc.effective(step, self.doc, "redact")))
        self.v_info.set(info)
        self.v_hl_step.set(bool(stepdoc.effective(step, self.doc, "highlight")))
        self._set_caption(step.get("caption", ""))
        self.schedule_preview()

    def _set_caption(self, text):
        self._loading_caption = True
        self.caption.delete("1.0", "end")
        self.caption.insert("1.0", text or "")
        self.caption.edit_modified(False)
        self._loading_caption = False

    def on_caption_modified(self, _event=None):
        if self._loading_caption or not self.caption.edit_modified():
            return
        self.caption.edit_modified(False)
        step = self.current_step()
        if step is None:
            return
        text = self.caption.get("1.0", "end").strip()
        if text != (step.get("caption") or ""):
            step["caption"] = text
            self.set_dirty()
            i = self.current_index()
            label = f"{i + 1:03d}  {stepdoc.fmt_ts(step['time'])}  {text.replace(chr(10), ' ')[:30]}"
            self.step_list.delete(i)
            self.step_list.insert(i, label)
            self.step_list.selection_set(i)

    def step_by(self, delta):
        if not self.doc or not self.doc["steps"]:
            return
        i = self.current_index()
        i = 0 if i is None else max(0, min(i + delta, len(self.doc["steps"]) - 1))
        self.step_list.selection_clear(0, "end")
        self.step_list.selection_set(i)
        self.step_list.see(i)
        self.on_select()

    def on_arrow(self, event, delta):
        """Up/Down page through the steps from anywhere in the Steps tab, so
        they still work after clicking a button or the picture. The step list
        and text fields keep their own arrow-key behavior."""
        if not self.winfo_ismapped() or not self.doc:
            return
        # The widget that received the key, not focus_get(): on Windows focus
        # can be left on a widget in the other tab, or be None while the
        # window is in the background
        target = event.widget
        if target is self.step_list or isinstance(target, (tk.Text, tk.Entry, ttk.Entry,
                                                           ttk.Combobox)):
            return
        if isinstance(target, ttk.Treeview) and target.winfo_viewable():
            return                        # a visible list keeps its own arrows
        self.step_by(delta)

    def move(self, delta):
        """Reorder: the selected step moves and stays selected, so the picture
        keeps showing the step you are moving."""
        i = self.current_index()
        if i is None:
            return
        j = stepdoc.move_step(self.doc, i, delta)
        if j != i:
            self.set_dirty()
            self.refresh_list(j)
            self.app.set_status(f"Moved the step from position {i + 1} to {j + 1}. "
                                "Use Up/Down (or < Prev / Next >) to look at other steps.")
        else:
            self.app.set_status("That step is already at the "
                                f"{'top' if delta < 0 else 'bottom'} of the list.")

    def delete_step(self):
        i = self.current_index()
        if i is None:
            return
        stepdoc.delete_step(self.doc, i)
        self.set_dirty()
        self.refresh_list(i)

    def restore_deleted(self):
        if not self.doc or not self.doc["deleted_steps"]:
            messagebox.showinfo(self.app.name, "There are no deleted steps to restore.",
                                parent=self.winfo_toplevel())
            return
        n = stepdoc.restore_deleted(self.doc)
        self.set_dirty()
        self.refresh_list(self.current_index() or 0)
        self.app.set_status(f"Restored {n} step(s). Click Save Changes to keep them.")

    def ensure_boxes(self):
        try:
            stepdoc.ensure_change_boxes(self.out_dir, self.doc, self.app.ffmpeg)
        except Exception as exc:
            self.app.log_error(f"Could not work out what changed: {exc}")

    def toggle_doc_highlight(self):
        if not self.doc:
            return
        self.doc["highlight"] = self.v_hl_doc.get()
        if self.doc["highlight"]:
            self.ensure_boxes()
        self.set_dirty()
        self.on_select()

    def toggle_step_highlight(self):
        step = self.current_step()
        if step is None:
            return
        step["highlight"] = self.v_hl_step.get()
        if step["highlight"]:
            self.ensure_boxes()
        self.set_dirty()
        self.schedule_preview()

    # -------------------------------------------------------------- export

    def on_meta_changed(self):
        if self._loading_meta or not self.doc:
            return
        meta = self.doc.setdefault("document", {})
        new = {"title": self.v_doc_title.get().strip(),
               "version": self.v_doc_version.get().strip(),
               "author": self.v_doc_author.get().strip()}
        if any(meta.get(k, "") != v for k, v in new.items()):
            meta.update(new)
            self.v_title.set(new["title"])
            self.set_dirty()

    def export(self, fmt):
        """Export the saved steps. Unsaved edits are saved first, so the
        document matches what the editor shows."""
        if not self.doc:
            return
        parent = self.winfo_toplevel()
        if self.dirty:
            if not messagebox.askyesno(self.app.name, "Save your changes before exporting?",
                                       parent=parent):
                return
            if not self.save(wait=True):
                return
        unredacted = self.v_export_unredacted.get()
        if unredacted and not messagebox.askyesno(
                self.app.name, "The unblurred screenshots may show passwords, keys, or "
                "internal addresses. Export them anyway? The file name will include "
                "UNREDACTED.", icon="warning", parent=parent):
            return
        doc, out_dir = self.doc, self.out_dir
        result = {}

        def work():
            try:
                result["path"] = export.export(out_dir, doc, fmt, unredacted,
                                               pandoc=self.app.pandoc, browser=self.app.browser)
            except Exception as exc:
                result["error"] = exc

        for b in self.export_buttons:
            b.configure(state="disabled")
        self.app.set_status(f"Exporting {fmt.upper()}...")
        thread = threading.Thread(target=work, daemon=True)
        thread.start()

        def check():
            if thread.is_alive():
                self.after(150, check)
                return
            for b in self.export_buttons:
                b.configure(state="normal")
            if "error" in result:
                self.app.log_error(f"Export failed: {result['error']}")
                messagebox.showerror(self.app.name, f"Export failed:\n{result['error']}",
                                     parent=parent)
                return
            self.app.set_status(f"Exported {result['path'].name}")
            self.app.open_path(result["path"])

        check()

    def open_export_folder(self):
        folder = self.out_dir / export.EXPORT_DIR if self.out_dir else None
        if folder and folder.is_dir():
            self.app.open_path(folder)
        elif self.out_dir:
            self.app.set_status("Nothing has been exported yet.")

    # ----------------------------------------------------------- redaction

    def scan_if_needed(self, step):
        """Scan one step for sensitive text right away (when it has never been
        scanned) so the preview shows the blur before saving."""
        if "auto_redactions" in step or not self.app.tesseract:
            return
        try:
            step["auto_redactions"] = redact.scan_image(
                self.app.tesseract, self.out_dir / step["original"], self.doc["width"],
                self.doc["height"], self.doc.get("redact_patterns", []))
        except Exception as exc:
            self.app.log_error(f"Text scan failed: {exc}")

    def toggle_doc_redact(self):
        if not self.doc:
            return
        self.doc["redact"] = self.v_redact_doc.get()
        if self.doc["redact"] and not self.app.tesseract:
            messagebox.showinfo(self.app.name, redact.TESSERACT_MISSING_HELP,
                                parent=self.winfo_toplevel())
        self.set_dirty()
        self.on_select()

    def toggle_step_redact(self):
        step = self.current_step()
        if step is None:
            return
        step["redact"] = self.v_redact_step.get()
        self.set_dirty()
        self.on_select()

    def rescan(self):
        """Forget earlier scan results and scan every step again on save
        (for example after Tesseract was installed). Hand-drawn boxes stay."""
        if not self.doc:
            return
        if not self.app.tesseract:
            messagebox.showinfo(self.app.name, redact.TESSERACT_MISSING_HELP,
                                parent=self.winfo_toplevel())
            return
        for step in self.doc["steps"]:
            step.pop("auto_redactions", None)
        self.set_dirty()
        self.save()

    def begin_pick(self):
        """Click a blur box on the original frame to switch it off or on.
        Hand-drawn boxes are removed instead."""
        if self.current_step() is None or not self.doc.get("width"):
            return
        self.draw = {"kind": "pick", "scope": "step", "start": None, "item": None}
        self.v_view.set("original")
        self.canvas.configure(cursor="hand2")
        self.render_preview()
        self.app.set_status("Click a blur box to switch it off (or back on). Esc cancels.")

    def pick_box(self, x, y):
        step = self.current_step()
        hits = []
        for r in step.get("auto_redactions") or []:
            bx, by, bw, bh = r["box"]
            if bx <= x <= bx + bw and by <= y <= by + bh:
                hits.append((bw * bh, "auto", r))
        for b in step.get("manual_redactions") or []:
            bx, by, bw, bh = b
            if bx <= x <= bx + bw and by <= y <= by + bh:
                hits.append((bw * bh, "manual", b))
        if not hits:
            self.app.set_status("No blur box there.")
            return
        _, kind, item = min(hits, key=lambda h: h[0])
        if kind == "auto":
            item["ignored"] = not item.get("ignored")
            self.app.set_status(f"{'Un-blurred' if item['ignored'] else 'Blurred again'}: "
                                f"{item.get('reason', 'detected text')}.")
        else:
            step["manual_redactions"].remove(item)
            self.app.set_status("Removed the hand-drawn blur box.")
        self.set_dirty()

    # -------------------------------------------------------- rectangles

    def begin_draw(self, kind, scope):
        """Start a rectangle tool. Rectangles are drawn on the original frame
        so they are stored in original-frame pixels."""
        if self.current_step() is None or not self.doc.get("width"):
            return
        self.draw = {"kind": kind, "scope": scope, "start": None, "item": None}
        self.v_view.set("original")
        self.canvas.configure(cursor="crosshair")
        self.render_preview()
        what = {"crop": "the area to keep", "blur": "the area to blur"}.get(kind, "the area")
        self.app.set_status(f"Drag a rectangle around {what}. Press Esc to cancel.")

    def cancel_draw(self):
        if self.draw:
            self.draw = None
            self.canvas.configure(cursor="")
            self.app.set_status("Cancelled.")
            self.schedule_preview()

    def on_press(self, event):
        if self.draw and self.view_map:
            if self.draw["kind"] == "pick":
                self.draw = None
                self.canvas.configure(cursor="")
                scale, ox, oy = self.view_map
                self.pick_box((event.x - ox) / scale, (event.y - oy) / scale)
                self.on_select()
                return
            self.draw["start"] = (event.x, event.y)

    def on_drag(self, event):
        if not self.draw or not self.draw["start"]:
            return
        if self.draw["item"]:
            self.canvas.delete(self.draw["item"])
        x0, y0 = self.draw["start"]
        self.draw["item"] = self.canvas.create_rectangle(x0, y0, event.x, event.y,
                                                         outline="#4FC3F7", width=2, dash=(6, 3))

    def on_release(self, event):
        if not self.draw or not self.draw["start"]:
            return
        draw, self.draw = self.draw, None
        self.canvas.configure(cursor="")
        scale, ox, oy = self.view_map
        x0, y0 = draw["start"]
        rect = [(min(x0, event.x) - ox) / scale, (min(y0, event.y) - oy) / scale,
                abs(event.x - x0) / scale, abs(event.y - y0) / scale]
        if rect[2] < 8 or rect[3] < 8:
            self.app.set_status("Rectangle too small; nothing changed.")
            self.schedule_preview()
            return
        rect = stepdoc.clamp_rect(rect, self.doc["width"], self.doc["height"])
        self.apply_rect(draw["kind"], draw["scope"], rect)

    def apply_rect(self, kind, scope, rect):
        step = self.current_step()
        if kind == "crop":
            if scope == "all":
                self.doc["crop"] = rect
            else:
                step["crop"] = rect
            self.app.set_status(f"Crop set to {rect[2]}x{rect[3]} at {rect[0]},{rect[1]}"
                                f"{' for all steps' if scope == 'all' else ' for this step'}.")
        elif kind == "blur":
            step.setdefault("manual_redactions", []).append(rect)
            if not stepdoc.effective(step, self.doc, "redact"):
                step["redact"] = True
            self.app.set_status("Blur box added.")
        self.set_dirty()
        self.v_view.set("final")
        self.on_select()

    def no_crop_step(self):
        step = self.current_step()
        if step is not None:
            step["crop"] = stepdoc.NO_CROP
            self.set_dirty()
            self.on_select()

    def clear_crops(self):
        if not self.doc:
            return
        self.doc["crop"] = None
        for step in self.doc["steps"]:
            step.pop("crop", None)
        self.set_dirty()
        self.on_select()

    # ------------------------------------------------------------- preview

    def schedule_preview(self):
        if self.preview_job:
            self.after_cancel(self.preview_job)
        self.preview_job = self.after(150, self.render_preview)

    def preview_size(self):
        return max(self.canvas.winfo_width(), 50), max(self.canvas.winfo_height(), 50)

    def render_preview(self):
        """Draw the selected step. "Screenshot" shows it as it will be saved,
        including unsaved edits; "Original frame" shows the untouched capture."""
        self.preview_job = None
        step = self.current_step()
        self.canvas.delete("all")
        if step is None:
            return
        w, h = self.preview_size()
        src = self.out_dir / step["original"]
        if not src.is_file():
            self.canvas.create_text(w // 2, h // 2, fill="white",
                                    text="Original image is missing (deleted or moved).")
            return
        filters = None
        if self.v_view.get() == "final":
            filters = stepdoc.build_filter(step, self.doc)
        scale = f"scale={w}:{h}:force_original_aspect_ratio=decrease"
        vf = f"{filters},{scale}" if filters else scale
        thumb = self.app.temp_dir / "preview.png"
        try:
            if not self.app.ffmpeg:
                raise RuntimeError("FFmpeg is required for previews")
            res = self.app.run([self.app.ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
                                "-i", str(src), "-vf", vf, "-frames:v", "1", str(thumb)])
            if res.returncode != 0:
                raise RuntimeError(res.stderr.strip()[-200:])
            self.preview_image = tk.PhotoImage(file=str(thumb))
            self.canvas.create_image(w // 2, h // 2, image=self.preview_image)
            self.view_map = None
            if self.v_view.get() == "original" and self.doc.get("width"):
                scale = self.preview_image.width() / self.doc["width"]
                self.view_map = (scale, (w - self.preview_image.width()) / 2,
                                 (h - self.preview_image.height()) / 2)
                self.draw_overlays(step)
        except Exception as exc:
            self.canvas.create_text(w // 2, h // 2, fill="white", width=w - 20,
                                    text=f"Preview unavailable: {exc}")

    def overlay(self, rect, color, label=None):
        scale, ox, oy = self.view_map
        x, y, w, h = rect
        x0, y0 = ox + x * scale, oy + y * scale
        self.canvas.create_rectangle(x0, y0, x0 + w * scale, y0 + h * scale,
                                     outline=color, width=2, dash=(6, 3))
        if label:   # above the box, so it does not cover what is inside
            above = y0 - 2 > 12
            self.canvas.create_text(x0, y0 - 2 if above else y0 + h * scale + 2,
                                    anchor="sw" if above else "nw", text=label, fill=color)

    def draw_overlays(self, step):
        """On the original frame, outline what will be applied: the crop
        (blue), the "what changed" box (red), detected text to blur (yellow,
        gray when switched off), and hand-drawn blur boxes (orange)."""
        crop = stepdoc.effective_crop(step, self.doc)
        if crop:
            self.overlay(crop, "#4FC3F7", "crop")
        for r in step.get("auto_redactions") or []:
            if r.get("ignored"):
                self.overlay(r["box"], "#9E9E9E", "not blurred")
            else:
                self.overlay(r["box"], "#FFD54F", r.get("reason"))
        for b in step.get("manual_redactions") or []:
            self.overlay(b, "#FF9800", "blur")
        if step.get("change_box") and stepdoc.effective(step, self.doc, "highlight"):
            self.overlay(step["change_box"], "#E53935")

    # ------------------------------------------------------------- saving

    def confirm_discard(self):
        if not self.dirty:
            return True
        answer = messagebox.askyesnocancel(
            self.app.name, "Save your changes to this recording's steps first?",
            parent=self.winfo_toplevel())
        if answer is None:
            return False
        if answer:
            return self.save(wait=True)
        return True

    def discard(self):
        if self.dirty and messagebox.askyesno(self.app.name, "Discard all unsaved changes?",
                                              parent=self.winfo_toplevel()):
            self.reload()

    def save(self, wait=False):
        """Re-render screenshots and write steps.md/steps.json in the
        background so the window stays responsive."""
        if not self.doc or (self.render_thread and self.render_thread.is_alive()):
            return False
        doc, out_dir = self.doc, self.out_dir
        result = {}

        def work():
            try:
                stepdoc.render(out_dir, doc, self.app.ffmpeg,
                               progress=lambda f, t: self.app.q.put(("status", t)),
                               tesseract=self.app.tesseract)
                result["ok"] = True
            except Exception as exc:
                result["error"] = exc

        self.btn_save.configure(state="disabled")
        self.app.set_status("Saving steps...")
        self.render_thread = threading.Thread(target=work, daemon=True)
        self.render_thread.start()
        if wait:
            self.render_thread.join()
            return self._after_save(result)
        self._poll_save(result)
        return True

    def _poll_save(self, result):
        if self.render_thread.is_alive():
            self.after(100, lambda: self._poll_save(result))
        else:
            self._after_save(result)

    def _after_save(self, result):
        self.btn_save.configure(state="normal")
        if "error" in result:
            self.app.log_error(f"Saving steps failed: {result['error']}")
            messagebox.showerror(self.app.name, f"Saving failed:\n{result['error']}",
                                 parent=self.winfo_toplevel())
            return False
        self.set_dirty(False)
        # Through the queue so it lands after any queued progress messages
        self.app.q.put(("status", f"Saved {len(self.doc['steps'])} step(s) to {self.out_dir.name}"))
        self.app.on_steps_saved(self.out_dir)
        return True

    # ---------------------------------------------------------- open files

    def open_image(self):
        step = self.current_step()
        if step is None:
            return
        path = self.out_dir / (step.get("file") or "")
        if not step.get("file") or not path.is_file() or self.dirty:
            path = self.out_dir / step["original"]
        if path.is_file():
            self.app.open_path(path)

    def source_video(self):
        """The recording this output came from: the one selected in the
        Videos list, or the path saved when it was processed."""
        if self.video and Path(self.video).is_file():
            return Path(self.video)
        saved = self.doc.get("source_path") if self.doc else None
        if saved and Path(saved).is_file():
            return Path(saved)
        return None

    def play(self):
        step = self.current_step()
        if step is None:
            return
        if not self.app.vlc:
            messagebox.showinfo(self.app.name, player.VLC_MISSING_HELP,
                                parent=self.winfo_toplevel())
            return
        video = self.source_video()
        if video is None:
            messagebox.showinfo(self.app.name, "The original recording was not found. It may "
                                "have been moved or deleted from the source folder.",
                                parent=self.winfo_toplevel())
            return
        start = player.start_time(step)
        try:
            player.open_at(self.app.vlc, video, start)
            self.app.set_status(f"Opened {video.name} in VLC at {stepdoc.fmt_ts(start)}")
        except OSError as exc:
            self.app.log_error(f"Could not start VLC: {exc}")

    def captions_from_narration(self):
        """Transcribe the recording and fill the captions that are still empty.
        The work runs on a copy; the result is applied here, on the Tk thread,
        and stays unsaved until Save Changes."""
        if not self.doc:
            return
        parent = self.winfo_toplevel()
        python = transcribe.find_python()
        if not python:
            messagebox.showinfo(self.app.name, transcribe.WHISPER_MISSING_HELP, parent=parent)
            return
        video = self.source_video()
        if video is None:
            messagebox.showinfo(self.app.name, "The original recording was not found. It may "
                                "have been moved or deleted from the source folder.",
                                parent=parent)
            return
        model = self.app.whisper_model()
        work_doc, out_dir, ffmpeg = copy.deepcopy(self.doc), self.out_dir, self.app.ffmpeg
        result = {}

        def work():
            try:
                result["summary"] = transcribe.transcribe(video, out_dir, work_doc, ffmpeg,
                                                          model, python)
            except Exception as exc:
                result["error"] = exc

        self.btn_narration.configure(state="disabled")
        self.app.set_status(f"Transcribing narration with the {model} model. The first "
                            "time, the model is downloaded, which can take a few minutes...")
        thread = threading.Thread(target=work, daemon=True)
        thread.start()

        def check():
            if thread.is_alive():
                self.after(250, check)
                return
            self.btn_narration.configure(state="normal")
            if "error" in result:
                self.app.log_error(f"Captions from narration failed: {result['error']}")
                messagebox.showerror(self.app.name, str(result["error"]), parent=parent)
                return
            if self.doc is None or self.out_dir != out_dir:
                return                      # another recording was opened meanwhile
            summary = result["summary"]
            filled = transcribe.apply(self.doc, summary["result"])
            self.doc["narration"] = work_doc.get("narration")
            if not summary["audio"]:
                text = "This recording has no audio, so there is no narration to use."
            elif not summary["segments"]:
                text = "No speech was found in this recording."
            else:
                text = (f"Filled {filled} empty caption(s) from {summary['segments']} spoken "
                        f"passage(s). Captions you typed were kept. Review them, then "
                        f"Save Changes. Full text: {transcribe.TRANSCRIPT_NAME}")
                self.set_dirty()
                self.refresh_list(self.current_index() or 0)
            self.app.set_status(text)

        check()

    def open_folder(self):
        if self.out_dir and self.out_dir.is_dir():
            self.app.open_path(self.out_dir)

    def open_index(self):
        if self.out_dir and (self.out_dir / stepdoc.INDEX_NAME).is_file():
            self.app.open_path(self.out_dir / stepdoc.INDEX_NAME)
