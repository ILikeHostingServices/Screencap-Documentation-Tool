#!/usr/bin/env python3
#
# i18n.py
# 2026-11-11
# Version: v1.0.0
#
# PURPOSE:
# The language of the app's windows: English, Spanish, French, German, or
# Portuguese (Brazil). The system's own language is used unless one is
# chosen in View > Language (it applies the next time the app starts).
# Text that is not translated yet stays in English.
#
# In the code, user-facing text is wrapped in _(): _("Process All"), or
# _("Saved {n} step(s)").format(n=3) for text with values in it (the
# translation keeps the same {names}). The translations are in
# translations.py, one dictionary per language. Text defined before the
# language is chosen is marked N_("...") and translated where it is shown.
# The translations are kept as Python, so every package of the
# app carries them without extra files.

import locale
import os
import subprocess
import sys

# Code -> the language's own name, as shown in View > Language
LANGUAGES = {
    "en": "English",
    "es": "Español",
    "fr": "Français",
    "de": "Deutsch",
    "pt_BR": "Português (Brasil)",
}
SYSTEM = "system"

_catalog = {}
_current = "en"


def _normalize(tag):
    """'es_MX.UTF-8', 'pt-BR', 'pt_PT' -> a code of LANGUAGES, or None.
    Any Portuguese uses the Brazilian translation."""
    if not tag:
        return None
    tag = tag.split(".")[0].split("@")[0].replace("-", "_")
    lang = tag.split("_")[0].lower()
    if lang == "pt":
        return "pt_BR"
    return lang if lang in LANGUAGES else None


def _windows_ui_language():
    try:
        import ctypes
        lcid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
        return locale.windows_locale.get(lcid)
    except (AttributeError, OSError):
        return None


def _mac_language():
    try:
        out = subprocess.run(["defaults", "read", "-g", "AppleLanguages"],
                             capture_output=True, text=True, timeout=5).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    for line in out.splitlines():
        line = line.strip().strip('",()')
        if line:
            return line
    return None


def system_language():
    """The code of the system's language when it is one of LANGUAGES,
    else "en"."""
    candidates = []
    if os.name == "nt":
        candidates.append(_windows_ui_language())
    for var in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        value = os.environ.get(var)
        if value:
            candidates.extend(value.split(":"))
    if sys.platform == "darwin":
        candidates.append(_mac_language())
    for tag in candidates:
        code = _normalize(tag)
        if code:
            return code
    return "en"


def set_language(code):
    """Use a language (a code of LANGUAGES, or "system"). Returns the code
    in use."""
    global _current, _catalog
    if code == SYSTEM or code not in LANGUAGES:
        code = system_language()
    _current = code
    if code == "en":
        _catalog = {}
    else:
        import translations
        _catalog = translations.CATALOGS.get(code, {})
    return code


def current():
    return _current


def gettext(text):
    """The translation of text in the current language, or text itself."""
    return _catalog.get(text) or text


_ = gettext


def N_(text):
    """Marks text to translate later, where it is defined before the
    language is chosen (module constants): translate it with _() where it
    is shown."""
    return text
