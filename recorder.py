#!/usr/bin/env python3
#
# recorder.py
# 2026-10-16
# Version: v1.1.0
#
# PURPOSE:
# The built-in screen recorder. FFmpeg records the screen (and, if chosen,
# a microphone for narration) while this module notes where and when the
# mouse is clicked and which keys are pressed, so the steps found in the
# recording can be captioned and marked automatically (see actions.py).
#
#   Windows: FFmpeg gdigrab (all monitors), dshow for the microphone
#   macOS:   FFmpeg avfoundation (main display); needs the Screen Recording
#            permission, and Input Monitoring for keys
#   Linux:   FFmpeg x11grab (X11 sessions; Wayland is not supported),
#            PulseAudio or ALSA for the microphone
#
# Input is read with the system's own functions (ctypes, no extra
# packages): on Linux the X RECORD extension reports every click and key;
# on Windows and macOS the buttons and keys are checked about 60 times a
# second, with the system's "pressed since" flags and counters so that very
# short clicks and taps are not missed. The
# text typed is never stored: letters, digits, and punctuation only count as
# "typing". Enter, Tab, Esc, function and arrow keys, and shortcuts such as
# Ctrl+S are stored by name. Keys that type a character with AltGr (Ctrl+Alt
# on Windows, such as @ or a euro sign on many European keyboards) or with
# Option on a Mac also only count as typing, so a password is never stored
# as a list of "shortcuts".
#
# Administrators can stop keys from being noted for everyone by setting the
# environment variable SCREENCAP_NO_KEYS=1 (for example with Group Policy);
# clicks are still recorded.
#
# Next to each recording, <name>.events.json holds the clicks and keys with
# their time in the recording and the screen area that was recorded.

import ctypes
import ctypes.util
import json
import os
import re
import subprocess
import sys
import threading
import time
from pathlib import Path

EVENTS_SUFFIX = ".events.json"
EVENTS_FORMAT = 1
FPS = 15
POLL_HZ = 60
DOUBLE_CLICK_TIME = 0.5      # seconds between the clicks of a double-click
DOUBLE_CLICK_DIST = 6        # pixels
DRAG_DIST = 12               # pixels the mouse must move while held to be a drag
TYPING_GAP = 3.0             # keystrokes closer than this are one "typing" action
REPEAT_GAP = 1.0             # the same key pressed again within this counts up

NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
MODIFIERS = ("Ctrl", "Alt", "Shift", "Win", "Cmd")
NAMED_KEYS = ("Enter", "Tab", "Esc", "Delete", "Up", "Down", "Left", "Right", "Home", "End",
              "PageUp", "PageDown", "Insert") + tuple(f"F{n}" for n in range(1, 13))
# Keys that only count as "typing" (their character is never stored)
TYPING = "char"


def keys_disabled_by_policy():
    """True when the administrator has switched off noting keys
    (SCREENCAP_NO_KEYS=1)."""
    return os.environ.get("SCREENCAP_NO_KEYS", "").strip().lower() in ("1", "true", "yes")


class RecorderError(Exception):
    """A problem worth showing to the user as-is."""


def load_library(name, soname):
    """A shared library by its short name, or by its file name when the
    lookup fails (inside a snap, find_library cannot see the snap's own
    libraries, but loading them by file name works). None when missing."""
    for candidate in (ctypes.util.find_library(name), soname):
        if candidate:
            try:
                return ctypes.cdll.LoadLibrary(candidate)
            except OSError:
                pass
    return None


def platform_name():
    if os.name == "nt":
        return "windows"
    if sys.platform == "darwin":
        return "macos"
    return "linux"


def unsupported_reason():
    """Why recording cannot work here, or None when it can."""
    plat = platform_name()
    if plat == "linux":
        if os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland" or (
                os.environ.get("WAYLAND_DISPLAY") and not os.environ.get("DISPLAY")):
            return ("Recording needs an X11 desktop session; this one uses Wayland, "
                    "where other programs may not capture the screen. Log out and "
                    "choose an \"on Xorg\" or \"X11\" session at the login screen, or "
                    "record with your desktop's own recorder (GNOME: Ctrl+Shift+Alt+R) "
                    "and put the file in the Recordings folder.")
        if not os.environ.get("DISPLAY"):
            return "No X11 display was found (the DISPLAY variable is not set)."
        if load_library("X11", "libX11.so.6") is None:
            return "The X11 library (libX11) was not found."
    return None


def events_path(video):
    video = Path(video)
    return video.with_name(video.stem + EVENTS_SUFFIX)


def default_name():
    return time.strftime("Recording %Y-%m-%d %H-%M-%S.mkv")


# ---------------------------------------------------------------------------
# FFmpeg command
# ---------------------------------------------------------------------------

def _run(cmd):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                          errors="replace", stdin=subprocess.DEVNULL, creationflags=NO_WINDOW)


def pick_encoder(ffmpeg):
    """Video encoder options: H.264 when FFmpeg has it, else MPEG-4."""
    out = _run([ffmpeg, "-hide_banner", "-encoders"]).stdout
    if re.search(r"^\s*V\S*\s+libx264\s", out, re.M):
        return ["-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-g", str(FPS * 10)]
    if re.search(r"^\s*V\S*\s+libopenh264\s", out, re.M):
        return ["-c:v", "libopenh264", "-b:v", "4M", "-g", str(FPS * 10)]
    return ["-c:v", "mpeg4", "-q:v", "3", "-g", str(FPS * 10)]


def list_avfoundation(ffmpeg):
    """({index: name} of video devices, {index: name} of audio devices)."""
    res = _run([ffmpeg, "-hide_banner", "-f", "avfoundation", "-list_devices", "true",
                "-i", ""])
    video, audio, section = {}, {}, None
    for line in res.stderr.splitlines():
        if "video devices" in line:
            section = video
        elif "audio devices" in line:
            section = audio
        else:
            m = re.search(r"\]\s*\[(\d+)\]\s*(.+)$", line)
            if m and section is not None:
                section[int(m.group(1))] = m.group(2).strip()
    return video, audio


def list_microphones(ffmpeg):
    """Microphones FFmpeg can record from: list of (label, spec). spec is
    passed back to command()."""
    plat = platform_name()
    if plat == "windows":
        res = _run([ffmpeg, "-hide_banner", "-list_devices", "true", "-f", "dshow",
                    "-i", "dummy"])
        names = re.findall(r'"([^"]+)"\s*\(audio\)', res.stderr)
        if not names:   # older FFmpeg lists devices under a heading instead
            section = False
            for line in res.stderr.splitlines():
                if "DirectShow audio devices" in line:
                    section = True
                elif "DirectShow video devices" in line:
                    section = False
                elif section:
                    m = re.search(r'\]\s+"([^"]+)"\s*$', line)
                    if m:
                        names.append(m.group(1))
        return [(n, n) for n in dict.fromkeys(names)]
    if plat == "macos":
        _, audio = list_avfoundation(ffmpeg)
        return [(name, str(i)) for i, name in sorted(audio.items())]
    devices = _run([ffmpeg, "-hide_banner", "-devices"]).stdout
    if re.search(r"^\s*D\S*\s+pulse\s", devices, re.M):
        return [("Default microphone", "pulse:default")]
    if re.search(r"^\s*D\S*\s+alsa\s", devices, re.M):
        return [("Default microphone", "alsa:default")]
    return []


def command(ffmpeg, dest, encoder, microphone=None, display=None, screen_index=None):
    """The FFmpeg command that records the screen into dest (.mkv). Every
    input is timestamped with the wall clock, so FFmpeg reports when the
    first frame was taken ("start:") and clicks can be placed in the video."""
    plat = platform_name()
    cmd = [ffmpeg, "-hide_banner", "-loglevel", "info", "-y"]
    clock = ["-thread_queue_size", "1024", "-use_wallclock_as_timestamps", "1"]
    audio = False
    if plat == "windows":
        cmd += clock + ["-f", "gdigrab", "-framerate", str(FPS), "-draw_mouse", "1",
                        "-i", "desktop"]
        if microphone:
            cmd += clock + ["-f", "dshow", "-i", f"audio={microphone}"]
            audio = True
    elif plat == "macos":
        if screen_index is None:
            raise RecorderError("No screen to record was found (FFmpeg lists no "
                                "\"Capture screen\" device).")
        source = f"{screen_index}:{microphone}" if microphone else f"{screen_index}:none"
        cmd += clock + ["-f", "avfoundation", "-framerate", "30", "-capture_cursor", "1",
                        "-i", source]
        audio = bool(microphone)
    else:
        cmd += clock + ["-f", "x11grab", "-framerate", str(FPS), "-draw_mouse", "1",
                        "-i", display or os.environ.get("DISPLAY", ":0")]
        if microphone:
            kind, _, name = microphone.partition(":")
            cmd += clock + ["-f", kind, "-i", name or "default"]
            audio = True
    cmd += ["-map", "0:v:0"]
    if audio:
        cmd += ["-map", "1:a:0" if plat != "macos" else "0:a:0", "-c:a", "aac", "-b:a", "128k"]
    cmd += ["-vf", "crop=trunc(iw/2)*2:trunc(ih/2)*2,format=yuv420p", "-r", str(FPS)]
    cmd += encoder + [str(dest)]
    return cmd


START_RE = re.compile(r"start:\s*([0-9]+(?:\.[0-9]+)?)")


# ---------------------------------------------------------------------------
# Reading the mouse and keyboard
# ---------------------------------------------------------------------------

class _WinPoint(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class _WinRect(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                ("right", ctypes.c_long), ("bottom", ctypes.c_long)]


class WindowsInput:
    """GetCursorPos and GetAsyncKeyState. Physical pixels, the same as the
    recording, because the polling thread asks for per-monitor DPI awareness."""

    VK = {0x0D: "Enter", 0x09: "Tab", 0x1B: "Esc", 0x2E: "Delete", 0x26: "Up", 0x28: "Down",
          0x25: "Left", 0x27: "Right", 0x24: "Home", 0x23: "End", 0x21: "PageUp",
          0x22: "PageDown", 0x2D: "Insert", 0x08: TYPING, 0x20: TYPING,
          0x11: "Ctrl", 0x12: "Alt", 0x10: "Shift", 0x5B: "Win", 0x5C: "Win"}
    VK.update({0x70 + n: f"F{n + 1}" for n in range(12)})
    VK.update({c: chr(c) for c in range(0x41, 0x5B)})        # A-Z
    VK.update({c: chr(c) for c in range(0x30, 0x3A)})        # 0-9
    VK.update({c: TYPING for c in list(range(0x60, 0x70)) + list(range(0xBA, 0xC1))
               + list(range(0xDB, 0xE0))})                   # keypad, punctuation
    BUTTONS = {0x01: "left", 0x02: "right", 0x04: "middle"}

    def __init__(self, keys=True):
        self.user32 = ctypes.WinDLL("user32", use_last_error=True)
        try:   # per-monitor aware v2, for this thread only
            self.user32.SetThreadDpiAwarenessContext.restype = ctypes.c_void_p
            self.user32.SetThreadDpiAwarenessContext(ctypes.c_void_p(-4))
        except (AttributeError, OSError):
            pass
        self.user32.GetAsyncKeyState.restype = ctypes.c_short
        self.user32.GetAncestor.restype = ctypes.c_void_p     # a window handle
        self.keys = keys
        self.codes = list(self.BUTTONS) + (list(self.VK) if keys else [])
        for vk in self.codes:   # clear the "pressed since last time" bits
            self.user32.GetAsyncKeyState(vk)

    def screen(self):
        m = self.user32.GetSystemMetrics
        return [m(76), m(77), m(78), m(79)]     # virtual screen: all monitors

    def poll(self):
        pt = _WinPoint()
        self.user32.GetCursorPos(ctypes.byref(pt))
        down = set()
        for vk in self.codes:
            # high bit: held now; low bit: pressed since the last call
            if self.user32.GetAsyncKeyState(vk) & 0x8001:
                down.add(vk)
        buttons = {name for vk, name in self.BUTTONS.items() if vk in down}
        keys = {self.VK[vk] + ("" if self.VK[vk] != TYPING else f":{vk}")
                for vk in down if vk in self.VK}
        return pt.x, pt.y, buttons, keys

    def window_rect(self, window_id):
        """Screen rectangle of a Tk window (by winfo_id), in this thread's pixels."""
        try:
            hwnd = self.user32.GetAncestor(ctypes.c_void_p(window_id), 2)   # GA_ROOT
            r = _WinRect()
            if hwnd and self.user32.GetWindowRect(ctypes.c_void_p(hwnd), ctypes.byref(r)):
                return [r.left, r.top, r.right - r.left, r.bottom - r.top]
        except OSError:
            pass
        return None


class _CGPoint(ctypes.Structure):
    _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double)]


class _CGSize(ctypes.Structure):
    _fields_ = [("width", ctypes.c_double), ("height", ctypes.c_double)]


class _CGRect(ctypes.Structure):
    _fields_ = [("origin", _CGPoint), ("size", _CGSize)]


class MacInput:
    """Quartz event source state. Points, not pixels; the recording's size
    gives the scale."""

    KEYCODES = {36: "Enter", 76: "Enter", 48: "Tab", 53: "Esc", 117: "Delete", 126: "Up",
                125: "Down", 123: "Left", 124: "Right", 115: "Home", 119: "End",
                116: "PageUp", 121: "PageDown", 51: TYPING, 49: TYPING,
                59: "Ctrl", 62: "Ctrl", 58: "Alt", 61: "Alt", 56: "Shift", 60: "Shift",
                55: "Cmd", 54: "Cmd",
                122: "F1", 120: "F2", 99: "F3", 118: "F4", 96: "F5", 97: "F6", 98: "F7",
                100: "F8", 101: "F9", 109: "F10", 103: "F11", 111: "F12"}
    LETTERS = {0: "A", 11: "B", 8: "C", 2: "D", 14: "E", 3: "F", 5: "G", 4: "H", 34: "I",
               38: "J", 40: "K", 37: "L", 46: "M", 45: "N", 31: "O", 35: "P", 12: "Q",
               15: "R", 1: "S", 17: "T", 32: "U", 9: "V", 13: "W", 7: "X", 16: "Y", 6: "Z",
               29: "0", 18: "1", 19: "2", 20: "3", 21: "4", 23: "5", 22: "6", 26: "7",
               28: "8", 25: "9"}
    PUNCTUATION = (24, 27, 30, 33, 39, 41, 42, 43, 44, 47, 50)

    def __init__(self, keys=True):
        path = ctypes.util.find_library("ApplicationServices") or \
            "/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices"
        cg = ctypes.cdll.LoadLibrary(path)
        cf = ctypes.cdll.LoadLibrary(ctypes.util.find_library("CoreFoundation") or
                                     "/System/Library/Frameworks/CoreFoundation.framework/"
                                     "CoreFoundation")
        cg.CGEventCreate.restype = ctypes.c_void_p
        cg.CGEventCreate.argtypes = [ctypes.c_void_p]
        cg.CGEventGetLocation.restype = _CGPoint
        cg.CGEventGetLocation.argtypes = [ctypes.c_void_p]
        cg.CGEventSourceButtonState.restype = ctypes.c_bool
        cg.CGEventSourceButtonState.argtypes = [ctypes.c_int32, ctypes.c_uint32]
        cg.CGEventSourceKeyState.restype = ctypes.c_bool
        cg.CGEventSourceKeyState.argtypes = [ctypes.c_int32, ctypes.c_uint16]
        cg.CGEventSourceCounterForEventType.restype = ctypes.c_uint32
        cg.CGEventSourceCounterForEventType.argtypes = [ctypes.c_int32, ctypes.c_uint32]
        cg.CGMainDisplayID.restype = ctypes.c_uint32
        cg.CGDisplayBounds.restype = _CGRect
        cg.CGDisplayBounds.argtypes = [ctypes.c_uint32]
        cf.CFRelease.argtypes = [ctypes.c_void_p]
        self.cg, self.cf = cg, cf
        names = dict(self.KEYCODES)
        names.update(self.LETTERS)
        names.update({k: TYPING for k in self.PUNCTUATION})
        self.names = names if keys else {}
        self.keys = keys
        self.counts = {}
        self.counter_changed()

    # mouse-down and key-down events counted by the system since it started
    COUNTERS = {"left": 1, "right": 3, "middle": 25, "key": 10}

    def counter_changed(self):
        """Names of the counters that went up since the last call."""
        up = set()
        for name, kind in self.COUNTERS.items():
            n = self.cg.CGEventSourceCounterForEventType(1, kind)
            if name in self.counts and n != self.counts[name]:
                up.add(name)
            self.counts[name] = n
        return up

    def screen(self):
        r = self.cg.CGDisplayBounds(self.cg.CGMainDisplayID())
        return [r.origin.x, r.origin.y, r.size.width, r.size.height]

    def poll(self):
        ev = self.cg.CGEventCreate(None)
        p = self.cg.CGEventGetLocation(ev)
        self.cf.CFRelease(ev)
        state = 1   # kCGEventSourceStateHIDSystemState
        buttons = {name for n, name in ((0, "left"), (1, "right"), (2, "middle"))
                   if self.cg.CGEventSourceButtonState(state, n)}
        keys = set()
        for code, name in self.names.items():
            if self.cg.CGEventSourceKeyState(state, code):
                keys.add(name + ("" if name != TYPING else f":{code}"))
        # a click or key press that started and ended between two checks
        up = self.counter_changed()
        buttons |= {b for b in ("left", "right", "middle") if b in up}
        if self.keys and "key" in up and not keys:
            keys.add(TYPING + ":tap")
        return p.x, p.y, buttons, keys

    def window_rect(self, window_id):
        return None


class X11Input:
    """XQueryPointer and XQueryKeymap on the X display."""

    KEYSYMS = {"Return": "Enter", "KP_Enter": "Enter", "Tab": "Tab", "ISO_Left_Tab": "Tab",
               "Escape": "Esc", "Delete": "Delete", "Up": "Up", "Down": "Down", "Left": "Left",
               "Right": "Right", "Home": "Home", "End": "End", "Prior": "PageUp",
               "Next": "PageDown", "Insert": "Insert", "BackSpace": TYPING, "space": TYPING,
               "Control_L": "Ctrl", "Control_R": "Ctrl", "Alt_L": "Alt", "Alt_R": "Alt",
               "Shift_L": "Shift", "Shift_R": "Shift", "Super_L": "Win", "Super_R": "Win"}

    def __init__(self, keys=True, display=None):
        x = load_library("X11", "libX11.so.6")
        if x is None:
            raise RecorderError("The X11 library (libX11) was not found.")
        x.XOpenDisplay.restype = ctypes.c_void_p
        x.XOpenDisplay.argtypes = [ctypes.c_char_p]
        x.XDefaultRootWindow.restype = ctypes.c_ulong
        x.XDefaultRootWindow.argtypes = [ctypes.c_void_p]
        x.XDefaultScreen.argtypes = [ctypes.c_void_p]
        x.XDisplayWidth.argtypes = [ctypes.c_void_p, ctypes.c_int]
        x.XDisplayHeight.argtypes = [ctypes.c_void_p, ctypes.c_int]
        x.XQueryPointer.argtypes = [ctypes.c_void_p, ctypes.c_ulong] + \
            [ctypes.POINTER(ctypes.c_ulong)] * 2 + [ctypes.POINTER(ctypes.c_int)] * 4 + \
            [ctypes.POINTER(ctypes.c_uint)]
        x.XQueryKeymap.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
        x.XkbKeycodeToKeysym.restype = ctypes.c_ulong
        x.XkbKeycodeToKeysym.argtypes = [ctypes.c_void_p, ctypes.c_ubyte, ctypes.c_int,
                                         ctypes.c_int]
        x.XKeysymToString.restype = ctypes.c_char_p
        x.XKeysymToString.argtypes = [ctypes.c_ulong]
        x.XCloseDisplay.argtypes = [ctypes.c_void_p]
        name = (display or os.environ.get("DISPLAY") or "").encode() or None
        self.x = x
        self.dpy = x.XOpenDisplay(name)
        if not self.dpy:
            raise RecorderError("Could not open the X display "
                                f"{(display or os.environ.get('DISPLAY') or '')!r}.")
        self.root = x.XDefaultRootWindow(self.dpy)
        self.names = {}
        if keys:
            for code in range(8, 256):
                sym = x.XkbKeycodeToKeysym(self.dpy, code, 0, 0)
                text = x.XKeysymToString(sym) if sym else None
                if not text:
                    continue
                text = text.decode("ascii", "replace")
                if text in self.KEYSYMS:
                    self.names[code] = self.KEYSYMS[text]
                elif re.fullmatch(r"F([1-9]|1[0-2])", text):
                    self.names[code] = text
                elif re.fullmatch(r"[a-zA-Z0-9]", text):
                    self.names[code] = text.upper()
                elif len(text) > 1 and text.isalpha() and text.islower() or \
                        text.startswith("KP_"):
                    self.names[code] = TYPING      # punctuation names: comma, period...

    def screen(self):
        s = self.x.XDefaultScreen(self.dpy)
        return [0, 0, self.x.XDisplayWidth(self.dpy, s), self.x.XDisplayHeight(self.dpy, s)]

    def poll(self):
        root, child = ctypes.c_ulong(), ctypes.c_ulong()
        rx, ry, wx, wy = (ctypes.c_int() for _ in range(4))
        mask = ctypes.c_uint()
        self.x.XQueryPointer(self.dpy, self.root, ctypes.byref(root), ctypes.byref(child),
                             ctypes.byref(rx), ctypes.byref(ry), ctypes.byref(wx),
                             ctypes.byref(wy), ctypes.byref(mask))
        m = mask.value
        buttons = {name for bit, name in ((8, "left"), (9, "middle"), (10, "right"))
                   if m & (1 << bit)}
        keys = set()
        if self.names:
            buf = ctypes.create_string_buffer(32)
            self.x.XQueryKeymap(self.dpy, buf)
            raw = buf.raw
            for code, name in self.names.items():
                if raw[code >> 3] & (1 << (code & 7)):
                    keys.add(name + ("" if name != TYPING else f":{code}"))
        return rx.value, ry.value, buttons, keys

    def window_rect(self, window_id):
        return None

    def close(self):
        if self.dpy:
            self.x.XCloseDisplay(self.dpy)
            self.dpy = None


class _Range8(ctypes.Structure):
    _fields_ = [("first", ctypes.c_ubyte), ("last", ctypes.c_ubyte)]


class _Range16(ctypes.Structure):
    _fields_ = [("first", ctypes.c_ushort), ("last", ctypes.c_ushort)]


class _ExtRange(ctypes.Structure):
    _fields_ = [("ext_major", _Range8), ("ext_minor", _Range16)]


class _RecordRange(ctypes.Structure):
    _fields_ = [("core_requests", _Range8), ("core_replies", _Range8),
                ("ext_requests", _ExtRange), ("ext_replies", _ExtRange),
                ("delivered_events", _Range8), ("device_events", _Range8),
                ("errors", _Range8), ("client_started", ctypes.c_int),
                ("client_died", ctypes.c_int)]


class _InterceptData(ctypes.Structure):
    _fields_ = [("id_base", ctypes.c_ulong), ("server_time", ctypes.c_ulong),
                ("client_seq", ctypes.c_ulong), ("category", ctypes.c_int),
                ("client_swapped", ctypes.c_int), ("data", ctypes.POINTER(ctypes.c_ubyte)),
                ("data_len", ctypes.c_ulong)]


_INTERCEPT = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.POINTER(_InterceptData))


class X11RecordInput(X11Input):
    """Every click and key from the X RECORD extension (as screen recorders
    and accessibility tools do), so short clicks are never missed."""

    BUTTONS = {1: "left", 2: "middle", 3: "right"}

    def __init__(self, keys=True, display=None):
        super().__init__(keys, display)
        xt = load_library("Xtst", "libXtst.so.6")
        if xt is None:
            raise RecorderError("libXtst was not found.")
        xt.XRecordQueryVersion.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_int),
                                           ctypes.POINTER(ctypes.c_int)]
        xt.XRecordAllocRange.restype = ctypes.POINTER(_RecordRange)
        xt.XRecordCreateContext.restype = ctypes.c_ulong
        xt.XRecordCreateContext.argtypes = [
            ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(ctypes.c_ulong), ctypes.c_int,
            ctypes.POINTER(ctypes.POINTER(_RecordRange)), ctypes.c_int]
        xt.XRecordEnableContext.argtypes = [ctypes.c_void_p, ctypes.c_ulong, _INTERCEPT,
                                            ctypes.c_void_p]
        xt.XRecordDisableContext.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
        xt.XRecordFreeContext.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
        xt.XRecordFreeData.argtypes = [ctypes.POINTER(_InterceptData)]
        self.x.XFlush.argtypes = [ctypes.c_void_p]
        self.x.XSync.argtypes = [ctypes.c_void_p, ctypes.c_int]
        self.xt = xt
        major, minor = ctypes.c_int(), ctypes.c_int()
        if not xt.XRecordQueryVersion(self.dpy, ctypes.byref(major), ctypes.byref(minor)):
            raise RecorderError("The X server has no RECORD extension.")
        name = (display or os.environ.get("DISPLAY") or "").encode() or None
        self.data_dpy = self.x.XOpenDisplay(name)
        if not self.data_dpy:
            raise RecorderError("Could not open a second connection to the X display.")
        rng = xt.XRecordAllocRange()
        rng.contents.device_events.first = 2      # KeyPress
        rng.contents.device_events.last = 6       # MotionNotify
        clients = ctypes.c_ulong(3)               # XRecordAllClients
        self.ctx = xt.XRecordCreateContext(self.dpy, 0, ctypes.byref(clients), 1,
                                           ctypes.byref(rng), 1)
        self.x.XSync(self.dpy, 0)
        if not self.ctx:
            raise RecorderError("Could not start listening for clicks.")
        self.buttons, self.held, self.pos = set(), set(), (0, 0)

    def run(self, feed, stop):
        """Report every click and key to feed(t, x, y, buttons, keys) until
        stop() is called from another thread."""
        def on_data(_closure, data):
            try:
                d = data.contents
                if d.category == 0 and d.data_len >= 2:      # XRecordFromServer
                    raw = ctypes.string_at(d.data, 32)
                    kind, detail = raw[0] & 0x7F, raw[1]
                    x = int.from_bytes(raw[20:22], sys.byteorder, signed=True)
                    y = int.from_bytes(raw[22:24], sys.byteorder, signed=True)
                    self.pos = (x, y)
                    changed = True
                    if kind in (4, 5) and detail in self.BUTTONS:
                        (self.buttons.add if kind == 4 else self.buttons.discard)(
                            self.BUTTONS[detail])
                    elif kind in (2, 3) and detail in self.names:
                        name = self.names[detail]
                        name += "" if name != TYPING else f":{detail}"
                        (self.held.add if kind == 2 else self.held.discard)(name)
                    else:
                        changed = False
                    if changed:
                        feed(time.time(), x, y, set(self.buttons), set(self.held))
            finally:
                self.xt.XRecordFreeData(data)
        self._callback = _INTERCEPT(on_data)     # keep a reference while enabled
        self.xt.XRecordEnableContext(self.data_dpy, self.ctx, self._callback, None)

    def stop(self):
        self.xt.XRecordDisableContext(self.dpy, self.ctx)
        self.x.XFlush(self.dpy)

    def close(self):
        try:
            self.xt.XRecordFreeContext(self.dpy, self.ctx)
        except OSError:
            pass
        if self.data_dpy:
            self.x.XCloseDisplay(self.data_dpy)
            self.data_dpy = None
        super().close()


def open_input(keys=True, display=None):
    plat = platform_name()
    if plat == "windows":
        return WindowsInput(keys)
    if plat == "macos":
        return MacInput(keys)
    try:
        return X11RecordInput(keys, display)
    except (RecorderError, OSError, AttributeError):
        return X11Input(keys, display)


# ---------------------------------------------------------------------------
# Turning samples into actions
# ---------------------------------------------------------------------------

def _inside(rect, x, y):
    return rect is not None and rect[0] <= x < rect[0] + rect[2] and \
        rect[1] <= y < rect[1] + rect[3]


class EventLog:
    """Turns mouse and keyboard samples into actions: clicks (and
    double-clicks), drags, named keys, shortcuts, and typing. Times are
    whatever clock the caller uses (seconds)."""

    def __init__(self, option_types=None):
        self.events = []
        # On a Mac, Option with a key types a character (Option+2 is a
        # trademark sign), so it is typing, not a shortcut
        self.option_types = sys.platform == "darwin" if option_types is None else option_types
        self.buttons = set()
        self.keys = set()
        self.press = {}          # button -> (t, x, y)
        self.ignore = None       # screen rectangle whose clicks are dropped

    def feed(self, t, x, y, buttons, keys):
        for b in sorted(buttons - self.buttons):
            self.press[b] = (t, x, y)
        for b in sorted(self.buttons - buttons):
            if b in self.press:
                self._release(b, self.press.pop(b), x, y)
        held = {k for k in keys if k in MODIFIERS}
        for k in sorted(keys - self.keys):
            if k not in MODIFIERS:
                self._key(t, k, held)
        self.buttons, self.keys = set(buttons), set(keys)

    def _release(self, button, press, x, y):
        t, px, py = press
        if _inside(self.ignore, px, py):
            return
        if max(abs(x - px), abs(y - py)) >= DRAG_DIST:
            self.events.append({"t": t, "type": "drag", "button": button,
                                "x": px, "y": py, "x2": x, "y2": y})
            return
        last = self.events[-1] if self.events else None
        if last and last["type"] == "click" and last["button"] == button and \
                t - last.get("t_last", last["t"]) <= DOUBLE_CLICK_TIME and \
                max(abs(px - last["x"]), abs(py - last["y"])) <= DOUBLE_CLICK_DIST:
            last["count"] = last.get("count", 1) + 1
            last["t_last"] = t
            return
        self.events.append({"t": t, "type": "click", "button": button, "x": px, "y": py,
                            "count": 1})

    def _key(self, t, key, held):
        last = self.events[-1] if self.events else None
        mods = [m for m in MODIFIERS if m in held]
        types_char = key.startswith(TYPING) or (len(key) == 1 and key.isalnum())
        # AltGr (seen as Ctrl+Alt) or a Mac's Option, with or without Shift,
        # types a character: count it as typing so the character is never kept
        altgr = {"Ctrl", "Alt"} <= set(mods) or (self.option_types and "Alt" in mods)
        if types_char and altgr and set(mods) <= {"Ctrl", "Alt", "Shift"}:
            mods = []
        if any(m != "Shift" for m in mods):
            name = key if not key.startswith(TYPING) else None
            if name:
                self.events.append({"t": t, "type": "shortcut", "keys": "+".join(mods + [name])})
            return
        if types_char:
            if last and last["type"] == "typing" and t - last["t_last"] <= TYPING_GAP:
                last["count"] += 1
                last["t_last"] = t
            else:
                self.events.append({"t": t, "type": "typing", "count": 1, "t_last": t})
            return
        if key in NAMED_KEYS:
            name = ("Shift+" + key) if "Shift" in mods else key
            if last and last["type"] == "key" and last["key"] == name and \
                    t - last["t_last"] <= REPEAT_GAP:
                last["count"] += 1
                last["t_last"] = t
            else:
                self.events.append({"t": t, "type": "key", "key": name, "count": 1,
                                    "t_last": t})

    def result(self, offset=0.0, until=None):
        """Events with times moved into the recording (t - offset), without
        the ones after `until` (the click on Stop)."""
        out = []
        for e in self.events:
            if until is not None and e["t"] > until:
                continue
            e = {k: v for k, v in e.items() if k != "t_last"}
            e["t"] = round(e["t"] - offset, 3)
            if e["t"] >= 0:
                out.append(e)
        return out


# ---------------------------------------------------------------------------
# Recording
# ---------------------------------------------------------------------------

class Recorder:
    """Records the screen into dest until stop() or cancel(). Runs FFmpeg
    and an input-polling thread; safe to drive from a GUI thread."""

    def __init__(self, ffmpeg, dest, microphone=None, keys=True, display=None,
                 log=None):
        self.ffmpeg = ffmpeg
        self.dest = Path(dest)
        self.microphone = microphone
        self.keys = keys and not keys_disabled_by_policy()
        self.display = display
        self.log = log
        self.proc = None
        self.started_wall = None      # wall clock time of the recording's first frame
        self.stderr_tail = []
        self.events = EventLog()
        self.screen = None
        self.ignore_window = None     # (Tk window id, fallback rect) of our own window
        self._stop = threading.Event()
        self._poll_error = None
        self._threads = []

    # -- control

    def start(self):
        reason = unsupported_reason()
        if reason:
            raise RecorderError(reason)
        if not self.ffmpeg:
            raise RecorderError("FFmpeg was not found.")
        self.dest.parent.mkdir(parents=True, exist_ok=True)
        screen_index = None
        if platform_name() == "macos":
            video, _ = list_avfoundation(self.ffmpeg)
            screen_index = next((i for i, n in sorted(video.items())
                                 if n.lower().startswith("capture screen")), None)
        cmd = command(self.ffmpeg, self.dest, pick_encoder(self.ffmpeg), self.microphone,
                      self.display, screen_index)
        poll = threading.Thread(target=self._poll, daemon=True)
        self._threads.append(poll)
        poll.start()
        try:
            self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                                         stderr=subprocess.PIPE, creationflags=NO_WINDOW)
        except OSError as exc:
            self._finish(2)   # stop reading clicks and keys again
            raise RecorderError(f"FFmpeg could not be started: {exc}") from exc
        reader = threading.Thread(target=self._read_stderr, daemon=True)
        self._threads.append(reader)
        reader.start()

    def running(self):
        return self.proc is not None and self.proc.poll() is None

    def recording(self):
        """True once the first frame is in."""
        return self.started_wall is not None and self.running()

    def elapsed(self):
        return max(0.0, time.time() - self.started_wall) if self.started_wall else 0.0

    def set_ignore_window(self, window_id, rect=None):
        """Clicks on this window (the recorder's own controls) are dropped.
        rect is its screen rectangle as Tk sees it; on Windows the window's
        own rectangle is looked up, since Tk and the recording can count
        pixels differently on high-DPI screens."""
        self.ignore_window = (window_id, rect)
        if rect is not None:
            self.events.ignore = rect

    def stop(self, timeout=20):
        """Finish the recording and write the events file. Returns the video
        path. Raises RecorderError when FFmpeg failed."""
        stopped_at = time.time()
        self._finish(timeout)
        if not self.dest.is_file() or self.dest.stat().st_size == 0:
            raise RecorderError("The recording could not be made. FFmpeg said:\n" +
                                self.error_text())
        if self.started_wall is None:
            raise RecorderError("FFmpeg did not report when the recording started, so "
                                "clicks cannot be placed in it. FFmpeg said:\n" +
                                self.error_text())
        events = self.events.result(self.started_wall, until=stopped_at - 0.4)
        data = {"format": EVENTS_FORMAT, "platform": platform_name(),
                "screen": self.screen, "events": events,
                "keys": bool(self.keys), "recorded": time.strftime("%Y-%m-%d %H:%M:%S")}
        if self._poll_error:
            data["input_error"] = self._poll_error
        tmp = events_path(self.dest).with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=1), encoding="utf-8")
        os.replace(tmp, events_path(self.dest))
        return self.dest

    def cancel(self):
        self._finish(10)
        for p in (self.dest, events_path(self.dest)):
            try:
                p.unlink()
            except OSError:
                pass

    def _finish(self, timeout):
        self._stop.set()
        source = getattr(self, "_source", None)
        if source is not None:
            try:
                source.stop()
            except Exception:
                pass
        if self.proc is not None and self.proc.poll() is None:
            try:
                self.proc.stdin.write(b"q")
                self.proc.stdin.flush()
                self.proc.stdin.close()
            except OSError:
                pass
            try:
                self.proc.wait(timeout)
            except subprocess.TimeoutExpired:
                self.proc.terminate()
                try:
                    self.proc.wait(5)
                except subprocess.TimeoutExpired:
                    self.proc.kill()
        for t in self._threads:
            t.join(2)

    def error_text(self):
        lines = [ln for ln in self.stderr_tail if ln.strip()]
        return "\n".join(lines[-12:]) or "(no output)"

    # -- threads

    def _read_stderr(self):
        input_seen = False
        for raw in iter(self.proc.stderr.readline, b""):
            line = raw.decode("utf-8", "replace").rstrip()
            self.stderr_tail = (self.stderr_tail + [line])[-60:]
            if line.startswith("Input #0"):
                input_seen = True
            elif input_seen and self.started_wall is None:
                m = START_RE.search(line)
                if m:
                    start = float(m.group(1))
                    # the wall clock, as asked for; anything else means a
                    # device ignored the option, so use the time it opened
                    self.started_wall = start if abs(start - time.time()) < 30 \
                        else time.time()
            if self.started_wall is None and line.startswith("Press [q]"):
                self.started_wall = time.time()
        self.proc.stderr.close()

    def _poll(self):
        try:
            source = open_input(self.keys, self.display)
        except Exception as exc:     # recording still works without input
            self._poll_error = f"Clicks and keys could not be read: {exc}"
            if self.log:
                self.log.warning(self._poll_error)
            return
        try:
            self.screen = list(source.screen())
            if hasattr(source, "run"):      # reports events as they happen
                self._source = source
                if self._stop.is_set():
                    return
                source.run(self.events.feed, self._stop)
                return
            period = 1.0 / POLL_HZ
            n = 0
            while not self._stop.is_set():
                if n % 30 == 0 and self.ignore_window:
                    wid, rect = self.ignore_window
                    self.events.ignore = (source.window_rect(wid) if wid else None) or rect
                n += 1
                x, y, buttons, keys = source.poll()
                self.events.feed(time.time(), x, y, buttons, keys)
                time.sleep(period)
        except Exception as exc:
            self._poll_error = f"Reading clicks and keys stopped: {exc}"
            if self.log:
                self.log.warning(self._poll_error)
        finally:
            close = getattr(source, "close", None)
            if close:
                close()


def hide_from_capture(window_id):
    """Leave a window (by Tk winfo_id) out of screen captures, so the
    recorder's own controls are not in the recording. Windows 10 2004 and
    later only; returns True when it worked."""
    if platform_name() != "windows":
        return False
    try:
        user32 = ctypes.WinDLL("user32")
        user32.GetAncestor.restype = ctypes.c_void_p
        hwnd = user32.GetAncestor(ctypes.c_void_p(window_id), 2)     # GA_ROOT
        return bool(hwnd and user32.SetWindowDisplayAffinity(ctypes.c_void_p(hwnd), 0x11))
    except (AttributeError, OSError):
        return False


def load_events(video):
    """The events file of a recording, or None."""
    try:
        data = json.loads(events_path(video).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict) or not isinstance(data.get("events"), list):
        return None
    return data
