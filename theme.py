#!/usr/bin/env python3
#
# theme.py
# 2026-10-10
# Version: v1.0.0
#
# PURPOSE:
# Light and dark appearance for the GUI, and "System" mode that follows the
# operating system's app theme (Windows: Settings > Personalization >
# Colors; macOS: Appearance; Linux: the GNOME/KDE color scheme) and switches
# when it changes. Built on Tk's "clam" theme with our own colors, so it
# needs nothing beyond the Tkinter that comes with Python. On Windows the
# title bar is switched to dark as well.

import os
import subprocess
import sys

import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

MODES = ("system", "light", "dark")
MODE_LABELS = {"system": "System", "light": "Light", "dark": "Dark"}

PALETTES = {
    "light": {
        "bg": "#f3f3f3",          # window
        "surface": "#ffffff",     # cards, lists, inputs
        "surface_alt": "#f7f7f8",
        "border": "#d6d6d9",
        "text": "#1b1b1f",
        "muted": "#5f6368",
        "accent": "#0f6cbd",
        "accent_hover": "#115ea3",
        "accent_text": "#ffffff",
        "select": "#cfe4fa",
        "select_text": "#1b1b1f",
        "button": "#fbfbfb",
        "button_hover": "#eef0f2",
        "button_pressed": "#e1e4e8",
        "disabled": "#a0a3a8",
        "warn": "#9a5b00",
        "error": "#c42b1c",
        "canvas": "#e6e6e9",
        "canvas_text": "#1b1b1f",
    },
    "dark": {
        "bg": "#1f1f22",
        "surface": "#2b2b2f",
        "surface_alt": "#26262a",
        "border": "#3d3d43",
        "text": "#ececf1",
        "muted": "#a2a5ab",
        "accent": "#4ca0e0",
        "accent_hover": "#62b0ea",
        "accent_text": "#0d1117",
        "select": "#264f78",
        "select_text": "#ffffff",
        "button": "#323237",
        "button_hover": "#3b3b41",
        "button_pressed": "#45454c",
        "disabled": "#6b6e74",
        "warn": "#f0b45b",
        "error": "#ff7b72",
        "canvas": "#161618",
        "canvas_text": "#ececf1",
    },
}


def system_theme():
    """'dark' or 'light' from the operating system's app theme setting."""
    try:
        if os.name == "nt":
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows"
                                r"\CurrentVersion\Themes\Personalize") as key:
                value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return "light" if value else "dark"
        if sys.platform == "darwin":
            out = subprocess.run(["defaults", "read", "-g", "AppleInterfaceStyle"],
                                 capture_output=True, text=True, timeout=3)
            return "dark" if "dark" in out.stdout.lower() else "light"
        out = subprocess.run(["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"],
                             capture_output=True, text=True, timeout=3)
        if out.returncode == 0 and out.stdout.strip():
            return "dark" if "dark" in out.stdout.lower() else "light"
        kde = os.path.expanduser("~/.config/kdeglobals")
        if os.path.isfile(kde):
            with open(kde, encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    if line.startswith("ColorScheme="):
                        return "dark" if "dark" in line.lower() else "light"
        out = subprocess.run(["gsettings", "get", "org.gnome.desktop.interface", "gtk-theme"],
                             capture_output=True, text=True, timeout=3)
        if out.returncode == 0 and "dark" in out.stdout.lower():
            return "dark"
    except (OSError, ValueError, subprocess.SubprocessError):
        pass
    return "light"


def set_title_bar_dark(window, dark):
    """Windows 10 (20H1+) and 11: dark or light title bar for one window."""
    if os.name != "nt":
        return
    try:
        import ctypes
        window.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
        value = ctypes.c_int(1 if dark else 0)
        for attribute in (20, 19):   # DWMWA_USE_IMMERSIVE_DARK_MODE (new, old)
            if ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, attribute, ctypes.byref(value), ctypes.sizeof(value)) == 0:
                break
    except Exception:
        pass


class Theme:
    """Applies a palette to ttk styles and to the classic Tk widgets
    (Listbox, Text, Canvas, Menu) that ttk styles do not reach."""

    POLL_MS = 4000

    def __init__(self, root, mode="system"):
        self.root = root
        self.mode = mode if mode in MODES else "system"
        self.name = None          # resolved: "light" or "dark"
        self.colors = PALETTES["light"]
        self.style = ttk.Style(root)
        self.listeners = []       # callables run after every change
        self._poll_job = None
        self._images = {}         # indicator images per theme (kept alive for Tk)
        self._setup_fonts()

    # ------------------------------------------------------------- fonts

    def _setup_fonts(self):
        default = tkfont.nametofont("TkDefaultFont")
        if os.name == "nt":
            for name in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont",
                         "TkCaptionFont", "TkSmallCaptionFont", "TkTooltipFont"):
                try:
                    tkfont.nametofont(name).configure(family="Segoe UI", size=10)
                except tk.TclError:
                    pass
        family = default.actual("family")
        size = abs(default.actual("size")) or 10
        self.fonts = {
            "title": tkfont.Font(self.root, family=family, size=size + 5, weight="bold"),
            "heading": tkfont.Font(self.root, family=family, size=size + 1, weight="bold"),
            "small": tkfont.Font(self.root, family=family, size=max(size - 1, 8)),
            "bold": tkfont.Font(self.root, family=family, size=size, weight="bold"),
            "mono": tkfont.Font(self.root, family="Consolas" if os.name == "nt" else "DejaVu Sans Mono",
                                size=size),
        }

    # ------------------------------------------------------------- modes

    def set_mode(self, mode):
        self.mode = mode if mode in MODES else "system"
        self.apply()

    def resolved(self):
        return system_theme() if self.mode == "system" else self.mode

    def apply(self):
        name = self.resolved()
        self.name = name
        self.colors = PALETTES[name]
        self._configure_styles()
        self.style_widgets(self.root)
        for listener in list(self.listeners):
            listener()
        self._schedule_poll()

    def _schedule_poll(self):
        if self._poll_job:
            try:
                self.root.after_cancel(self._poll_job)
            except tk.TclError:
                pass
            self._poll_job = None
        if self.mode == "system":
            self._poll_job = self.root.after(self.POLL_MS, self._poll)

    def _poll(self):
        self._poll_job = None
        if self.mode == "system" and system_theme() != self.name:
            self.apply()
        else:
            self._schedule_poll()

    def stop(self):
        if self._poll_job:
            try:
                self.root.after_cancel(self._poll_job)
            except tk.TclError:
                pass
            self._poll_job = None

    # ------------------------------------------------------------ styles

    def _configure_styles(self):
        c, s = self.colors, self.style
        s.theme_use("clam")
        base = dict(background=c["bg"], foreground=c["text"], fieldbackground=c["surface"],
                    bordercolor=c["border"], lightcolor=c["border"], darkcolor=c["border"],
                    troughcolor=c["surface_alt"], selectbackground=c["select"],
                    selectforeground=c["select_text"], insertcolor=c["text"],
                    focuscolor=c["accent"], arrowcolor=c["text"], font="TkDefaultFont")
        s.configure(".", **base)
        s.map(".", foreground=[("disabled", c["disabled"])])

        s.configure("TFrame", background=c["bg"])
        s.configure("Card.TFrame", background=c["surface"])
        s.configure("Bar.TFrame", background=c["surface"])
        s.configure("TLabel", background=c["bg"], foreground=c["text"])
        for prefix, bg in (("", c["bg"]), ("Card.", c["surface"]), ("Bar.", c["surface"])):
            s.configure(f"{prefix}TLabel", background=bg, foreground=c["text"])
            s.configure(f"{prefix}Muted.TLabel", background=bg, foreground=c["muted"])
            s.configure(f"{prefix}Heading.TLabel", background=bg, foreground=c["text"],
                        font=self.fonts["heading"])
            s.configure(f"{prefix}Title.TLabel", background=bg, foreground=c["text"],
                        font=self.fonts["title"])
            s.configure(f"{prefix}Warn.TLabel", background=bg, foreground=c["warn"],
                        font=self.fonts["bold"])
            s.configure(f"{prefix}TCheckbutton", background=bg, foreground=c["text"],
                        indicatorbackground=c["surface"], indicatorforeground=c["accent"],
                        indicatormargin=(0, 0, 6, 0), padding=(0, 2))
            s.map(f"{prefix}TCheckbutton",
                  background=[("active", bg)],
                  indicatorbackground=[("disabled", c["surface_alt"]), ("pressed", c["select"]),
                                       ("selected", c["accent"]), ("", c["surface"])],
                  indicatorforeground=[("selected", c["accent_text"]), ("", c["surface"])])
            s.configure(f"{prefix}TRadiobutton", background=bg, foreground=c["text"],
                        indicatorbackground=c["surface"], indicatorforeground=c["accent"],
                        indicatormargin=(0, 0, 6, 0), padding=(0, 2))
            s.map(f"{prefix}TRadiobutton",
                  background=[("active", bg)],
                  indicatorbackground=[("selected", c["accent"]), ("", c["surface"])],
                  indicatorforeground=[("selected", c["accent_text"]), ("", c["surface"])])

        self._indicators()

        s.configure("TButton", background=c["button"], foreground=c["text"],
                    bordercolor=c["border"], lightcolor=c["button"], darkcolor=c["button"],
                    padding=(12, 5), focusthickness=1, focuscolor=c["accent"])
        s.map("TButton",
              background=[("disabled", c["surface_alt"]), ("pressed", c["button_pressed"]),
                          ("active", c["button_hover"])],
              lightcolor=[("pressed", c["button_pressed"]), ("active", c["button_hover"])],
              darkcolor=[("pressed", c["button_pressed"]), ("active", c["button_hover"])],
              foreground=[("disabled", c["disabled"])])
        s.configure("Accent.TButton", background=c["accent"], foreground=c["accent_text"],
                    bordercolor=c["accent"], lightcolor=c["accent"], darkcolor=c["accent"],
                    font=self.fonts["bold"])
        s.map("Accent.TButton",
              background=[("disabled", c["surface_alt"]), ("pressed", c["accent_hover"]),
                          ("active", c["accent_hover"])],
              lightcolor=[("active", c["accent_hover"])], darkcolor=[("active", c["accent_hover"])],
              bordercolor=[("disabled", c["border"])],
              foreground=[("disabled", c["disabled"])])
        for name, bg in (("Link.TButton", c["bg"]), ("Card.Link.TButton", c["surface"])):
            s.configure(name, background=bg, foreground=c["accent"], bordercolor=bg,
                        lightcolor=bg, darkcolor=bg, padding=(0, 2), focusthickness=0)
            s.map(name, background=[("active", bg), ("pressed", bg)],
                  lightcolor=[("active", bg)], darkcolor=[("active", bg)],
                  foreground=[("active", c["accent_hover"])])
        s.configure("Toolbutton", background=c["surface"], padding=(8, 3))
        s.configure("Segment.TRadiobutton", background=c["button"], foreground=c["text"],
                    padding=(12, 4), indicatorsize=0, indicatormargin=0, borderwidth=1,
                    relief="solid", bordercolor=c["border"])
        s.layout("Segment.TRadiobutton", [("Radiobutton.padding", {"sticky": "nswe", "children": [
            ("Radiobutton.label", {"sticky": "nswe"})]})])
        s.map("Segment.TRadiobutton",
              background=[("selected", c["accent"]), ("active", c["button_hover"])],
              foreground=[("selected", c["accent_text"])])

        for widget in ("TEntry", "TCombobox", "TSpinbox"):
            s.configure(widget, fieldbackground=c["surface"], foreground=c["text"],
                        background=c["button"], bordercolor=c["border"], lightcolor=c["surface"],
                        darkcolor=c["surface"], insertcolor=c["text"], padding=(6, 4),
                        arrowcolor=c["text"])
            s.map(widget, bordercolor=[("focus", c["accent"])],
                  lightcolor=[("focus", c["accent"])],
                  fieldbackground=[("readonly", c["surface"]), ("disabled", c["surface_alt"])],
                  foreground=[("disabled", c["disabled"])],
                  selectbackground=[("readonly", c["surface"])],
                  selectforeground=[("readonly", c["text"])],
                  background=[("active", c["button_hover"])])

        s.configure("Treeview", background=c["surface"], fieldbackground=c["surface"],
                    foreground=c["text"], bordercolor=c["border"], rowheight=self._row_height(),
                    lightcolor=c["surface"], darkcolor=c["surface"])
        s.map("Treeview", background=[("selected", c["select"])],
              foreground=[("selected", c["select_text"])])
        s.configure("Treeview.Heading", background=c["surface_alt"], foreground=c["muted"],
                    bordercolor=c["border"], lightcolor=c["surface_alt"],
                    darkcolor=c["surface_alt"], relief="flat", padding=(6, 4))
        s.map("Treeview.Heading", background=[("active", c["button_hover"])])

        s.configure("TNotebook", background=c["bg"], bordercolor=c["border"], tabmargins=(0, 4, 0, 0),
                    lightcolor=c["bg"], darkcolor=c["bg"])
        s.configure("TNotebook.Tab", background=c["bg"], foreground=c["muted"], padding=(16, 6),
                    bordercolor=c["bg"], lightcolor=c["bg"], darkcolor=c["bg"])
        s.map("TNotebook.Tab",
              background=[("selected", c["surface"]), ("active", c["button_hover"])],
              foreground=[("selected", c["text"])],
              lightcolor=[("selected", c["accent"])],
              bordercolor=[("selected", c["border"])])
        s.configure("TLabelframe", background=c["surface"], bordercolor=c["border"],
                    lightcolor=c["border"], darkcolor=c["border"], relief="solid", borderwidth=1)
        s.configure("TLabelframe.Label", background=c["surface"], foreground=c["text"],
                    font=self.fonts["heading"])
        s.configure("TProgressbar", background=c["accent"], troughcolor=c["surface_alt"],
                    bordercolor=c["border"], lightcolor=c["accent"], darkcolor=c["accent"])
        for orient in ("Vertical", "Horizontal"):
            s.configure(f"{orient}.TScrollbar", background=c["button"], troughcolor=c["surface"],
                        bordercolor=c["surface"], lightcolor=c["button"], darkcolor=c["button"],
                        arrowcolor=c["muted"], gripcount=0, arrowsize=12)
            s.map(f"{orient}.TScrollbar", background=[("active", c["button_hover"])])
        s.configure("TSeparator", background=c["border"])
        s.configure("TPanedwindow", background=c["bg"])
        s.configure("Sash", sashthickness=6, gripcount=0, background=c["bg"])

        # Classic widgets created later (dialogs, combobox drop-downs)
        r = self.root
        r.option_add("*TCombobox*Listbox.background", c["surface"])
        r.option_add("*TCombobox*Listbox.foreground", c["text"])
        r.option_add("*TCombobox*Listbox.selectBackground", c["select"])
        r.option_add("*TCombobox*Listbox.selectForeground", c["select_text"])
        r.option_add("*Menu.background", c["surface"])
        r.option_add("*Menu.foreground", c["text"])
        r.option_add("*Menu.activeBackground", c["select"])
        r.option_add("*Menu.activeForeground", c["select_text"])

    # -------------------------------------------------- check and radio

    def _indicator_size(self):
        try:
            scaling = float(self.root.tk.call("tk", "scaling"))
        except (tk.TclError, ValueError):
            scaling = 1.333
        return max(12, round(14 * scaling / 1.333))

    def _draw(self, size, kind, fill, edge, mark=None):
        """A check box or radio indicator, drawn pixel by pixel so it looks
        the same everywhere. Pixels outside the shape stay transparent; the
        mark inside is smoothed against the fill color."""
        width = size + max(4, size // 3)          # room before the label
        img = tk.PhotoImage(width=width, height=size)

        def rgb(color):
            color = color.lstrip("#")
            return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))

        def mix(a, b, t):
            return "#%02x%02x%02x" % tuple(round(x + (y - x) * t) for x, y in zip(a, b))

        f, e = rgb(fill), rgb(edge)
        m = rgb(mark) if mark else None
        r = size / 2.0
        radius = max(2.0, size / 5.0)
        stroke = max(1.0, size / 14.0)
        check = [(0.24, 0.53), (0.43, 0.71), (0.77, 0.33)]

        def seg_dist(px, py, a, b):
            (ax, ay), (bx, by) = a, b
            dx, dy = bx - ax, by - ay
            t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
            return ((px - ax - t * dx) ** 2 + (py - ay - t * dy) ** 2) ** 0.5

        for y in range(size):
            row = []
            for x in range(size):
                cx, cy = x + 0.5, y + 0.5
                if kind == "radio":
                    d = ((cx - r) ** 2 + (cy - r) ** 2) ** 0.5
                    inside, border = d <= r - 0.3, d > r - 0.3 - stroke
                else:
                    qx = max(abs(cx - r) - (r - radius), 0.0)
                    qy = max(abs(cy - r) - (r - radius), 0.0)
                    d = (qx * qx + qy * qy) ** 0.5
                    inside = d <= radius - 0.3
                    border = d > radius - 0.3 - stroke or abs(cx - r) > r - stroke \
                        or abs(cy - r) > r - stroke
                if not inside:
                    row.append(None)
                    continue
                color = e if border else f
                if m is not None:
                    cover = 0
                    for sy in (0.25, 0.75):
                        for sx in (0.25, 0.75):
                            ux, uy = (x + sx) / size, (y + sy) / size
                            if kind == "radio":
                                hit = ((ux - 0.5) ** 2 + (uy - 0.5) ** 2) ** 0.5 <= 0.2
                            else:
                                hit = min(seg_dist(ux, uy, check[0], check[1]),
                                          seg_dist(ux, uy, check[1], check[2])) <= 0.085
                            cover += hit
                    row.append(mix(color, m, cover / 4.0) if cover else
                               "#%02x%02x%02x" % color)
                else:
                    row.append("#%02x%02x%02x" % color)
            for x, color in enumerate(row):
                if color:
                    img.put(color, (x, y))
        return img

    def _indicators(self):
        c, s = self.colors, self.style
        size = self._indicator_size()
        for kind, element in (("check", "Checkbutton"), ("radio", "Radiobutton")):
            name = f"ILHS.{self.name}.{element}.indicator"
            if name not in self._images:
                images = (self._draw(size, kind, c["surface"], c["muted"]),
                          self._draw(size, kind, c["accent"], c["accent"], c["accent_text"]),
                          self._draw(size, kind, c["surface_alt"], c["border"]),
                          self._draw(size, kind, c["disabled"], c["disabled"], c["surface"]))
                self._images[name] = images
                off, on, dis, dis_on = images
                s.element_create(name, "image", off, ("disabled", "selected", dis_on),
                                 ("selected", on), ("disabled", dis))
            for prefix in ("", "Card.", "Bar."):
                s.layout(f"{prefix}T{element}", [(f"{element}.padding", {"sticky": "nswe", "children": [
                    (name, {"side": "left", "sticky": ""}),
                    (f"{element}.focus", {"side": "left", "sticky": "w", "children": [
                        (f"{element}.label", {"sticky": "nswe"})]})]})])

    def _row_height(self):
        return tkfont.nametofont("TkDefaultFont").metrics("linespace") + 10

    # ------------------------------------------------------- tk widgets

    def style_widgets(self, widget):
        """Colors for classic Tk widgets under `widget` (ttk ones follow the
        styles). Widgets can opt out with `widget._theme_skip = True`."""
        c = self.colors
        stack = [widget]
        while stack:
            w = stack.pop()
            stack.extend(w.winfo_children())
            if getattr(w, "_theme_skip", False):
                continue
            try:
                if isinstance(w, (tk.Tk, tk.Toplevel)):
                    w.configure(background=c["bg"])
                    set_title_bar_dark(w, self.name == "dark")
                elif isinstance(w, tk.Listbox):
                    w.configure(background=c["surface"], foreground=c["text"],
                                selectbackground=c["select"], selectforeground=c["select_text"],
                                highlightthickness=1, highlightbackground=c["border"],
                                highlightcolor=c["accent"], borderwidth=0, relief="flat",
                                disabledforeground=c["disabled"])
                elif isinstance(w, tk.Text):
                    w.configure(background=c["surface"], foreground=c["text"],
                                insertbackground=c["text"], selectbackground=c["select"],
                                selectforeground=c["select_text"], highlightthickness=1,
                                highlightbackground=c["border"], highlightcolor=c["accent"],
                                borderwidth=0, relief="flat")
                elif isinstance(w, tk.Canvas):
                    w.configure(background=c["canvas"], highlightthickness=0)
                elif isinstance(w, tk.Menu):
                    w.configure(background=c["surface"], foreground=c["text"],
                                activebackground=c["select"], activeforeground=c["select_text"],
                                selectcolor=c["accent"], borderwidth=0, relief="flat",
                                disabledforeground=c["disabled"])
                elif isinstance(w, (tk.Frame, tk.Label)):
                    w.configure(background=c["bg"])
            except tk.TclError:
                pass
        # Menus attached with root.configure(menu=...) are not children of a frame
        try:
            menu = widget.nametowidget(widget.cget("menu")) if widget.cget("menu") else None
        except (tk.TclError, KeyError, AttributeError):
            menu = None
        if menu is not None and menu is not widget:
            self._style_menu_tree(menu)

    def _style_menu_tree(self, menu):
        c = self.colors
        stack = [menu]
        while stack:
            m = stack.pop()
            stack.extend(child for child in m.winfo_children() if isinstance(child, tk.Menu))
            try:
                m.configure(background=c["surface"], foreground=c["text"],
                            activebackground=c["select"], activeforeground=c["select_text"],
                            selectcolor=c["accent"], borderwidth=0, relief="flat",
                            disabledforeground=c["disabled"])
            except tk.TclError:
                pass
