#!/usr/bin/env python3
#
# gui_shots.py
# 2026-10-13
# Version: v1.0.0
#
# PURPOSE:
# Opens the GUI on the demo recording made by make_screenshots.sh and takes
# the store screenshots: the Steps tab, the Annotate menu, the Record
# window, the dark theme, and a recording in progress. Also exports the
# demo as HTML for the document screenshot. Run by make_screenshots.sh.
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
ed.v_doc_title.set("Install Example App 4.2"); ed.v_doc_version.set("v1.0.0"); ed.v_doc_author.set("IT Service Desk")
ed.save(wait=True); pump(1)
for _ in range(2): ed.step_by(1); pump(0.3)          # step 3: product key, blurred
ed.v_view.set("final"); ed.on_select(); pump(2.5)
shot("01-steps-editor")
# Annotations on the license step
ed.step_by(-1); pump(0.5)
st = ed.current_step()
st.setdefault("annotations", []).extend([
    {"kind": "number", "at": [438, 456], "n": 1},
    {"kind": "arrow", "from": [640, 520], "to": [522, 468]},
    {"kind": "text", "at": [600, 505], "text": "Accept the license first"},
    {"kind": "number", "at": [770, 586], "n": 2}])
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
for _ in range(5): ed.step_by(1); pump(0.3)
ed.v_view.set("final"); ed.on_select(); pump(2.5)
shot("04-dark-theme")
app.set_theme("light"); pump(1)
# Recording in progress: the wizard on screen, the Recording window in the corner
env = dict(os.environ, WIZARD_MANUAL="1")
wiz = subprocess.Popen([sys.executable, str(HERE / "demo_wizard.py")], env=env)
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
app.on_close()
