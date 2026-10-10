#!/usr/bin/env python3
#
# test_updates.py
# 2026-10-10
# Version: v1.0.0
#
# PURPOSE:
# Tests for the update check (updates.py): version comparison, reading a
# GitHub release answer from a local test server (no internet needed),
# error handling, the right download for each kind of install, and the
# administrator switch that turns checks off.

import http.server
import json
import os
import threading
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


if __name__ == "__main__":
    unittest.main()
