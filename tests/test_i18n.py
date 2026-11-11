#!/usr/bin/env python3
#
# test_i18n.py
# 2026-11-11
# Version: v1.0.0
#
# PURPOSE:
# Tests for the app's languages (i18n.py and translations.py): every text the
# windows show has a translation in each language with the same {names},
# no translation is left over for text the code no longer uses, the
# system's language is recognised (es_MX.UTF-8, pt-PT, and so on), and a
# missing text falls back to English; and the Windows installer has every
# text of its own in each language. The app in Spanish is in test_gui.py.
#
# Run from the repository root:
#   python -m unittest discover -s tests -v

import ast
import re
import unittest
from unittest import mock

from helpers import ROOT

import i18n  # noqa: E402
import translations  # noqa: E402

# The files whose text is wrapped in _() or N_()
SOURCES = ("screencap_gui.pyw", "gui_recorder.py", "gui_archive.py", "gui_editor.py",
           "region.py")
NAMES = re.compile(r"\{(\w*)\}")


def texts_in_code():
    """English text in _("...") and N_("...") -> where it is."""
    found = {}
    for name in SOURCES:
        tree = ast.parse((ROOT / name).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                    and node.func.id in ("_", "N_") and node.args):
                arg = node.args[0]
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    found.setdefault(arg.value, f"{name}:{node.lineno}")
    return found


class TranslationTests(unittest.TestCase):
    def tearDown(self):
        i18n.set_language("en")

    def test_every_text_is_translated_with_the_same_names(self):
        texts = texts_in_code()
        self.assertGreater(len(texts), 300)
        self.assertEqual(set(translations.CATALOGS), set(i18n.LANGUAGES) - {"en"})
        for code, catalog in translations.CATALOGS.items():
            missing = [f"{where}: {text!r}" for text, where in texts.items()
                       if not catalog.get(text)]
            self.assertEqual(missing, [], f"not translated into {code}")
            for text, translated in catalog.items():
                self.assertEqual(sorted(NAMES.findall(translated)), sorted(NAMES.findall(text)),
                                 f"{code}: {text!r}")
                self.assertEqual(translated.count("\n"), text.count("\n"), f"{code}: {text!r}")

    def test_no_translation_is_left_over(self):
        texts = texts_in_code()
        for code, catalog in translations.CATALOGS.items():
            self.assertEqual(sorted(set(catalog) - set(texts)), [], code)

    def test_only_literal_text_is_wrapped(self):
        """The text in _() is written out, so it can be checked above. A name
        is allowed for text marked N_() where it was defined; an f-string or
        joined text would never match a translation."""
        for name in SOURCES:
            tree = ast.parse((ROOT / name).read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                        and node.func.id == "_" and node.args):
                    self.assertIsInstance(
                        node.args[0], (ast.Constant, ast.Name, ast.Subscript, ast.Attribute),
                        f"{name}:{node.lineno}: _() of an f-string or expression")

    def test_language_choice_and_fallback(self):
        self.assertEqual(i18n.set_language("de"), "de")
        self.assertEqual(i18n._("Process All"), "Alle verarbeiten")
        self.assertEqual(i18n._("Not a text of the app"), "Not a text of the app")
        self.assertEqual(i18n._("Saved {n} step(s) to {folder}").format(n=3, folder="Demo"),
                         "3 Schritt(e) in Demo gespeichert")
        self.assertEqual(i18n.set_language("en"), "en")
        self.assertEqual(i18n._("Process All"), "Process All")
        with mock.patch.object(i18n, "system_language", return_value="fr"):
            self.assertEqual(i18n.set_language("system"), "fr")
            self.assertEqual(i18n.set_language("xx"), "fr")     # unknown -> system

    def test_system_language_is_recognised(self):
        for tag, code in (("es_MX.UTF-8", "es"), ("fr_CA", "fr"), ("de-AT", "de"),
                          ("pt_BR.UTF-8", "pt_BR"), ("pt-PT", "pt_BR"), ("en_US", "en"),
                          ("ja_JP", None), ("C", None), ("", None), (None, None)):
            self.assertEqual(i18n._normalize(tag), code, tag)
        env = {"LANGUAGE": "", "LC_ALL": "", "LC_MESSAGES": "", "LANG": "de_DE.UTF-8"}
        with mock.patch.dict("os.environ", env), \
                mock.patch.object(i18n, "_windows_ui_language", return_value=None), \
                mock.patch.object(i18n, "_mac_language", return_value=None):
            self.assertEqual(i18n.system_language(), "de")
        env["LANG"] = "ja_JP.UTF-8"
        with mock.patch.dict("os.environ", env), \
                mock.patch.object(i18n, "_windows_ui_language", return_value=None), \
                mock.patch.object(i18n, "_mac_language", return_value=None):
            self.assertEqual(i18n.system_language(), "en")


class InstallerTests(unittest.TestCase):
    def test_installer_text_is_in_every_language(self):
        script = (ROOT / "packaging" / "installer.iss").read_text(encoding="utf-8")
        languages = re.findall(r'^Name: "(\w+)"; MessagesFile:', script, re.M)
        self.assertEqual(languages, ["english", "spanish", "french", "german",
                                     "brazilianportuguese"])
        messages = {}
        for lang, key, text in re.findall(r"^(\w+)\.(\w+)=(.*)$", script, re.M):
            messages.setdefault(lang, {})[key] = text
        self.assertEqual(sorted(messages), sorted(languages))
        english = messages["english"]
        for lang, texts in messages.items():
            self.assertEqual(sorted(texts), sorted(english), lang)
            for key, text in texts.items():
                self.assertEqual(sorted(re.findall(r"%\d", text)),
                                 sorted(re.findall(r"%\d", english[key])), f"{lang}.{key}")
        used = set(re.findall(r"CustomMessage\('(\w+)'\)", script))
        used |= set(re.findall(r"\{cm:(\w+)", script)) - {"Name", "CreateDesktopIcon",
                                                          "LaunchProgram"}
        self.assertEqual(sorted(used - set(english)), [])
        self.assertEqual(sorted(set(english) - used), [])
        # The installer's own words are no longer written out in the code
        code = script[script.index("\n[Code]\n"):]
        self.assertNotIn("Click Finish to close Setup", code)


if __name__ == "__main__":
    unittest.main()
