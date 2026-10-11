#!/usr/bin/env python3
#
# test_apppaths.py
# 2026-10-11
# Version: v1.0.0
#
# PURPOSE:
# Tests for apppaths.py: the folders chosen in the Windows installer are read
# from the registry (Windows only: elsewhere the class is not defined at all,
# because the test run treats skipped tests as failures), and nothing is read
# outside the packaged Windows app.

import os
import unittest
from pathlib import Path
from unittest import mock

from helpers import ROOT  # also puts the repository on sys.path
import apppaths


class NotPackagedTests(unittest.TestCase):
    def test_runs_from_the_repository(self):
        self.assertEqual(apppaths.APP_DIR, ROOT)

    def test_no_installer_folders_outside_the_packaged_app(self):
        with mock.patch.object(apppaths, "FROZEN", False):
            self.assertIsNone(apppaths.installer_folders())


if os.name == "nt":
    import winreg

    class RegistryTests(unittest.TestCase):
        KEY = r"Software\ILHS\Screencap Documentation Tool (test)"

        def setUp(self):
            self.addCleanup(self.delete_key)
            local = os.environ["LOCALAPPDATA"]
            patches = (mock.patch.object(apppaths, "FROZEN", True),
                       mock.patch.object(apppaths, "INSTALLER_KEY", self.KEY),
                       mock.patch.object(apppaths, "APP_DIR",
                                         Path(local) / "Programs" / "ILHS" / "Test"))
            for p in patches:
                p.start()
                self.addCleanup(p.stop)

        def delete_key(self):
            try:
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, self.KEY)
            except OSError:
                pass

        def write(self, **values):
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, self.KEY) as key:
                for name, value in values.items():
                    winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)

        def test_reads_the_folders_and_stamp(self):
            self.write(SourceDir=r"D:\Rec", OutputDir=r"D:\Out", FoldersStamp="20261011120000")
            self.assertEqual(apppaths.installer_folders(),
                             apppaths.InstallerFolders(Path(r"D:\Rec"), Path(r"D:\Out"),
                                                       "20261011120000"))

        def test_missing_stamp_means_do_not_override(self):
            self.write(SourceDir=r"D:\Rec", OutputDir=r"D:\Out")
            self.assertEqual(apppaths.installer_folders().stamp, "")

        def test_nothing_recorded(self):
            self.assertIsNone(apppaths.installer_folders())


if __name__ == "__main__":
    unittest.main()
