#!/usr/bin/env python3
#
# presets.py
# 2026-10-02
# Version: v1.0.0
#
# PURPOSE:
# Named sets of detection and output settings. A few presets are built in
# (tuned for common kinds of recordings) and you can save your own. User
# presets live in your profile, next to the GUI settings, and are shared by
# the GUI and the command line (--preset NAME).

import json
import os
from pathlib import Path

# Settings a preset can hold (argparse destination names in screencap.py)
KEYS = ("threshold", "debounce", "capture_point", "settle", "lead", "max_wait",
        "min_gap", "analyze_fps", "analyze_width", "format", "no_dedup",
        "dedup_threshold", "no_highlight", "no_redact", "redact_pattern")

BUILTIN = {
    "Installer wizard": {
        "_about": "The defaults. Setup wizards and settings dialogs with clear pauses between steps.",
    },
    "Web console": {
        "_about": "Admin portals and web apps: ignores spinners and slow-loading pages.",
        "threshold": 0.008, "debounce": 2.0, "max_wait": 15.0, "min_gap": 1.5,
    },
    "Terminal / command line": {
        "_about": "Shells and consoles: catches small text changes, merges bursts of typing.",
        "threshold": 0.002, "debounce": 1.5, "min_gap": 1.0, "analyze_width": 0,
    },
    "Fast clicking": {
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
    for name, values in sorted(load_user().items()):
        if name not in BUILTIN:
            merged[name] = values
    return merged


def names():
    return list(all_presets())


def get(name):
    """Settings for a preset (without the description), or None. Matching
    ignores case so the command line is forgiving."""
    for key, values in all_presets().items():
        if key.lower() == (name or "").strip().lower():
            return {k: v for k, v in values.items() if k in KEYS}
    return None


def describe(name):
    return all_presets().get(name, {}).get("_about", "Your saved preset.")


def is_builtin(name):
    return name in BUILTIN


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
