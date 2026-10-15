#!/usr/bin/env python3
#
# test_updates.py
# 2026-10-15
# Version: v1.2.0
#
# PURPOSE:
# Tests for the update check (updates.py): version comparison, reading a
# GitHub release answer from a local test server (no internet needed),
# error handling, the right download for each kind of install, and the
# administrator switch that turns checks off, and Update Now: downloading
# the installer, checking it against the release's checksum list, and the
# silent installer command for each install scope.

import hashlib
import http.server
import json
import os
import shutil
import tempfile
import threading
from pathlib import Path
import unittest
from unittest import mock

from helpers import ROOT  # also puts the repository on sys.path
import updates
import version

RELEASE = {
    "tag_name": "v9.8.7",
    "name": "v9.8.7 - Something new",
    "html_url": "https://github.com/x/y/releases/tag/v9.8.7",
    "published_at": "2030-01-02T03:04:05Z",
    "body": "Something new\n\n**New**\n- A `feature`.",
    "assets": [
        {"name": "Screencap-Documentation-Tool-v9.8.7-windows-x64-setup.exe",
         "browser_download_url": "https://example.test/setup.exe"},
        {"name": "Screencap-Documentation-Tool-v9.8.7-windows-x64-portable.zip",
         "browser_download_url": "https://example.test/portable.zip"},
        {"name": "SHA256SUMS.txt", "browser_download_url": "https://example.test/sums"},
    ],
}


class Handler(http.server.BaseHTTPRequestHandler):
    routes = {}

    def do_GET(self):
        status, body = self.routes.get(self.path, (404, b'{"message": "Not Found"}'))
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


class UpdateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # The test server is local: never send these requests through a proxy
        cls.env = mock.patch.dict(os.environ, {"NO_PROXY": "127.0.0.1,localhost",
                                               "no_proxy": "127.0.0.1,localhost"})
        cls.env.start()
        Handler.routes = {
            "/latest": (200, json.dumps(RELEASE).encode()),
            "/odd": (200, json.dumps({"tag_name": "nightly"}).encode()),
            "/broken": (200, b"not json"),
        }
        cls.server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.env.stop()

    def test_version_comparison(self):
        self.assertEqual(updates.parse_version("v1.2.3"), (1, 2, 3))
        self.assertEqual(updates.parse_version("1.10.0"), (1, 10, 0))
        self.assertIsNone(updates.parse_version("v1.2"))
        self.assertIsNone(updates.parse_version("v1.2.3-beta"))
        self.assertTrue(updates.is_newer("1.10.0", "1.9.9"))
        self.assertFalse(updates.is_newer("1.9.9", "1.10.0"))
        self.assertFalse(updates.is_newer(version.RELEASE))
        self.assertFalse(updates.is_newer("garbage"))

    def test_reads_the_latest_release(self):
        latest = updates.check_latest(self.base + "/latest", timeout=5)
        self.assertEqual(latest["version"], "9.8.7")
        self.assertEqual(latest["published"], "2030-01-02")
        self.assertTrue(updates.is_newer(latest["version"]))
        self.assertEqual(updates.download_for(latest, "installer"), "https://example.test/setup.exe")
        self.assertEqual(updates.download_for(latest, "portable"), "https://example.test/portable.zip")
        self.assertEqual(updates.download_for(latest, "python"), RELEASE["html_url"])

    def test_windows_on_arm_gets_the_arm64_build_when_there_is_one(self):
        latest = updates.check_latest(self.base + "/latest", timeout=5)
        # This test release has only x64 files: ARM PCs get those (emulated)
        self.assertEqual(updates.download_for(latest, "installer", "arm64"),
                         "https://example.test/setup.exe")
        latest["assets"]["Screencap-Documentation-Tool-v9.8.7-windows-arm64-setup.exe"] = \
            "https://example.test/arm64-setup.exe"
        latest["assets"]["Screencap-Documentation-Tool-v9.8.7-windows-arm64-portable.zip"] = \
            "https://example.test/arm64-portable.zip"
        self.assertEqual(updates.download_for(latest, "installer", "arm64"),
                         "https://example.test/arm64-setup.exe")
        self.assertEqual(updates.download_for(latest, "portable", "arm64"),
                         "https://example.test/arm64-portable.zip")
        self.assertEqual(updates.download_for(latest, "installer", "x64"),
                         "https://example.test/setup.exe")
        self.assertIn(updates.windows_arch(), ("x64", "arm64"))
        notes = updates.release_notes_excerpt(latest["notes"])
        self.assertIn("New", notes)
        self.assertNotIn("**", notes)
        self.assertNotIn("`", notes)

    def test_errors_are_explained(self):
        for path in ("/missing", "/odd", "/broken"):
            with self.subTest(path=path), self.assertRaises(updates.UpdateError):
                updates.check_latest(self.base + path, timeout=5)
        with self.assertRaises(updates.UpdateError):     # nothing listening there
            updates.check_latest("http://127.0.0.1:9/latest", timeout=2)

    def test_administrator_can_turn_checks_off(self):
        with mock.patch.dict(os.environ, {"SCREENCAP_NO_UPDATE_CHECK": "1"}):
            self.assertTrue(updates.disabled_by_policy())
        with mock.patch.dict(os.environ, {"SCREENCAP_NO_UPDATE_CHECK": ""}):
            self.assertFalse(updates.disabled_by_policy())

    def test_python_install_is_detected(self):
        self.assertTrue((ROOT / "updates.py").is_file())
        self.assertEqual(updates.install_kind(), "python")
        self.assertIn("Quick Start", updates.how_to_update("python"))
        self.assertIn("winget upgrade", updates.how_to_update("installer"))


SETUP_NAME = "Screencap-Documentation-Tool-v9.8.7-windows-x64-setup.exe"
SETUP = b"MZ" + bytes(range(256)) * 4000    # about 1 MB, so progress is reported


class UpdateNowTests(unittest.TestCase):
    """Downloading and checking the installer, from a local test server."""

    @classmethod
    def setUpClass(cls):
        cls.env = mock.patch.dict(os.environ, {"NO_PROXY": "127.0.0.1,localhost",
                                               "no_proxy": "127.0.0.1,localhost"})
        cls.env.start()
        good = hashlib.sha256(SETUP).hexdigest()
        Handler.routes.update({
            "/dl/setup.exe": (200, SETUP),
            "/dl/sums": (200, f"{good}  {SETUP_NAME}\n{'0' * 64}  other.zip\n".encode()),
            "/dl/badsums": (200, f"{'1' * 64}  {SETUP_NAME}\n".encode()),
            "/dl/othersums": (200, f"{good}  something-else.exe\n".encode()),
        })
        cls.server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.env.stop()

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="screencap_update_"))
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def latest(self, sums="/dl/sums"):
        return {"version": "9.8.7", "url": "https://example.test/release", "assets": {
            SETUP_NAME: self.base + "/dl/setup.exe",
            updates.CHECKSUMS_NAME: self.base + sums}}

    def download(self, latest, **kw):
        kw.setdefault("allowed", self.base + "/dl/")
        return updates.download_installer(latest, dest_dir=self.tmp, arch="x64", **kw)

    def test_downloads_and_checks_the_installer(self):
        seen = []
        path = self.download(self.latest(), progress=lambda d, t: seen.append((d, t)))
        self.assertEqual(path.name, SETUP_NAME)
        self.assertEqual(path.read_bytes(), SETUP)
        self.assertEqual(seen[-1], (len(SETUP), len(SETUP)))
        self.assertEqual([f.name for f in self.tmp.iterdir()], [SETUP_NAME])

    def test_a_file_that_does_not_match_is_never_kept(self):
        with self.assertRaisesRegex(updates.UpdateError, "does not match"):
            self.download(self.latest("/dl/badsums"))
        self.assertEqual(list(self.tmp.iterdir()), [])
        with self.assertRaisesRegex(updates.UpdateError, "not in the release's checksum list"):
            self.download(self.latest("/dl/othersums"))
        latest = self.latest()
        del latest["assets"][updates.CHECKSUMS_NAME]
        with self.assertRaisesRegex(updates.UpdateError, "no checksum list"):
            self.download(latest)
        self.assertEqual(list(self.tmp.iterdir()), [])

    def test_only_this_projects_release_files_are_downloaded(self):
        with self.assertRaisesRegex(updates.UpdateError, "unexpected address"):
            updates.download_installer(self.latest(), dest_dir=self.tmp, arch="x64")
        self.assertTrue(updates.DOWNLOAD_PREFIX.startswith(
            "https://github.com/ILikeHostingServices/Screencap-Documentation-Tool/releases/download/"))

    def test_cancel_leaves_nothing_behind(self):
        cancel = threading.Event()
        with self.assertRaises(updates.UpdateCancelled):
            self.download(self.latest(), cancel=cancel, progress=lambda d, t: cancel.set())
        self.assertEqual(list(self.tmp.iterdir()), [])

    def test_missing_installer_and_server_errors(self):
        latest = self.latest()
        latest["assets"] = {updates.CHECKSUMS_NAME: self.base + "/dl/sums"}
        with self.assertRaisesRegex(updates.UpdateError, "no Windows installer"):
            self.download(latest)
        latest = self.latest()
        latest["assets"][SETUP_NAME] = self.base + "/dl/missing.exe"
        with self.assertRaisesRegex(updates.UpdateError, "404"):
            self.download(latest)
        self.assertEqual(list(self.tmp.iterdir()), [])

    def test_checksum_list_formats(self):
        h = "A" * 64
        sums = updates.read_checksums(f"{h}  one.exe\n{h.lower()} *two.zip\nnot a line\n\n")
        self.assertEqual(sums, {"one.exe": "a" * 64, "two.zip": "a" * 64})

    def test_arm_pcs_get_the_arm_installer_when_there_is_one(self):
        latest = self.latest()
        self.assertEqual(updates.installer_asset(latest, "arm64")[0], SETUP_NAME)
        arm = SETUP_NAME.replace("x64", "arm64")
        latest["assets"][arm] = "https://example.test/arm"
        self.assertEqual(updates.installer_asset(latest, "arm64")[0], arm)
        self.assertEqual(updates.installer_asset(latest, "x64")[0], SETUP_NAME)

    def test_scope_follows_where_this_copy_is_installed(self):
        pf = Path(self.tmp, "Program Files")
        env = {"ProgramFiles": str(pf), "ProgramW6432": str(pf), "ProgramFiles(x86)": ""}
        with mock.patch.dict(os.environ, env):
            self.assertEqual(updates.install_scope(pf / "ILHS" / "Screencap-Documentation-Tool"),
                             "ALLUSERS")
            self.assertEqual(updates.install_scope(Path(self.tmp, "Users", "me", "AppData", "Local",
                                                        "Programs", "ILHS")), "CURRENTUSER")
            self.assertEqual(updates.install_scope(Path(str(pf) + " Extra", "x")), "CURRENTUSER")
        args = updates.installer_args("ALLUSERS", "C:\\t\\setup.log")
        for flag in ("/SILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/ALLUSERS", "/RELAUNCH=1"):
            self.assertIn(flag, args)
        self.assertNotIn("/RELAUNCH=1", updates.installer_args("CURRENTUSER", "x", relaunch=False))

    def test_installer_relaunches_after_a_silent_update(self):
        script = (ROOT / "packaging" / "installer.iss").read_text(encoding="utf-8")
        self.assertIn("Check: RelaunchAfterUpdate", script)
        self.assertIn("runasoriginaluser", script)
        self.assertIn("{param:RELAUNCH|0}", script)

    def test_who_gets_update_now(self):
        with mock.patch.object(updates.os, "name", "nt"):
            self.assertTrue(updates.can_install("installer"))
            for kind in ("portable", "deb", "snap", "brew", "python"):
                self.assertFalse(updates.can_install(kind))
            with mock.patch.dict(os.environ, {"SCREENCAP_NO_UPDATE_CHECK": "1"}):
                self.assertFalse(updates.can_install("installer"))
        if os.name != "nt":
            self.assertFalse(updates.can_install("installer"))
            with self.assertRaises(updates.UpdateError):
                updates.start_installer(self.tmp / "setup.exe")

    def test_update_commands(self):
        self.assertEqual(updates.update_command("deb", "9.8.7"),
                         "sudo apt install ./screencap-documentation-tool_9.8.7-1_all.deb")
        self.assertIn("9.8.7-1.noarch.rpm", updates.update_command("rpm", "9.8.7"))
        self.assertIn("snap refresh", updates.update_command("snap"))
        self.assertIn("brew upgrade", updates.update_command("brew"))
        self.assertIsNone(updates.update_command("portable"))
        self.assertIsNone(updates.update_command("python"))


if __name__ == "__main__":
    unittest.main()
