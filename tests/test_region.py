#!/usr/bin/env python3
#
# test_region.py
# 2026-11-11
# Version: v1.0.0
#
# PURPOSE:
# Tests for how dates and times are written (region.py): each date format
# and clock, Windows date pictures turned into strftime patterns, stored
# times shown in the chosen format, the system setting as the default, and
# the date on exported documents following the choice.
#
# Run from the repository root:
#   python -m unittest discover -s tests -v

import time
import unittest
from unittest import mock

import helpers  # noqa: F401  (puts the repository on the path)
import export  # noqa: E402
import region  # noqa: E402

WHEN = time.mktime((2026, 11, 22, 14, 5, 9, 0, 0, -1))


class RegionTests(unittest.TestCase):
    def tearDown(self):
        region.configure("system", "system")

    def test_each_date_format_and_clock(self):
        expected = {"iso": "2026-11-22", "us": "11/22/2026", "dmy": "22/11/2026",
                    "dmy-dot": "22.11.2026"}
        for key, text in expected.items():
            region.configure(key, "24")
            self.assertEqual(region.format_date(WHEN), text)
            self.assertEqual(region.format_datetime(WHEN), f"{text} 14:05")
        region.configure("iso", "12")
        self.assertEqual(region.format_datetime(WHEN), "2026-11-22 2:05 PM")
        self.assertEqual(region.format_datetime(WHEN, seconds=True), "2026-11-22 2:05:09 PM")

    def test_windows_pictures_become_strftime_patterns(self):
        self.assertEqual(region.windows_to_strftime("M/d/yyyy"), "%m/%d/%Y")
        self.assertEqual(region.windows_to_strftime("dd.MM.yyyy"), "%d.%m.%Y")
        self.assertEqual(region.windows_to_strftime("h:mm:ss tt"), "%I:%M:%S %p")
        self.assertEqual(region.windows_to_strftime("yyyy'年'M'月'd'日'"), "%Y年%m月%d日")

    def test_the_system_setting_is_used_by_default(self):
        region.configure("system", "system")
        with mock.patch.object(region, "_system", {"date": "%d.%m.%Y", "clock": True}):
            self.assertEqual(region.format_datetime(WHEN), "22.11.2026 2:05 PM")
        with mock.patch.object(region, "_system", {"date": "%Y-%m-%d", "clock": False}):
            self.assertEqual(region.format_datetime(WHEN), "2026-11-22 14:05")

    def test_unknown_choices_fall_back_to_the_system(self):
        region.configure("klingon", "36")
        self.assertEqual(region.settings(), {"date": "system", "clock": "system"})

    def test_stored_times_are_shown_in_the_chosen_format(self):
        region.configure("us", "12")
        self.assertEqual(region.format_stored("2026-11-22 14:05:00"), "11/22/2026 2:05 PM")
        self.assertEqual(region.format_stored("not a time"), "not a time")

    def test_exported_documents_use_the_chosen_date(self):
        region.configure("dmy-dot", "24")
        self.assertEqual(export.metadata({})["date"], time.strftime("%d.%m.%Y"))


if __name__ == "__main__":
    unittest.main()
