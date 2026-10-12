#!/usr/bin/env python3
#
# test_export.py
# 2026-10-12
# Version: v1.0.0
#
# PURPOSE:
# Tests for exports: alt text on every screenshot (steps.md, HTML, Word),
# the company logo at the top of HTML, Word, and PDF documents, a Word
# template's styles carried into Word exports, the starter template, and
# clear errors for a missing or unsupported file.
#
# Run from the repository root:
#   python -m unittest discover -s tests -v

import re
import shutil
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

from helpers import FFMPEG, FFPROBE, make_video  # noqa: E402

import export  # noqa: E402
import screencap as sc  # noqa: E402
import stepdoc  # noqa: E402

MARKER_FONT = "Screencap Test Serif"   # a font name only the test template uses


@unittest.skipUnless(FFMPEG and FFPROBE, "FFmpeg is not installed")
class BrandingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="screencap_export_"))
        source = cls.tmp / "source"
        source.mkdir()
        make_video(source / "Demo.mp4", duration=10)
        assert sc.main(["-s", str(source), "-o", str(cls.tmp / "out"), "--no-redact"]) == 0
        cls.folder = cls.tmp / "out" / "Demo"
        cls.logo = cls.tmp / "brand" / "Company logo.png"
        cls.logo.parent.mkdir()
        subprocess.run([FFMPEG, "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi",
                        "-i", "color=0x2563eb:s=200x60", "-frames:v", "1", str(cls.logo)],
                       check=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def doc(self):
        doc = stepdoc.load(self.folder)
        doc["document"]["title"] = "Install *Acme* [Agent] #2"
        return doc

    def test_html_has_the_logo_in_its_header(self):
        page = export.build_html(self.folder, self.doc(), logo=self.logo)
        header = page[page.index("<header>"):page.index("</header>")]
        self.assertIn('<img class="logo" src="data:image/png;base64,', header)
        self.assertNotIn('class="logo"', export.build_html(self.folder, self.doc()))

    def test_bad_logo_and_template_give_clear_errors(self):
        with self.assertRaisesRegex(RuntimeError, "PNG, JPG, GIF, or SVG"):
            export.check_logo(self.folder / "steps.json")
        with self.assertRaisesRegex(RuntimeError, "not found"):
            export.check_logo(self.tmp / "missing.png")
        with self.assertRaisesRegex(RuntimeError, ".docx"):
            export.check_template(self.logo)
        self.assertIsNone(export.check_logo(None))

    def test_title_text_is_kept_exactly_in_word_markdown(self):
        md = export.build_markdown(self.folder, self.doc(), logo=self.logo)
        self.assertIn('::: {custom-style="Title"}', md)
        self.assertIn(r"Install \*Acme\* \[Agent\] \#2", md)
        self.assertIn(self.logo.as_posix(), md)

    @unittest.skipUnless(export.find_pandoc(), "Pandoc is not installed")
    def test_word_export_uses_the_logo_and_the_template(self):
        template = export.create_template(self.tmp / "My template.docx")
        self.assertTrue(zipfile.is_zipfile(template))
        branded = self.tmp / "Branded.docx"
        with zipfile.ZipFile(template) as src, zipfile.ZipFile(branded, "w") as dst:
            for item in src.infolist():
                data = src.read(item.filename)
                if item.filename == "word/styles.xml":
                    # every style that names a font now names the marker font
                    data = re.sub(rb'w:ascii="[^"]+"', f'w:ascii="{MARKER_FONT}"'.encode(), data)
                dst.writestr(item, data)

        dest = export.export(self.folder, self.doc(), "docx", logo=self.logo, template=branded)
        with zipfile.ZipFile(dest) as docx:
            names = docx.namelist()
            body = docx.read("word/document.xml").decode("utf-8")
            styles = docx.read("word/styles.xml").decode("utf-8")
        self.assertTrue(any(n.startswith("word/media/") for n in names), "logo picture")
        self.assertIn(MARKER_FONT, styles, "the template's styles are used")
        self.assertIn("Install *Acme* [Agent] #2", body)
        self.assertLess(body.index("<w:drawing>"), body.index("Install *Acme*"),
                        "the logo comes before the title")

        plain = export.export(self.folder, self.doc(), "docx")
        with zipfile.ZipFile(plain) as docx:
            self.assertNotIn(MARKER_FONT, docx.read("word/styles.xml").decode("utf-8"))

    def test_alt_text_describes_each_screenshot(self):
        step = {"caption": "  Click   Next\nto continue.", "annotations": [
            {"kind": "text", "at": [1, 1], "text": "Next [button]"},
            {"kind": "arrow", "from": [0, 0], "to": [50, 50]}]}
        self.assertEqual(stepdoc.alt_text(step, 3), 'Step 3: Click Next to continue. Labels on '
                         'the screenshot: "Next [button]"')
        self.assertEqual(stepdoc.alt_text({"caption": ""}, 1), "Screenshot of step 1")
        self.assertLessEqual(len(stepdoc.alt_text({"caption": "x" * 900}, 1)), stepdoc.ALT_MAX)
        self.assertEqual(stepdoc.markdown_alt("a [b] \\ c"), "a \\[b\\] \\\\ c")

        doc = self.doc()
        doc["steps"][0]["caption"] = 'Open "Setup" & <accept>'
        page = export.build_html(self.folder, doc)
        self.assertIn('alt="Step 1: Open &quot;Setup&quot; &amp; &lt;accept&gt;"', page)
        stepdoc.save(self.folder, doc)
        md = (self.folder / stepdoc.INDEX_NAME).read_text(encoding="utf-8")
        self.assertIn('![Step 1: Open "Setup" & <accept>](', md)
        self.assertIn(f"![Screenshot of step 2]({doc['steps'][1]['file']})", md)

    @unittest.skipUnless(export.find_pandoc(), "Pandoc is not installed")
    def test_word_pictures_have_alt_text_and_no_extra_caption(self):
        doc = self.doc()
        doc["steps"][0]["caption"] = "Accept the license agreement"
        dest = export.export(self.folder, doc, "docx")
        with zipfile.ZipFile(dest) as docx:
            body = docx.read("word/document.xml").decode("utf-8")
        self.assertIn('descr="Step 1: Accept the license agreement"', body)
        visible = re.findall(r"<w:t[^>]*>([^<]*)</w:t>", body)
        self.assertEqual(sum("Accept the license" in t for t in visible), 1,
                         "the caption is printed once, not again as a figure caption")

    def test_command_line_options(self):
        out = self.tmp / "cli"
        source = self.folder.parent.parent / "source"
        self.assertEqual(sc.main(["-s", str(source), "-o", str(out), "--no-redact",
                                  "--export", "html", "--logo", str(self.logo)]), 0)
        page = (out / "Demo" / "export" / "Demo.html").read_text(encoding="utf-8")
        self.assertIn('class="logo"', page)
        if export.find_pandoc():
            dest = self.tmp / "cli-template.docx"
            self.assertEqual(sc.main(["--create-word-template", str(dest)]), 0)
            self.assertTrue(zipfile.is_zipfile(dest))


if __name__ == "__main__":
    unittest.main()
