#!/usr/bin/env python3
#
# gui_editor.py
# 2026-10-02
# Version: v1.1.0
#
# PURPOSE:
# The "Steps" tab of the GUI: review and edit the steps of one processed
# recording. Reorder, delete (and restore) steps, write a caption for each
# one, then Save to re-render the screenshots and regenerate steps.md from
# the untouched originals.

import threading

import tkinter as tk
from tkinter import messagebox, ttk

import stepdoc


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
        self._loading_caption = False
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
        self.options_bar = ttk.Frame(top)   # per-video toggles added by later features
        self.options_bar.pack(side="right")

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
        self.step_buttons = []
        for r, (text, cmd) in enumerate((("Move Up", lambda: self.move(-1)),
                                         ("Move Down", lambda: self.move(1)),
                                         ("Delete Step", self.delete_step),
                                         ("Restore Deleted", self.restore_deleted)), 1):
            b = ttk.Button(left, text=text, command=cmd)
            b.grid(row=(r + 1) // 2, column=(r + 1) % 2, sticky="ew", pady=(4, 0), padx=(0, 4))
            self.step_buttons.append(b)
        # Rows 1-2 hold the four buttons above; extra tools go from row 3
        self.tools_frame = ttk.Frame(left)
        self.tools_frame.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(6, 0))

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

        ttk.Label(right, textvariable=self.v_info, anchor="w").grid(row=2, column=0, sticky="ew",
                                                                    pady=(4, 0))
        cap = ttk.Frame(right)
        cap.grid(row=3, column=0, sticky="ew", pady=(4, 0))
        cap.columnconfigure(1, weight=1)
        ttk.Label(cap, text="Caption:").grid(row=0, column=0, sticky="nw", padx=(0, 6))
        self.caption = tk.Text(cap, height=3, wrap="word", undo=True)
        self.caption.grid(row=0, column=1, sticky="ew")
        self.caption.bind("<<Modified>>", self.on_caption_modified)

        bar = ttk.Frame(self)
        bar.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        ttk.Button(bar, text="< Prev", command=lambda: self.step_by(-1)).pack(side="left")
        ttk.Button(bar, text="Next >", command=lambda: self.step_by(1)).pack(side="left", padx=4)
        ttk.Button(bar, text="Open Image", command=self.open_image).pack(side="left", padx=4)
        self.action_bar = ttk.Frame(bar)    # extra actions added by later features
        self.action_bar.pack(side="left", padx=4)
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
        info = f"Step {i + 1} of {len(self.doc['steps'])} at {stepdoc.fmt_ts(step['time'])}"
        if step.get("still_from") is not None and step.get("still_to") is not None:
            info += (f" | screen stable {stepdoc.fmt_ts(step['still_from'])} to "
                     f"{stepdoc.fmt_ts(step['still_to'])}")
        self.v_info.set(info)
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

    def move(self, delta):
        i = self.current_index()
        if i is None:
            return
        j = stepdoc.move_step(self.doc, i, delta)
        if j != i:
            self.set_dirty()
            self.refresh_list(j)

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
            self.after_preview_drawn(step, w, h)
        except Exception as exc:
            self.canvas.create_text(w // 2, h // 2, fill="white", width=w - 20,
                                    text=f"Preview unavailable: {exc}")

    def after_preview_drawn(self, step, w, h):
        """Hook for later features that draw overlays on the original frame."""

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
                               progress=lambda f, t: self.app.q.put(("status", t)))
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

    def open_folder(self):
        if self.out_dir and self.out_dir.is_dir():
            self.app.open_path(self.out_dir)

    def open_index(self):
        if self.out_dir and (self.out_dir / stepdoc.INDEX_NAME).is_file():
            self.app.open_path(self.out_dir / stepdoc.INDEX_NAME)
