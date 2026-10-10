#!/usr/bin/env python3
#
# presets.py
# 2026-10-10
# Version: v1.2.0
#
# PURPOSE:
# Named sets of detection and output settings. A few presets are built in
# (tuned for common kinds of recordings) and you can save your own. User
# presets live in your profile, next to the GUI settings, and are shared by
# the GUI and the command line (--preset NAME). Names are matched without
# regard to case, so settings saved before v1.23.0 (when the built-in names
# were in sentence case, e.g. "Web console") still find their preset.

import json
import os
from pathlib import Path

# Settings a preset can hold (argparse destination names in screencap.py)
KEYS = ("threshold", "debounce", "capture_point", "settle", "lead", "max_wait",
        "min_gap", "analyze_fps", "analyze_width", "format", "no_dedup",
        "dedup_threshold", "no_highlight", "no_redact", "redact_pattern")

BUILTIN = {
    "Installer Wizard": {
        "_about": "The defaults. Setup wizards and settings dialogs with clear pauses between steps.",
    },
    "General Desktop Use": {
        "_about": "Moving around the operating system: opening apps, browsing files, and "
                  "flipping through menus. No blurring and no red boxes.",
        "threshold": 0.003, "debounce": 0.8, "min_gap": 0.8,
        "no_highlight": True, "no_redact": True,
    },
    "Web Console": {
        "_about": "Admin portals and web apps: ignores spinners and slow-loading pages.",
        "threshold": 0.008, "debounce": 2.0, "max_wait": 15.0, "min_gap": 1.5,
    },
    "Terminal / Command Line": {
        "_about": "Shells and consoles: catches small text changes, merges bursts of typing.",
        "threshold": 0.002, "debounce": 1.5, "min_gap": 1.0, "analyze_width": 0,
    },
    "Remote Desktop / VM Console": {
        "_about": "RDP, VNC, and virtual machine consoles: ignores compression noise and "
                  "waits for a laggy screen to finish drawing.",
        "threshold": 0.01, "debounce": 2.0, "settle": 1.0, "max_wait": 20.0, "min_gap": 1.5,
    },
    "Forms and Spreadsheets": {
        "_about": "Filling in forms, tickets, and spreadsheets: catches small field changes "
                  "and merges a whole entry being typed into one step.",
        "threshold": 0.002, "debounce": 2.5, "min_gap": 1.5, "analyze_width": 1280,
    },
    "Slideshow / Presentation": {
        "_about": "Slide decks and click-through demos: one screenshot per slide, no red "
                  "boxes, and no forced shots on slides shown for a long time.",
        "threshold": 0.02, "debounce": 0.5, "max_wait": 60.0, "min_gap": 1.0,
        "no_highlight": True, "no_redact": True,
    },
    "Video Meeting / Screen Share": {
        "_about": "Recorded calls and screen shares: ignores webcam and video movement, "
                  "keeps the blurring on for names and email addresses.",
        "threshold": 0.03, "debounce": 3.0, "max_wait": 30.0, "min_gap": 3.0,
        "analyze_fps": 2.0, "no_highlight": True,
    },
    "Fast Clicking": {
        "_about": "Recordings with short pauses between actions.",
        "debounce": 0.5, "min_gap": 0.5, "lead": 0.15, "analyze_fps": 10.0,
    },
}


def settings_dir():
    """Per-user settings folder (outside the install folder and the repo)."""
    if os.name == "nt":
        return Path(os.environ.get("APPDATA", Path.home())) / "ScreencapDocTool"
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "screencap-doc-tool"


def user_file():
    return settings_dir() / "presets.json"


def load_user():
    try:
        data = json.loads(user_file().read_text(encoding="utf-8"))
        return {k: v for k, v in data.items() if isinstance(v, dict)}
    except (OSError, ValueError):
        return {}


def _write_user(data):
    path = user_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def all_presets():
    """Built-in presets first, then the user's, in name order."""
    merged = dict(BUILTIN)
    builtin = {key.lower() for key in BUILTIN}
    for name, values in sorted(load_user().items()):
        if name.strip().lower() not in builtin:
            merged[name] = values
    return merged


def names():
    return list(all_presets())


DEFAULT = "Installer Wizard"


def canonical(name):
    """The preset's name as listed (ignoring case and spaces around it), or None."""
    wanted = (name or "").strip().lower()
    for key in all_presets():
        if key.lower() == wanted:
            return key
    return None


def get(name):
    """Settings for a preset (without the description), or None. Matching
    ignores case so the command line is forgiving."""
    key = canonical(name)
    if key is None:
        return None
    return {k: v for k, v in all_presets()[key].items() if k in KEYS}


def describe(name):
    key = canonical(name)
    return all_presets()[key].get("_about", "Your saved preset.") if key else "Your saved preset."


def is_builtin(name):
    wanted = (name or "").strip().lower()
    return any(key.lower() == wanted for key in BUILTIN)


def save_user(name, values, about=None):
    name = name.strip()
    if not name:
        raise ValueError("A preset needs a name.")
    if is_builtin(name):
        raise ValueError(f'"{name}" is a built-in preset. Choose another name.')
    data = load_user()
    data[name] = {k: v for k, v in values.items() if k in KEYS}
    if about:
        data[name]["_about"] = about
    _write_user(data)


def delete_user(name):
    if is_builtin(name):
        raise ValueError("Built-in presets cannot be deleted.")
    data = load_user()
    if data.pop(name, None) is not None:
        _write_user(data)
        return True
    return False
