#!/usr/bin/env python3
#
# gui_shots.py
# 2026-10-20
# Version: v1.3.0
#
# PURPOSE:
# Opens the GUI on the demo recording made by make_screenshots.sh and takes
# the store screenshots: the Steps tab, the Annotate menu, the Record
# window, the dark theme, a recording in progress, and the update window
# (as a user of the previous release sees this one). Also exports the
# demo as HTML and as PowerPoint (with a made-up logo) for the document
# screenshots. Run by make_screenshots.sh.
#
# Usage: gui_shots.py DEMO_DOCUMENTS_FOLDER OUTPUT_FOLDER

import os
import subprocess
import sys
import tempfile
import time
from importlib.machinery import SourceFileLoader
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
D = Path(sys.argv[1])
OUT = Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT))
prof = Path(tempfile.mkdtemp())
os.environ["APPDATA"] = os.environ["XDG_CONFIG_HOME"] = str(prof)
os.environ["SCREENCAP_NO_UPDATE_CHECK"] = "1"
import tkinter as tk  # noqa: E402
from tkinter import ttk  # noqa: E402
gui = SourceFileLoader("screencap_gui", str(ROOT / "screencap_gui.pyw")).load_module()
root = tk.Tk(className="ScreencapDocTool"); gui.set_window_icon(root)
app = gui.App(root); app.open_path = lambda p: None
root.geometry("1480x900+60+36")
def pump(s=0.3):
    end = time.monotonic() + s
    while time.monotonic() < end: root.update(); time.sleep(0.02)
def shot(name): pump(0.8); subprocess.run(["import", "-window", "root", str(OUT / f"{name}.png")]); print("shot", name, flush=True)
def widgets(w):
    yield w
    for c in w.winfo_children(): yield from widgets(c)
def menubutton(text):
    return next(w for w in widgets(root) if isinstance(w, ttk.Menubutton) and w.cget("text") == text)
def click(w):
    root.update_idletasks()
    subprocess.run(["xdotool", "mousemove", str(w.winfo_rootx() + w.winfo_width() // 2),
                    str(w.winfo_rooty() + w.winfo_height() // 2), "click", "1"])
app.v_source.set(str(D / "Recordings")); app.v_output.set(str(D / "Output"))
app.refresh_videos(); pump(1)
app.tree.selection_set(app.tree.get_children()[0]); pump(); app.show_steps(); pump(1)
ed = app.editor
ed.v_doc_title.set("Create the Northwind Traders password database"); ed.v_doc_version.set("v1.0.0"); ed.v_doc_author.set("IT Service Desk")
ed.save(wait=True); pump(1)
def goto(caption_start, fallback):
    """Show the step whose caption starts with caption_start (else step
    number fallback): the steps can differ a little between recordings."""
    steps = ed.doc["steps"]
    want = next((i for i, st in enumerate(steps) if st.get("caption", "").startswith(caption_start)),
                min(fallback, len(steps)) - 1)
    ed.step_by(want - (ed.current_index() or 0)); pump(0.5)
goto('Click next to "Enter password"', 4)             # the password, blurred
ed.v_view.set("final"); ed.on_select(); pump(2.5)
shot("01-steps-editor")
# Annotations on the welcome screen (points in recording pixels)
goto('Click "Create new database"', 1)
st = ed.current_step()
st.setdefault("annotations", []).extend([
    {"kind": "number", "at": [540, 536], "n": 1},
    {"kind": "arrow", "from": [720, 676], "to": [700, 556]},
    {"kind": "text", "at": [610, 696], "text": "Start with a new database"}])
ed.set_dirty(); ed.save(wait=True); pump(1)
ed.v_view.set("final"); ed.on_select(); pump(2.5)
click(menubutton("Annotate")); pump(1)
shot("02-annotate-menu")
subprocess.run(["xdotool", "key", "Escape"]); pump(0.5)
# Record window
app.start_recording(); pump(1.5)
shot("03-record-window")
dlg = next(w for w in root.winfo_children() if isinstance(w, gui.gui_recorder.RecordDialog)); dlg.destroy(); pump()
# Dark theme, the finished step
app.set_theme("dark"); pump(1)
# The last step with something blurred: the new login with its email blurred
blurred = [i for i, st in enumerate(ed.doc["steps"]) if st.get("auto_redactions")]
ed.step_by((blurred[-1] if blurred else len(ed.doc["steps"]) - 3) - (ed.current_index() or 0))
ed.v_view.set("final"); ed.on_select(); pump(2.5)
shot("04-dark-theme")
app.set_theme("light"); pump(1)
# The update window, as someone on the previous release sees this release
import gui_help  # noqa: E402
import updates  # noqa: E402
import version  # noqa: E402
from unittest import mock  # noqa: E402
notes = (ROOT / ".github" / "releases" / f"v{version.RELEASE}.md").read_text(encoding="utf-8")
new = version.RELEASE
major, minor, patch = (int(n) for n in new.split("."))
previous = f"{major}.{minor}.{patch - 1}" if patch else f"{major}.{minor - 1}.0"
with mock.patch.object(updates, "can_install", return_value=True), \
        mock.patch.object(updates, "install_scope", return_value="ALLUSERS"), \
        mock.patch.object(gui_help.version, "RELEASE", previous):
    upd = gui_help.UpdateDialog(app, {"version": new, "url": updates.LATEST_URL,
                                      "published": version.RELEASE_DATE,
                                      "notes": notes.split("\n", 2)[2], "assets": {}})
    pump(1.5)
    # Just the window and its title bar, on the page background color
    x, y = upd.winfo_rootx() - 2, upd.winfo_rooty() - 26
    w, h = upd.winfo_width() + 4, upd.winfo_height() + 28
    subprocess.run(["import", "-window", "root", "-crop", f"{w}x{h}+{max(x, 0)}+{max(y, 0)}",
                    "+repage", str(OUT / "08-update.png")])
    print("shot 08-update", flush=True)
    upd.destroy(); pump()
# Recording in progress: KeePassXC on screen, the Recording window in the corner
wiz = subprocess.Popen([sys.executable, str(HERE / "keepassxc_demo.py"), "--static"])
pump(2)
app.start_recording(); pump(1)
dlg = next(w for w in root.winfo_children() if isinstance(w, gui.gui_recorder.RecordDialog))
dlg.v_mic.set(gui.gui_recorder.NO_MIC); dlg.start()
end = time.monotonic() + 20
while not (app.recording and app.recording.rec and app.recording.rec.recording()) and time.monotonic() < end:
    pump(0.2)
pump(4.2)
shot("05-recording")
app.recording.discard(); pump(1)
wiz.terminate()
root.deiconify(); pump(1)
import export  # noqa: E402
html = export.export(ed.out_dir, ed.doc, "html")
(OUT / "export.path").write_text(str(html))
logo = OUT.parent / "demo-logo.png"
import annotate  # noqa: E402
font = annotate.find_font()
font_opt = f"fontfile={annotate.filter_path(font)}:" if font else ""
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "color=0x1f4e8c:s=560x120",
                "-vf", f"drawtext={font_opt}text='NORTHWIND TRADERS':fontcolor=white:fontsize=42:"
                "x=(w-text_w)/2:y=(h-text_h)/2", "-frames:v", "1", str(logo)], check=True)
ed.doc["steps"][0]["narration"] = "Open KeePassXC from the applications menu."
deck = export.export(ed.out_dir, ed.doc, "pptx", logo=logo)
logo.unlink()
(OUT / "pptx.path").write_text(str(deck))
app.on_close()
