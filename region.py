#!/usr/bin/env python3
#
# region.py
# 2026-11-11
# Version: v1.0.0
#
# PURPOSE:
# How dates and times are written in what the app shows and makes: the
# date on exported documents, the "Generated" line of steps.md, and the
# times in the Archived Recordings window. The date format and the clock
# (12 or 24 hours) are either the system's own (Windows: Settings > Time &
# language > Language & region; macOS and Linux: the locale) or chosen in
# View > Advanced Settings > Region (command line: --date-format, --clock).
#
# File names and stored values (events.json, archive.json) always stay in
# ISO form (2026-11-22 14:05:00), so they sort and read the same anywhere.

import locale
import os
import re
import time

from i18n import N_

# Choice -> (label, strftime pattern); labels are translated where shown. "system" asks the operating system.
DATE_FORMATS = {
    "system": (N_("System setting"), None),
    "iso": (N_("2026-11-22 (year-month-day)"), "%Y-%m-%d"),
    "us": (N_("11/22/2026 (month/day/year)"), "%m/%d/%Y"),
    "dmy": (N_("22/11/2026 (day/month/year)"), "%d/%m/%Y"),
    "dmy-dot": (N_("22.11.2026 (day.month.year)"), "%d.%m.%Y"),
}
CLOCKS = {
    "system": N_("System setting"),
    "24": N_("24-hour (14:05)"),
    "12": N_("12-hour (2:05 PM)"),
}
STORED = "%Y-%m-%d %H:%M:%S"     # how times are kept in files

_choice = {"date": "system", "clock": "system"}
_system = {}                     # cached answers from the operating system


def configure(date_format=None, clock=None):
    """Set the date format and clock (keys of DATE_FORMATS and CLOCKS);
    unknown values fall back to the system setting."""
    if date_format is not None:
        _choice["date"] = date_format if date_format in DATE_FORMATS else "system"
    if clock is not None:
        _choice["clock"] = clock if clock in CLOCKS else "system"


def settings():
    return dict(_choice)


# --------------------------------------------------------------------------
# The operating system's own formats
# --------------------------------------------------------------------------

def _windows_locale_info(kind):
    """A Windows regional setting of the user (LOCALE_SSHORTDATE 0x1F,
    LOCALE_STIMEFORMAT 0x1003), or None."""
    try:
        import ctypes
        buf = ctypes.create_unicode_buffer(100)
        if ctypes.windll.kernel32.GetLocaleInfoEx(None, kind, buf, len(buf)):
            return buf.value
    except (AttributeError, OSError):
        pass
    return None


def windows_to_strftime(pattern):
    """Turn a Windows date or time picture ("M/d/yyyy", "h:mm:ss tt") into
    a strftime pattern. Day and month names stay as numbers."""
    tokens = [
        ("yyyy", "%Y"), ("yy", "%y"), ("y", "%Y"),
        ("MMMM", "%m"), ("MMM", "%m"), ("MM", "%m"), ("M", "%m"),
        ("dddd", "%d"), ("ddd", "%d"), ("dd", "%d"), ("d", "%d"),
        ("HH", "%H"), ("H", "%H"), ("hh", "%I"), ("h", "%I"),
        ("mm", "%M"), ("m", "%M"), ("ss", "%S"), ("s", "%S"),
        ("tt", "%p"), ("t", "%p"),
    ]
    out, i = "", 0
    while i < len(pattern):
        if pattern[i] == "'":            # quoted text
            end = pattern.find("'", i + 1)
            end = len(pattern) if end < 0 else end
            out += pattern[i + 1:end].replace("%", "%%")
            i = end + 1
            continue
        for tok, rep in tokens:
            if pattern.startswith(tok, i):
                out += rep
                i += len(tok)
                break
        else:
            out += pattern[i].replace("%", "%%")
            i += 1
    return out


def _posix_format(item):
    try:
        locale.setlocale(locale.LC_TIME, "")
        return locale.nl_langinfo(item) or None
    except (AttributeError, locale.Error, ValueError):
        return None


def system_date_format():
    """The system's short date as a strftime pattern (ISO when unknown)."""
    if "date" not in _system:
        fmt = None
        if os.name == "nt":
            pic = _windows_locale_info(0x1F)
            fmt = windows_to_strftime(pic) if pic else None
        elif hasattr(locale, "D_FMT"):
            fmt = _posix_format(locale.D_FMT)
        if fmt == "%D":                  # the C locale: month/day/two-digit year
            fmt = "%m/%d/%y"
        if fmt:                          # a two-digit year is not clear enough
            fmt = fmt.replace("%y", "%Y")
        _system["date"] = fmt or "%Y-%m-%d"
    return _system["date"]


def system_uses_12_hours():
    """True when the system clock shows AM/PM."""
    if "clock" not in _system:
        twelve = False
        if os.name == "nt":
            pic = _windows_locale_info(0x1003)
            twelve = bool(pic) and "h" in pic.replace("hh", "h") and "H" not in pic
        elif hasattr(locale, "T_FMT"):
            fmt = _posix_format(locale.T_FMT) or ""
            ampm = _posix_format(getattr(locale, "T_FMT_AMPM", locale.T_FMT)) or ""
            twelve = "%p" in fmt or "%r" in fmt or ("%I" in fmt and bool(ampm))
        _system["clock"] = twelve
    return _system["clock"]


# --------------------------------------------------------------------------
# Writing dates and times
# --------------------------------------------------------------------------

def date_pattern():
    choice = DATE_FORMATS.get(_choice["date"], DATE_FORMATS["system"])[1]
    return choice or system_date_format()


def time_pattern(seconds=False):
    twelve = {"24": False, "12": True}.get(_choice["clock"])
    if twelve is None:
        twelve = system_uses_12_hours()
    if twelve:
        return "%I:%M:%S %p" if seconds else "%I:%M %p"
    return "%H:%M:%S" if seconds else "%H:%M"


def _strip_hour_zero(text):
    """'02:05 PM' -> '2:05 PM' (strftime has no portable no-padding flag)."""
    return re.sub(r"(^|\s)0(\d:\d\d)", r"\1\2", text)


def format_date(t=None):
    """A date (time.time() value, struct_time, or now) in the chosen format."""
    st = time.localtime(t) if t is None or isinstance(t, (int, float)) else t
    return time.strftime(date_pattern(), st)


def format_datetime(t=None, seconds=False):
    """Date and time in the chosen formats."""
    st = time.localtime(t) if t is None or isinstance(t, (int, float)) else t
    return _strip_hour_zero(time.strftime(f"{date_pattern()} {time_pattern(seconds)}", st))


def format_stored(text, seconds=False):
    """A time kept in a file (2026-11-22 14:05:00) in the chosen formats;
    the text unchanged when it is not in that form."""
    try:
        return format_datetime(time.strptime(text, STORED), seconds)
    except (TypeError, ValueError):
        return text
