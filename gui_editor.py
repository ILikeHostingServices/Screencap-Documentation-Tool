#!/usr/bin/env python3
#
# gui_editor.py
# 2026-10-16
# Version: v2.5.2
#
# PURPOSE:
# The "Steps" tab of the GUI: review and edit the steps of one processed
# recording. Reorder, delete (and restore) steps, write a caption for each
# one, then Save to re-render the screenshots and regenerate steps.md from
# the untouched originals. The red "what changed" box can be switched on or
# off for the whole recording or for a single step, screenshots can be
# cropped by dragging a rectangle on the original frame, and sensitive areas
# can be blurred (detected automatically, or drawn by hand) with an
# unblurred copy kept alongside. Arrows, numbered markers, and text labels
# can be drawn on each screenshot, and a zoomed inset can show a small
# change up close. Finished steps export to HTML, Word, PDF, or PowerPoint,
# Play in VLC opens the recording just before the selected step, and
# Captions From Narration fills empty captions from what was said. A
# company logo and a Word template can be chosen for every export.

import copy
import threading
from pathlib import Path

import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from tkinter import font as tkfont

import annotate
import clips
import export
import player
import redact
import stepdoc
import transcribe


ANNOTATION_COLOR = "#E53935"
LOGO_KEY, TEMPLATE_KEY = "export_logo", "export_template"   # keys in the app settings


class FlowBar(ttk.Frame):
    """A row of widgets that wraps onto more rows when the window is too
    narrow for all of them, instead of cutting the last ones off. Widgets
    must be created with the bar as their parent, then added in order."""

    def __init__(self, parent, gap=6, row_gap=6, **kw):
        super().__init__(parent, **kw)
        self.items = []
        self.gap, self.row_gap = gap, row_gap
        self._last = None
        self._height = None
        self.bind("<Configure>", lambda e: self.layout())

    def add(self, widget, gap=None, right=False):
        """right=True keeps the widget at the right edge of its row."""
        self.items.append((widget, self.gap if gap is None else gap, right))
        return widget

    def layout(self):
        width = self.winfo_width()
        if width <= 1:
            return
        x = y = row_h = 0
        spots = []
        for widget, gap, right in self.items:
            w, h = widget.winfo_reqwidth(), widget.winfo_reqheight()
            if x and x + gap + w > width:
                x, y, row_h = 0, y + row_h + self.row_gap, 0
            elif x:
                x += gap
            if right:
                x = max(x, width - w)
            spots.append((widget, x, y, h))
            x += w
            row_h = max(row_h, h)
        rows = {}
        for widget, wx, wy, h in spots:       # center each widget in its row
            rows.setdefault(wy, []).append(h)
        layout = (width, tuple((wx, wy) for _, wx, wy, _ in spots))
        if layout == self._last:
            return
        self._last = layout
        for widget, wx, wy, h in spots:
            widget.place(in_=self, x=wx, y=wy + (max(rows[wy]) - h) // 2)
        height = y + row_h
        if height != self._height:     # cget("height") is a Tcl object on some Tk builds
            self._height = height
            self.configure(height=height)


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
        self.v_info_shown = tk.StringVar(value=self.v_info.get())
        self.v_title = tk.StringVar(value="")
        self.v_view = tk.StringVar(value="final")
        self.v_dirty = tk.StringVar(value="")
        self.v_removed = tk.StringVar(value="")
        self.v_hl_doc = tk.BooleanVar(value=True)
        self.v_hl_step = tk.BooleanVar(value=True)
        self.v_redact_doc = tk.BooleanVar(value=True)
        self.v_redact_step = tk.BooleanVar(value=True)
        self.v_zoom_doc = tk.BooleanVar(value=False)
        self.v_zoom_step = tk.BooleanVar(value=False)
        self.v_clip_step = tk.BooleanVar(value=False)
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

        # Header: document title, unsaved marker, removed count, and the
        # switches that apply to the whole recording
        top = FlowBar(self, gap=10)
        top.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        for var, style in ((self.v_title, "Heading.TLabel"), (self.v_dirty, "Warn.TLabel"),
                           (self.v_removed, "Muted.TLabel")):
            label = top.add(ttk.Label(top, textvariable=var, style=style))
            # the text changes, so the row is laid out again when it does
            label.bind("<Configure>", lambda e: top.layout(), add="+")
        self.options_bar = top.add(ttk.Frame(top), gap=16, right=True)
        ttk.Label(self.options_bar, text="Whole recording:", style="Muted.TLabel").pack(
            side="left", padx=(0, 8))
        ttk.Checkbutton(self.options_bar, text="Blur sensitive info", variable=self.v_redact_doc,
                        command=self.toggle_doc_redact).pack(side="left")
        ttk.Checkbutton(self.options_bar, text="Highlight changes", variable=self.v_hl_doc,
                        command=self.toggle_doc_highlight).pack(side="left", padx=(12, 0))
        ttk.Checkbutton(self.options_bar, text="Zoomed inset", variable=self.v_zoom_doc,
                        command=self.toggle_doc_zoom).pack(side="left", padx=(12, 0))

        # Left: the list of steps and reordering
        left = ttk.Frame(self)
        left.grid(row=1, column=0, sticky="ns")
        left.rowconfigure(1, weight=1)
        left.columnconfigure(0, weight=1)
        ttk.Label(left, text="Steps", style="Heading.TLabel").grid(row=0, column=0, sticky="w",
                                                                    pady=(0, 6))
        self.step_list = tk.Listbox(left, width=28, height=8, exportselection=False,
                                    activestyle="none",
                                    font=self.app.theme.fonts["mono"] if hasattr(self.app, "theme")
                                    else ("Consolas", 9))
        self.step_list.grid(row=1, column=0, sticky="nsew")
        sb = ttk.Scrollbar(left, orient="vertical", command=self.step_list.yview)
        sb.grid(row=1, column=1, sticky="ns")
        self.step_list.configure(yscrollcommand=sb.set)
        self.step_list.bind("<<ListboxSelect>>", lambda e: self.on_select())
        self.step_list.bind("<Double-1>", lambda e: self.open_image())
        self.step_list.bind("<Delete>", lambda e: self.delete_step())
        # Ctrl+Up/Down reorder; plain Up/Down page through steps (see on_arrow)
        self.step_list.bind("<Control-Up>", lambda e: self.move(-1) or "break")
        self.step_list.bind("<Control-Down>", lambda e: self.move(1) or "break")
        top_level = self.winfo_toplevel()
        top_level.bind("<Up>", lambda e: self.on_arrow(e, -1), add="+")
        top_level.bind("<Down>", lambda e: self.on_arrow(e, 1), add="+")
        order = ttk.Frame(left)
        order.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        order.columnconfigure((0, 1), weight=1, uniform="order")
        self.step_buttons = []
        for n, (text, cmd) in enumerate((("Move Up", lambda: self.move(-1)),
                                         ("Move Down", lambda: self.move(1)),
                                         ("Delete Step", self.delete_step),
                                         ("Restore Deleted", self.restore_deleted))):
            b = ttk.Button(order, text=text, command=cmd)
            b.grid(row=n // 2, column=n % 2, sticky="ew", padx=(0 if n % 2 == 0 else 4, 0),
                   pady=(0 if n < 2 else 4, 0))
            self.step_buttons.append(b)

        # Right: picture with its tools, caption, document details, export
        right = ttk.Frame(self)
        right.grid(row=1, column=1, sticky="nsew", padx=(14, 0))
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)
        viewbar = FlowBar(right)
        viewbar.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        segment = viewbar.add(ttk.Frame(viewbar))
        for value, text in (("final", "Screenshot"), ("original", "Original frame")):
            ttk.Radiobutton(segment, text=text, value=value, variable=self.v_view,
                            style="Segment.TRadiobutton",
                            command=self.schedule_preview).pack(side="left")
        crop = ttk.Menubutton(viewbar, text="Crop", width=0)
        crop_menu = tk.Menu(crop, tearoff=False)
        crop_menu.add_command(label="Crop All Steps (drag on the picture)",
                              command=lambda: self.begin_draw("crop", "all"))
        crop_menu.add_command(label="Crop This Step Only (drag on the picture)",
                              command=lambda: self.begin_draw("crop", "step"))
        crop_menu.add_command(label="No Crop on This Step", command=self.no_crop_step)
        crop_menu.add_separator()
        crop_menu.add_command(label="Clear All Crops", command=self.clear_crops)
        crop.configure(menu=crop_menu)
        viewbar.add(crop, gap=14)
        blur = ttk.Menubutton(viewbar, text="Blur", width=0)
        blur_menu = tk.Menu(blur, tearoff=False)
        blur_menu.add_command(label="Add Blur Box (drag on the picture)",
                              command=lambda: self.begin_draw("blur", "step"))
        blur_menu.add_command(label="Un-blur / Re-blur (click a box)", command=self.begin_pick)
        blur_menu.add_checkbutton(label="Blur This Step", variable=self.v_redact_step,
                                  command=self.toggle_step_redact)
        blur_menu.add_separator()
        blur_menu.add_command(label="Re-scan All Steps for Sensitive Text", command=self.rescan)
        blur.configure(menu=blur_menu)
        viewbar.add(blur)
        mark = ttk.Menubutton(viewbar, text="Annotate", width=0)
        mark_menu = tk.Menu(mark, tearoff=False)
        mark_menu.add_command(label="Add Arrow (drag from the start to the tip)",
                              command=lambda: self.begin_draw("arrow", "step"))
        mark_menu.add_command(label="Add Number (click where it goes)",
                              command=lambda: self.begin_place("number"))
        mark_menu.add_command(label="Add Text Label (click where it starts)",
                              command=lambda: self.begin_place("text"))
        mark_menu.add_separator()
        mark_menu.add_command(label="Edit or Remove (click an annotation)",
                              command=lambda: self.begin_place("edit"))
        mark_menu.add_command(label="Clear Annotations on This Step",
                              command=self.clear_annotations)
        mark.configure(menu=mark_menu)
        viewbar.add(mark)
        hl = ttk.Menubutton(viewbar, text="Highlight", width=0)
        hl_menu = tk.Menu(hl, tearoff=False)
        hl_menu.add_checkbutton(label="Red Box on This Step", variable=self.v_hl_step,
                                command=self.toggle_step_highlight)
        hl_menu.add_checkbutton(label="Zoomed Inset on This Step", variable=self.v_zoom_step,
                                command=self.toggle_step_zoom)
        hl_menu.add_separator()
        hl_menu.add_checkbutton(label="Animated Clip of This Step (GIF)",
                                variable=self.v_clip_step, command=self.toggle_step_clip)
        hl.configure(menu=hl_menu)
        viewbar.add(hl)
        self.tool_menus = (crop_menu, blur_menu, mark_menu, hl_menu)
        self.viewbar = viewbar

        self.canvas = tk.Canvas(right, highlightthickness=0, height=180, width=320)
        self.canvas.grid(row=1, column=0, sticky="nsew")
        self.canvas.bind("<Configure>", lambda e: self.schedule_preview())
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        # Clicking the picture takes the keyboard, so Up/Down page from there
        self.canvas.bind("<ButtonPress-1>", lambda e: self.canvas.focus_set(), add="+")
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.winfo_toplevel().bind("<Escape>", lambda e: self.cancel_draw(), add="+")

        # One line, shortened to fit, so the picture keeps the room
        info = ttk.Label(right, textvariable=self.v_info_shown, style="Muted.TLabel",
                         anchor="w", width=1)
        info.grid(row=2, column=0, sticky="ew", pady=(6, 0))
        self.info_label = info
        info.bind("<Configure>", lambda e: self.fit_info())
        self.v_info.trace_add("write", lambda *a: self.fit_info())
        heading = ttk.Frame(right)
        heading.grid(row=3, column=0, sticky="ew", pady=(6, 2))
        ttk.Label(heading, text="Caption", style="Heading.TLabel").pack(side="left")
        self.btn_narration = ttk.Button(heading, text="Captions From Narration",
                                        style="Link.TButton",
                                        command=self.captions_from_narration)
        self.btn_narration.pack(side="right")
        self.caption = tk.Text(right, height=2, wrap="word", undo=True, padx=8, pady=6,
                               font="TkDefaultFont")
        self.caption.grid(row=4, column=0, sticky="ew")
        self.caption.bind("<<Modified>>", self.on_caption_modified)

        # Document details and export, side by side
        lower = ttk.Frame(self)
        lower.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        lower.columnconfigure(0, weight=1)
        doc = ttk.Frame(lower, style="Card.TFrame", padding=10)
        doc.grid(row=0, column=0, sticky="nsew")
        doc.columnconfigure(1, weight=1)
        doc.columnconfigure(3, weight=2)
        # The title on its own row, so it keeps its room when the window is small
        ttk.Label(doc, text="Document title", style="Card.Muted.TLabel").grid(
            row=0, column=0, columnspan=4, sticky="w")
        self.entry_title = ttk.Entry(doc, textvariable=self.v_doc_title, width=20,
                                     font=self.app.theme.fonts["heading"]
                                     if hasattr(self.app, "theme") else None)
        self.entry_title.grid(row=1, column=0, columnspan=4, sticky="ew", pady=(2, 6))
        ttk.Label(doc, text="Version", style="Card.Muted.TLabel").grid(
            row=2, column=0, sticky="w", padx=(0, 6))
        ttk.Entry(doc, textvariable=self.v_doc_version, width=8).grid(
            row=2, column=1, sticky="ew")
        ttk.Label(doc, text="Author", style="Card.Muted.TLabel").grid(
            row=2, column=2, sticky="w", padx=(12, 6))
        ttk.Entry(doc, textvariable=self.v_doc_author, width=12).grid(
            row=2, column=3, sticky="ew")
        for var in (self.v_doc_title, self.v_doc_version, self.v_doc_author):
            var.trace_add("write", lambda *a: self.on_meta_changed())
        exp = ttk.Frame(lower, style="Card.TFrame", padding=10)
        exp.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        exp.columnconfigure(0, weight=1)
        exp_head = ttk.Frame(exp, style="Card.TFrame")
        exp_head.grid(row=0, column=0, sticky="ew")
        ttk.Label(exp_head, text="Export", style="Card.Muted.TLabel").pack(side="left")
        ttk.Button(exp_head, text="Logo and Template...", style="Card.Link.TButton",
                   command=self.open_branding).pack(side="right")
        buttons = ttk.Frame(exp, style="Card.TFrame")
        buttons.grid(row=1, column=0, sticky="w", pady=(2, 6))
        self.export_buttons = []
        for fmt, text in (("html", "HTML"), ("docx", "Word"), ("pdf", "PDF"),
                          ("pptx", "PowerPoint")):
            b = ttk.Button(buttons, text=text, width=0, command=lambda f=fmt: self.export(f))
            b.pack(side="left", padx=(0, 4))
            self.export_buttons.append(b)
        options = ttk.Frame(exp, style="Card.TFrame")
        options.grid(row=2, column=0, sticky="ew")
        ttk.Checkbutton(options, text="Unblurred copy", variable=self.v_export_unredacted,
                        style="Card.TCheckbutton").pack(side="left")
        ttk.Button(options, text="Open Exports", style="Card.Link.TButton",
                   command=self.open_export_folder).pack(side="right")

        # Bottom bar: navigation and actions on the left, saving on the right
        bar = ttk.Frame(self)
        bar.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        saving = ttk.Frame(bar)
        saving.pack(side="right", anchor="n")
        self.btn_save = ttk.Button(saving, text="Save Changes", style="Accent.TButton",
                                   command=self.save)
        self.btn_save.pack(side="right")
        ttk.Button(saving, text="Discard", command=self.discard).pack(side="right", padx=6)
        actions = FlowBar(bar, gap=4)
        actions.pack(side="left", fill="x", expand=True)
        actions.add(ttk.Button(actions, text="< Prev", width=7, command=lambda: self.step_by(-1)))
        actions.add(ttk.Button(actions, text="Next >", width=7, command=lambda: self.step_by(1)))
        opener = ttk.Menubutton(actions, text="Open", width=6)
        open_menu = tk.Menu(opener, tearoff=False)
        open_menu.add_command(label="Open Image", command=self.open_image)
        open_menu.add_command(label="Open Animated Clip", command=self.open_clip)
        open_menu.add_command(label="Open steps.md", command=self.open_index)
        open_menu.add_command(label="Open Output Folder", command=self.open_folder)
        open_menu.add_command(label="Open Exports Folder", command=self.open_export_folder)
        opener.configure(menu=open_menu)
        actions.add(opener, gap=16)
        self.tool_menus = self.tool_menus + (open_menu,)
        actions.add(ttk.Button(actions, text="Play in VLC", command=self.play))

    def on_theme_changed(self):
        """Colors that are not styles: menus of the tool buttons and the
        picture background. Redraw the picture in the new colors."""
        theme = getattr(self.app, "theme", None)
        if theme is None:
            return
        for menu in self.tool_menus:
            theme.style_widgets(menu)
        self.schedule_preview()

    def canvas_text_color(self):
        theme = getattr(self.app, "theme", None)
        return theme.colors["canvas_text"] if theme else "white"

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
        self.v_zoom_doc.set(self.doc.get("zoom", False))
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
        self.v_removed.set(f"{deleted} removed{extra}" if deleted else "")

    # ------------------------------------------------------------ editing

    def current_index(self):
        sel = self.step_list.curselection()
        return sel[0] if sel and self.doc and sel[0] < len(self.doc["steps"]) else None

    def current_step(self):
        i = self.current_index()
        return self.doc["steps"][i] if i is not None else None

    def set_dirty(self, dirty=True):
        self.dirty = dirty
        if dirty:   # counts edits, so a save knows whether more came in meanwhile
            self.edits = getattr(self, "edits", 0) + 1
        self.v_dirty.set("Unsaved changes" if dirty else "")

    def fit_info(self):
        """Show the step details on one line, cut short with ... when the
        window is too narrow for all of it."""
        label = getattr(self, "info_label", None)
        text = self.v_info.get()
        if label is None:
            return
        width = label.winfo_width()
        try:
            font = tkfont.nametofont(str(label.cget("font")) or "TkDefaultFont")
        except tk.TclError:
            font = tkfont.nametofont("TkDefaultFont")
        if width > 1 and font.measure(text) > width:
            while text and font.measure(text + "\u2026") > width:
                text = text[:-1]
            text = text.rstrip(" |") + "\u2026"
        if self.v_info_shown.get() != text:
            self.v_info_shown.set(text)

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
        if stepdoc.effective(step, self.doc, "zoom", default=False) and "change_box" in step:
            info += (" | zoomed inset" if stepdoc.zoom_inset(step, self.doc) else
                     " | no inset (no change found, or it is big enough to read)")
        if clips.wanted(step):
            start, end = clips.clip_range(step, self.doc)
            made = " (made when you save)" if not clips.clip_path(self.out_dir, step) or \
                self.dirty else ""
            info += f" | animated clip {end - start:.1f} s{made}"
        marks = len(annotate.step_annotations(step))
        if marks:
            info += f" | {marks} annotation(s)"
        self.v_redact_step.set(bool(stepdoc.effective(step, self.doc, "redact")))
        self.v_info.set(info)
        self.v_hl_step.set(bool(stepdoc.effective(step, self.doc, "highlight")))
        self.v_zoom_step.set(bool(stepdoc.effective(step, self.doc, "zoom", default=False)))
        self.v_clip_step.set(clips.wanted(step))
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
            step.pop("caption_auto", None)     # edited by hand now
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

    def toggle_doc_zoom(self):
        if not self.doc:
            return
        self.doc["zoom"] = self.v_zoom_doc.get()
        if self.doc["zoom"]:
            self.ensure_boxes()
        self.set_dirty()
        self.on_select()

    def toggle_step_zoom(self):
        step = self.current_step()
        if step is None:
            return
        step["zoom"] = self.v_zoom_step.get()
        if step["zoom"]:
            self.ensure_boxes()
        self.set_dirty()
        self.on_select()

    def toggle_step_clip(self):
        step = self.current_step()
        if step is None:
            return
        if self.v_clip_step.get() and self.source_video() is None:
            self.v_clip_step.set(False)
            messagebox.showinfo(self.app.name, "The original recording was not found, so a clip "
                                "cannot be made. It may have been moved or deleted from the "
                                "source folder.", parent=self.winfo_toplevel())
            return
        step["clip"] = self.v_clip_step.get()
        if step["clip"] and not self.doc.get("source_path") and self.source_video():
            self.doc["source_path"] = str(self.source_video())
        self.set_dirty()
        self.app.set_status("The animated clip is made when you click Save Changes."
                            if step["clip"] else "Clip removed from this step.")
        self.on_select()

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
        branding = self.branding()
        result = {}

        def work():
            try:
                result["path"] = export.export(out_dir, doc, fmt, unredacted,
                                               pandoc=self.app.pandoc, browser=self.app.browser,
                                               logo=branding.get(LOGO_KEY),
                                               template=branding.get(TEMPLATE_KEY))
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

    # ---------------------------------------------------------- branding

    def branding(self):
        """The logo and Word template chosen for every export (app settings)."""
        extra = getattr(self.app, "settings_extra", {})
        return {k: extra.get(k) for k in (LOGO_KEY, TEMPLATE_KEY) if extra.get(k)}

    def set_branding(self, key, value):
        extra = self.app.settings_extra
        if value:
            extra[key] = str(value)
        else:
            extra.pop(key, None)
        self.app.save_settings()

    def open_branding(self):
        """A small window to choose the logo and the Word template used for
        every export."""
        win = getattr(self, "branding_window", None)
        if win is not None and win.winfo_exists():
            win.deiconify()
            win.lift()
            return win
        parent = self.winfo_toplevel()
        win = tk.Toplevel(parent)
        win.title("Logo and Template")
        win.resizable(False, False)
        win.transient(parent)
        self.branding_window = win
        body = ttk.Frame(win, padding=(20, 18))
        body.pack(fill="both", expand=True)
        body.columnconfigure(1, weight=1)
        ttk.Label(body, text="Logo and Word Template", style="Heading.TLabel").grid(
            row=0, column=0, columnspan=4, sticky="w")
        ttk.Label(body, text="Used for every export. The logo goes at the top of HTML, PDF, "
                             "and Word documents. A Word template sets the fonts, colors, "
                             "margins, and page header and footer of Word exports.",
                  style="Muted.TLabel", wraplength=760, justify="left").grid(
            row=1, column=0, columnspan=4, sticky="w", pady=(4, 14))
        current = self.branding()
        self.v_logo = tk.StringVar(value=current.get(LOGO_KEY, ""))
        self.v_template = tk.StringVar(value=current.get(TEMPLATE_KEY, ""))
        rows = ((LOGO_KEY, "Logo", self.v_logo,
                 [("Pictures", "*.png *.jpg *.jpeg *.gif *.svg"), ("All files", "*.*")]),
                (TEMPLATE_KEY, "Word template", self.v_template,
                 [("Word documents", "*.docx"), ("All files", "*.*")]))
        for row, (key, label, var, types) in enumerate(rows, start=2):
            ttk.Label(body, text=label).grid(row=row, column=0, sticky="w", padx=(0, 10),
                                             pady=3)
            ttk.Entry(body, textvariable=var, width=46, state="readonly").grid(
                row=row, column=1, sticky="ew", pady=3)

            def browse(key=key, var=var, types=types, label=label):
                path = filedialog.askopenfilename(parent=win, title=f"Choose the {label.lower()}",
                                                  filetypes=types)
                if path:
                    var.set(path)
                    self.set_branding(key, path)
                    self.app.set_status(f"{label} set for every export.")

            def clear(key=key, var=var, label=label):
                var.set("")
                self.set_branding(key, None)
                self.app.set_status(f"{label} cleared.")

            ttk.Button(body, text="Browse...", command=browse).grid(row=row, column=2,
                                                                    padx=(8, 0), pady=3)
            ttk.Button(body, text="Clear", command=clear).grid(row=row, column=3,
                                                               padx=(6, 0), pady=3)
        starter = ttk.Frame(body)
        starter.grid(row=4, column=0, columnspan=4, sticky="ew", pady=(14, 0))
        ttk.Button(starter, text="Create Starter Template...",
                   command=lambda: self.create_template(win)).pack(side="left")
        ttk.Label(starter, text="Saves the standard template. Open it in Word, change its "
                                "styles and page header, save it, and choose it above.",
                  style="Muted.TLabel", wraplength=520, justify="left").pack(
            side="left", padx=(10, 0))
        ttk.Button(body, text="Close", command=win.destroy).grid(
            row=5, column=3, columnspan=1, sticky="e", pady=(18, 0))
        theme = getattr(self.app, "theme", None)
        if theme is not None:
            theme.style_widgets(win)
        return win

    def create_template(self, win):
        path = filedialog.asksaveasfilename(parent=win, title="Save the starter Word template",
                                            defaultextension=".docx",
                                            initialfile="ScreenCap Docs template.docx",
                                            filetypes=[("Word documents", "*.docx")])
        if not path:
            return None
        try:
            dest = export.create_template(path, pandoc=self.app.pandoc)
        except Exception as exc:
            messagebox.showerror(self.app.name, str(exc), parent=win)
            return None
        self.v_template.set(str(dest))
        self.set_branding(TEMPLATE_KEY, dest)
        self.app.set_status(f"Saved {dest.name} and chose it as the Word template. "
                            "Open it in Word to change how exports look.")
        self.app.open_path(dest)
        return dest

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
        if kind == "arrow":
            self.app.set_status("Drag from where the arrow starts to what it points at. "
                                "Press Esc to cancel.")
            return
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
            if self.draw["kind"] in ("pick", "number", "text", "edit"):
                kind, self.draw = self.draw["kind"], None
                self.canvas.configure(cursor="")
                scale, ox, oy = self.view_map
                x, y = (event.x - ox) / scale, (event.y - oy) / scale
                if kind == "pick":
                    self.pick_box(x, y)
                    self.on_select()
                else:
                    self.place_annotation(kind, x, y)
                return
            self.draw["start"] = (event.x, event.y)

    def on_drag(self, event):
        if not self.draw or not self.draw["start"]:
            return
        if self.draw["item"]:
            self.canvas.delete(self.draw["item"])
        x0, y0 = self.draw["start"]
        if self.draw["kind"] == "arrow":
            self.draw["item"] = self.canvas.create_line(x0, y0, event.x, event.y, arrow="last",
                                                        fill=ANNOTATION_COLOR, width=3)
            return
        self.draw["item"] = self.canvas.create_rectangle(x0, y0, event.x, event.y,
                                                         outline="#4FC3F7", width=2, dash=(6, 3))

    def on_release(self, event):
        if not self.draw or not self.draw["start"]:
            return
        draw, self.draw = self.draw, None
        self.canvas.configure(cursor="")
        scale, ox, oy = self.view_map
        x0, y0 = draw["start"]
        if draw["kind"] == "arrow":
            self.add_arrow([(x0 - ox) / scale, (y0 - oy) / scale],
                           [(event.x - ox) / scale, (event.y - oy) / scale])
            return
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

    # ---------------------------------------------------------- annotations

    def begin_place(self, kind):
        """Click on the original frame to place a number or a text label, or
        to edit or remove an annotation."""
        step = self.current_step()
        if step is None or not self.doc.get("width"):
            return
        if kind == "edit" and not annotate.step_annotations(step):
            self.app.set_status("This step has no annotations.")
            return
        self.draw = {"kind": kind, "scope": "step", "start": None, "item": None}
        self.v_view.set("original")
        self.canvas.configure(cursor="hand2" if kind == "edit" else "crosshair")
        self.render_preview()
        self.app.set_status({
            "number": "Click where the number goes. Press Esc to cancel.",
            "text": "Click where the label's top-left corner goes. Press Esc to cancel.",
            "edit": "Click an annotation to edit or remove it. Press Esc to cancel.",
        }[kind])

    def _frame_point(self, x, y):
        return [max(0, min(round(x), self.doc["width"] - 1)),
                max(0, min(round(y), self.doc["height"] - 1))]

    def add_arrow(self, start, tip):
        start, tip = self._frame_point(*start), self._frame_point(*tip)
        if abs(tip[0] - start[0]) + abs(tip[1] - start[1]) < 12:
            self.app.set_status("Arrow too short; drag from where it starts to its tip.")
            self.schedule_preview()
            return
        self.add_annotation({"kind": "arrow", "from": start, "to": tip}, "Arrow added.")

    def ask_label(self, initial=""):
        text = simpledialog.askstring(self.app.name, "Label text:", initialvalue=initial,
                                      parent=self.winfo_toplevel())
        return " ".join((text or "").split())

    def place_annotation(self, kind, x, y):
        step = self.current_step()
        point = self._frame_point(x, y)
        if kind == "number":
            n = annotate.next_number(step)
            self.add_annotation({"kind": "number", "at": point, "n": n}, f"Number {n} added.")
        elif kind == "text":
            text = self.ask_label()
            if not text:
                self.app.set_status("No text; nothing added.")
                self.schedule_preview()
                return
            self.add_annotation({"kind": "text", "at": point, "text": text}, "Label added.")
        elif kind == "edit":
            self.edit_annotation(step, x, y)

    def add_annotation(self, ann, message):
        step = self.current_step()
        step.setdefault("annotations", []).append(ann)
        self.set_dirty()
        self.v_view.set("final")
        self.app.set_status(message + " Click Save Changes to keep it.")
        self.on_select()

    def edit_annotation(self, step, x, y):
        hits = [(d, a) for a in annotate.step_annotations(step)
                for d in [annotate.hit(a, x, y, self.doc["width"])] if d is not None]
        if not hits:
            self.app.set_status("No annotation there.")
            self.schedule_preview()
            return
        ann = min(hits, key=lambda h: h[0])[1]
        parent = self.winfo_toplevel()
        if ann["kind"] == "text":
            text = simpledialog.askstring(
                self.app.name, "Label text (clear it to remove the label):",
                initialvalue=ann["text"], parent=parent)
            if text is None:
                self.schedule_preview()
                return
            text = " ".join(text.split())
            if text:
                ann["text"] = text
                message = "Label changed."
            else:
                step["annotations"].remove(ann)
                message = "Label removed."
        elif ann["kind"] == "number":
            n = simpledialog.askinteger(
                self.app.name, "Number to show (0 removes the marker):",
                initialvalue=ann.get("n", 1), minvalue=0, maxvalue=999, parent=parent)
            if n is None:
                self.schedule_preview()
                return
            if n:
                ann["n"] = n
                message = f"Marker changed to {n}."
            else:
                step["annotations"].remove(ann)
                message = "Marker removed."
        else:
            what = "click ring" if ann["kind"] == "click" else "arrow"
            if not messagebox.askyesno(self.app.name, f"Remove this {what}?", parent=parent):
                self.schedule_preview()
                return
            step["annotations"].remove(ann)
            message = f"{what.capitalize()} removed."
        self.set_dirty()
        self.v_view.set("final")
        self.app.set_status(message + " Click Save Changes to keep it.")
        self.on_select()

    def clear_annotations(self):
        step = self.current_step()
        if step is None or not annotate.step_annotations(step):
            self.app.set_status("This step has no annotations.")
            return
        step["annotations"] = []
        self.set_dirty()
        self.app.set_status("Annotations cleared on this step. Click Save Changes to keep it.")
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
            self.canvas.create_text(w // 2, h // 2, fill=self.canvas_text_color(),
                                    text="Original image is missing (deleted or moved).")
            return
        filters = None
        if self.v_view.get() == "final":
            filters = stepdoc.build_filter(step, self.doc, work_dir=self.out_dir)
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
            self.canvas.create_text(w // 2, h // 2, fill=self.canvas_text_color(), width=w - 20,
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
        gray when switched off), hand-drawn blur boxes (orange), the zoomed
        inset (purple), and the annotations."""
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
        inset = stepdoc.zoom_inset(step, self.doc)
        if inset:
            t = 2 * inset["border"]
            self.overlay(inset["at"] + [inset["size"][0] + t, inset["size"][1] + t],
                         "#AB47BC", "zoomed inset")
        self.draw_annotations(step)

    def draw_annotations(self, step):
        """Annotations as simple outlines on the original frame, so they can
        be found and clicked; the Screenshot view shows them as saved."""
        scale, ox, oy = self.view_map
        sz = annotate.sizes(self.doc["width"])

        def pt(p):
            return ox + p[0] * scale, oy + p[1] * scale

        for ann in annotate.step_annotations(step):
            if ann["kind"] == "arrow":
                self.canvas.create_line(*pt(ann["from"]), *pt(ann["to"]), arrow="last",
                                        fill=ANNOTATION_COLOR, width=3)
            elif ann["kind"] == "number":
                (cx, cy), r = pt(ann["at"]), max(8, sz["marker"] * scale)
                self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r,
                                        outline=ANNOTATION_COLOR, width=2)
                self.canvas.create_text(cx, cy, text=str(ann.get("n", 1)),
                                        fill=ANNOTATION_COLOR)
            elif ann["kind"] == "click":
                (cx, cy), r = pt(ann["at"]), max(8, annotate.ring_radius(sz) * scale)
                self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r,
                                        outline=ANNOTATION_COLOR, width=3)
            elif ann["kind"] == "text":
                x, y = pt(ann["at"])
                w, h = annotate.label_size(ann["text"], self.doc["width"])
                self.canvas.create_rectangle(x, y, x + w * scale, y + h * scale,
                                             outline=ANNOTATION_COLOR, width=2)
                self.canvas.create_text(x + 4, y + h * scale / 2, anchor="w",
                                        text=ann["text"], fill=ANNOTATION_COLOR)

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
        result = {"edits": getattr(self, "edits", 0)}

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
        if getattr(self, "edits", 0) != result["edits"]:
            # Edited while saving: those changes are not in the saved files yet
            self.app.q.put(("status", "Saved. Newer changes are not saved yet: "
                                      "click Save Changes again."))
            self.app.on_steps_saved(self.out_dir)
            return True
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

    def open_clip(self):
        step = self.current_step()
        path = clips.clip_path(self.out_dir, step) if step is not None else None
        if path:
            self.app.open_path(path)
        else:
            self.app.set_status("This step has no animated clip. Switch it on in the "
                                "Highlight menu, then click Save Changes.")

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
