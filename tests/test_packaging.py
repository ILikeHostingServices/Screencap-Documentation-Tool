#!/usr/bin/env python3
#
# test_packaging.py
# 2026-10-10
# Version: v1.0.0
#
# PURPOSE:
# Checks the Linux package layout (packaging/linux/stage.sh) for every
# package kind, the launchers, the package-kind marker that moves the
# default folders to ~/Documents, the update advice for each kind, and that
# the software center details list the current release. The real install
# tests per distribution run in .github/workflows/build-linux.yml.

import os
import re
import shutil
import sys
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from helpers import ROOT

import apppaths
import updates
import version

NAME = "screencap-documentation-tool"
APPID = "io.github.ILikeHostingServices.ScreencapDocumentationTool"


# The staging script is bash for Linux packages; on Windows these tests are
# not defined at all (the test run treats skipped tests as failures)
class StageTests(unittest.TestCase if os.name != "nt" else object):
    def stage(self, kind):
        dest = Path(tempfile.mkdtemp(prefix=f"stage_{kind}_"))
        self.addCleanup(shutil.rmtree, dest, True)
        subprocess.run(["bash", str(ROOT / "packaging/linux/stage.sh"), str(dest), kind], check=True)
        return dest

    def test_layout_for_every_kind(self):
        for kind in ("deb", "rpm", "arch", "snap"):
            with self.subTest(kind=kind):
                dest = self.stage(kind)
                share = dest / "usr/share" / NAME
                for module in ROOT.glob("*.py"):
                    self.assertTrue((share / module.name).is_file(), module.name)
                self.assertTrue((share / "screencap_gui.pyw").is_file())
                self.assertTrue((share / "assets/icon.png").is_file())
                self.assertEqual((share / "package-kind").read_text().strip(), kind)
                for f in (f"usr/share/applications/{APPID}.desktop",
                          f"usr/share/metainfo/{APPID}.metainfo.xml",
                          f"usr/share/icons/hicolor/256x256/apps/{APPID}.png",
                          f"usr/share/licenses/{NAME}/LICENSE"):
                    self.assertTrue((dest / f).is_file(), f)
                for cmd, script in (("screencap", "screencap.py"),
                                    ("screencap-gui", "screencap_gui.pyw")):
                    launcher = dest / "usr/bin" / cmd
                    self.assertTrue(os.access(launcher, os.X_OK), cmd)
                    text = launcher.read_text()
                    self.assertIn(f"/usr/share/{NAME}/{script}", text)
                    self.assertIn(" -B ", text)
                    self.assertIn("$SNAP/usr/bin/python3" if kind == "snap" else "/usr/bin/python3",
                                  text)

    def test_unknown_kind_is_refused(self):
        dest = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, dest, True)
        res = subprocess.run(["bash", str(ROOT / "packaging/linux/stage.sh"), str(dest), "msi"],
                             capture_output=True, text=True)
        self.assertNotEqual(res.returncode, 0)

    def test_staged_program_runs(self):
        dest = self.stage("deb")
        res = subprocess.run([sys.executable, "-B", str(dest / "usr/share" / NAME / "screencap.py"),
                              "--version"], capture_output=True, text=True, check=True)
        self.assertIn(f"v{version.RELEASE}", res.stdout)


class PackageKindTests(unittest.TestCase):
    def test_package_installs_use_documents_and_package_updates(self):
        latest = {"url": "https://example.test/release", "assets": {
            f"{NAME}_9.0.0-1_all.deb": "https://example.test/deb",
            f"{NAME}-9.0.0-1.noarch.rpm": "https://example.test/rpm",
            f"{NAME}-9.0.0-1-any.pkg.tar.zst": "https://example.test/arch"}}
        for kind, link in (("deb", "deb"), ("rpm", "rpm"), ("arch", "arch"), ("snap", None),
                           ("brew", None)):
            with self.subTest(kind=kind), mock.patch.object(apppaths, "PACKAGE_KIND", kind):
                self.assertEqual(updates.install_kind(), kind)
                expected = f"https://example.test/{link}" if link else latest["url"]
                self.assertEqual(updates.download_for(latest), expected)
                self.assertTrue(updates.how_to_update().strip())

    def test_marker_is_read(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        with mock.patch.object(apppaths, "APP_DIR", tmp):
            self.assertIsNone(apppaths.package_kind())
            (tmp / "package-kind").write_text("rpm\n")
            self.assertEqual(apppaths.package_kind(), "rpm")
            (tmp / "package-kind").write_text("something-else\n")
            self.assertIsNone(apppaths.package_kind())

    def test_metainfo_lists_this_release(self):
        text = (ROOT / f"packaging/linux/{APPID}.metainfo.xml").read_text(encoding="utf-8")
        newest = re.search(r'<release version="([^"]+)"', text).group(1)
        self.assertEqual(newest, version.RELEASE,
                         "Add this release at the top of <releases> in the metainfo file")


if __name__ == "__main__":
    unittest.main()
