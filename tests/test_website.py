#!/usr/bin/env python3
#
# test_website.py
# 2026-10-30
# Version: v1.2.0
#
# PURPOSE:
# Tests for the website build (website/build.py): every menu page is built
# with the shared header, the links between pages and to their pictures
# exist, the download links name the release asked for, and the addresses
# of the old single-page site still lead somewhere.

import importlib.util
import re
import tempfile
import unittest
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("website_build", ROOT / "website" / "build.py")
build = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(build)

# The repositories step of the workflow adds this file to the same folder
ADDED_BY_WORKFLOW = ("ilhs-archive-key.asc",)


class WebsiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.site = Path(cls.tmp.name)
        cls.problems = build.build(cls.site, "9.8.7", ADDED_BY_WORKFLOW)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def page(self, rel):
        return (self.site / rel).read_text(encoding="utf-8")

    def test_every_link_between_pages_exists(self):
        self.assertEqual(self.problems, [])

    def test_one_page_per_menu_link_with_the_shared_menu(self):
        for slug in ("features", "steps-recorder", "requirements", "download", "for-it"):
            text = self.page(f"{slug}/index.html")
            self.assertIn(f'<a href="../{slug}/" aria-current="page">', text)
            self.assertIn('href="../download/"', text)
            self.assertIn('<link rel="canonical" href="https://screencap.ilhs.app/' + slug + '/">', text)
        self.assertIn('<a href="download/">Download</a>', self.page("index.html"))
        self.assertIn('content="noindex"', self.page("404.html"))
        # the credits page is linked from every page's footer
        self.assertIn("Valve Corporation", self.page("credits/index.html"))
        self.assertIn('href="../credits/">Credits</a>', self.page("features/index.html"))

    def test_download_links_name_the_release(self):
        text = self.page("download/index.html")
        links = re.findall(r'href="(https://github.com/[^"]+/releases/download/[^"]+)"', text)
        self.assertEqual(len(links), 8)
        for link in links:
            self.assertIn("/releases/download/v9.8.7/", link)
            self.assertIn("9.8.7", link.rsplit("/", 1)[1])
        self.assertNotIn("{{", text)

    def test_a_broken_link_is_reported(self):
        (self.site / "features" / "extra.html").write_text(
            '<a href="../nowhere/">x</a><a href="../download/#nowhere">y</a>', encoding="utf-8")
        try:
            problems = build.check_links(self.site, ADDED_BY_WORKFLOW)
        finally:
            (self.site / "features" / "extra.html").unlink()
        self.assertEqual(len(problems), 2)
        self.assertIn("../nowhere/", problems[0] + problems[1])

    def test_old_single_page_addresses_still_lead_somewhere(self):
        # ilhs.app and older links point at sections of the old page
        script = (ROOT / "website" / "assets" / "site.js").read_text(encoding="utf-8")
        for section in ("install", "install-windows", "install-linux", "install-mac",
                        "features", "psr", "requirements", "it"):
            self.assertRegex(script, rf"'{section}': '[a-z-]+/(#[a-z]+)?'")
        for target in re.findall(r"': '([a-z-]+)/(?:#([a-z]+))?'", script):
            page = self.page(f"{target[0]}/index.html")
            if target[1]:
                self.assertIn(f'id="{target[1]}"', page)
        self.assertIn('id="how"', self.page("index.html"))

    def test_sizes_follow_the_shared_sizing_spec(self):
        # The ILHS Shared Sizing Spec block is copied in unchanged, and no
        # text size is written in px (it would not follow the browser's
        # text size setting)
        css = (ROOT / "website" / "assets" / "site.css").read_text(encoding="utf-8")
        start = css.index("/* ILHS Shared Sizing Spec v")
        end = css.index(" end */", start)
        self.assertLess(start, end)
        self.assertIn("--wrap-max: 75rem;", css[start:end])
        rest = css[:start] + css[end:]
        self.assertNotRegex(rest, r"font(-size)?:[^;}]*\d+px")
        # ...and exactly as pinned: a changed block stops the build
        build.check_sizing()
        with mock.patch.object(build, "SIZING_PIN", self.site / "pin.css"):
            (self.site / "pin.css").write_text(css[start:end].replace("75rem", "70rem") + " end */",
                                               encoding="utf-8")
            with self.assertRaises(build.BuildError):
                build.check_sizing()

    def test_bad_version_or_page_is_an_error(self):
        with self.assertRaises(build.BuildError):
            build.render("1.2")
        self.assertEqual(build.release_version().count("."), 2)


if __name__ == "__main__":
    unittest.main()
