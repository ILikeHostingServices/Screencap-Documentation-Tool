#!/usr/bin/env python3
#
# gui_shots.py
# 2026-10-26
# Version: v1.5.0
#
# PURPOSE:
# Opens the GUI on the three demo recordings made by make_screenshots.sh
# (made-up sample data from sample_data/: Gordon Freeman's onboarding web
# form and staff directory entry at the Black Mesa Research Facility, and a
# Harris & Thompson partner's tax portal login saved in KeePassXC)
# and takes the store screenshots: the Steps tab, the Annotate menu, the
# Record window, the dark theme, a recording in progress, and the update
# window (as a user of the previous release sees this one). Also exports
# the web form steps as HTML and the KeePassXC steps as PowerPoint (with a
# made-up logo) for the document screenshots. Run by make_screenshots.sh.
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
ed = app.editor
TITLES = {"Fill in the onboarding form": "Onboard a new employee (HR web form)",
          "Add an employee to the staff directory": "Add a new employee to the staff directory",
          "Save a login in KeePassXC": "Save the federal tax portal login in KeePassXC"}
def open_recording(name):
    """Show the steps of the recording called name, with its document title."""
    iid = next(i for i, (video, _) in app.videos.items() if video.stem == name)
    app.tree.selection_set(iid); pump(); app.show_steps(); pump(1)
    if ed.v_doc_title.get() != TITLES[name]:
        ed.v_doc_title.set(TITLES[name]); ed.v_doc_version.set("v1.0.0"); ed.v_doc_author.set("IT Service Desk")
        ed.save(wait=True); pump(1)
open_recording("Save a login in KeePassXC")
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
# Annotations on the finished web form (points in recording pixels)
open_recording("Fill in the onboarding form")
goto('Click "Submit"', len(ed.doc["steps"]) - 1)
st = ed.current_step()
st.setdefault("annotations", []).extend([
    {"kind": "number", "at": [236, 681], "n": 1},
    {"kind": "arrow", "from": [600, 760], "to": [400, 695]},
    {"kind": "text", "at": [610, 750], "text": "Check every field, then submit"}])
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
# The staff directory after sorting, the email addresses blurred
open_recording("Add an employee to the staff directory")
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
# Recording in progress: the web form on screen, the Recording window in the corner
wiz = subprocess.Popen([sys.executable, str(HERE / "web_demo.py"), "--static"])
pump(4)
app.start_recording(); pump(1)
dlg = next(w for w in root.winfo_children() if isinstance(w, gui.gui_recorder.RecordDialog))
dlg.v_mic.set(gui.gui_recorder.NO_MIC); dlg.start()
end = time.monotonic() + 20
while not (app.recording and app.recording.rec and app.recording.rec.recording()) and time.monotonic() < end:
    pump(0.2)
pump(4.2)
shot("05-recording")
app.recording.discard(); pump(1)
wiz.terminate(); wiz.wait(10)
root.deiconify(); pump(1)
import export  # noqa: E402
open_recording("Fill in the onboarding form")
html = export.export(ed.out_dir, ed.doc, "html")
(OUT / "export.path").write_text(str(html))
logo = OUT.parent / "demo-logo.png"
import annotate  # noqa: E402
font = annotate.find_font()
font_opt = f"fontfile={annotate.filter_path(font)}:" if font else ""
open_recording("Save a login in KeePassXC")
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "color=0x1f3a5f:s=560x120",
                "-vf", f"drawtext={font_opt}text='HARRIS & THOMPSON':fontcolor=white:fontsize=40:"
                "x=(w-text_w)/2:y=(h-text_h)/2", "-frames:v", "1", str(logo)], check=True)
ed.doc["steps"][0]["narration"] = "Open KeePassXC from the applications menu."
deck = export.export(ed.out_dir, ed.doc, "pptx", logo=logo)
logo.unlink()
(OUT / "pptx.path").write_text(str(deck))
app.on_close()
