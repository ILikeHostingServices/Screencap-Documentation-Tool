#!/usr/bin/env python3
#
# test_workers.py
# 2026-10-14
# Version: v1.0.0
#
# PURPOSE:
# Tests for running per-screenshot work in parallel (workers.py) and the
# faster image comparisons (imaging.py) it goes with: results keep their
# order, errors and Cancel stop the run, and the row-skipping comparisons
# give the same answers as comparing every pixel.
#
# Run from the repository root:
#   python -m unittest discover -s tests -v

import os
import random
import threading
import time
import unittest
from unittest import mock

from helpers import ROOT  # also puts the repository on sys.path

import imaging  # noqa: E402
import workers  # noqa: E402


class RunAllTests(unittest.TestCase):
    def test_results_keep_their_order(self):
        def slow_square(n):
            time.sleep(0.01 * (5 - n % 5))   # later items often finish first
            return n * n
        self.assertEqual(workers.run_all(slow_square, range(20)), [n * n for n in range(20)])

    def test_runs_jobs_at_the_same_time(self):
        running, peak, lock = [0], [0], threading.Lock()

        def job(_):
            with lock:
                running[0] += 1
                peak[0] = max(peak[0], running[0])
            time.sleep(0.05)
            with lock:
                running[0] -= 1
        with mock.patch.dict(os.environ, {"SCREENCAP_WORKERS": "4"}):
            workers.run_all(job, range(8))
        self.assertEqual(peak[0], 4)

    def test_one_worker_runs_one_at_a_time(self):
        order = []
        with mock.patch.dict(os.environ, {"SCREENCAP_WORKERS": "1"}):
            workers.run_all(order.append, ["a", "b", "c"])
        self.assertEqual(order, ["a", "b", "c"])

    def test_worker_count_has_a_ceiling(self):
        with mock.patch.dict(os.environ, {"SCREENCAP_WORKERS": ""}), \
                mock.patch("os.cpu_count", return_value=64):
            self.assertEqual(workers.count(), workers.MAX_WORKERS)
        with mock.patch.dict(os.environ, {"SCREENCAP_WORKERS": "junk"}), \
                mock.patch("os.cpu_count", return_value=None):
            self.assertEqual(workers.count(), 1)

    def test_an_error_stops_the_run_and_is_raised(self):
        started = []

        def job(n):
            started.append(n)
            if n == 2:
                raise RuntimeError("frame 2 failed")
            time.sleep(0.05)
        with mock.patch.dict(os.environ, {"SCREENCAP_WORKERS": "2"}):
            with self.assertRaisesRegex(RuntimeError, "frame 2 failed"):
                workers.run_all(job, range(40))
        self.assertLess(len(started), 40)   # jobs not started yet were dropped

    def test_cancel_stops_the_run(self):
        cancel = threading.Event()

        def job(n):
            if n == 3:
                cancel.set()
            time.sleep(0.02)
        for count in ("1", "3"):
            cancel.clear()
            with mock.patch.dict(os.environ, {"SCREENCAP_WORKERS": count}):
                with self.assertRaises(workers.Cancelled):
                    workers.run_all(job, range(100), cancel)

    def test_done_reports_progress(self):
        seen = []
        workers.run_all(lambda n: n, range(5), done=lambda n, total: seen.append((n, total)))
        self.assertEqual(seen[-1], (5, 5))
        self.assertEqual([n for n, _ in seen], sorted(n for n, _ in seen))

    def test_nothing_to_do(self):
        self.assertEqual(workers.run_all(lambda n: n, []), [])

    def test_readme_lists_the_module(self):
        self.assertIn("`workers.py`", (ROOT / "README.md").read_text(encoding="utf-8"))


def changed_every_pixel(a, b, delta=imaging.PIXEL_DELTA):
    """The comparison as it was before rows were skipped."""
    return 100.0 * sum(1 for x, y in zip(a, b) if abs(x - y) > delta) / max(len(a), 1)


class ComparisonTests(unittest.TestCase):
    def pair(self, seed, changes):
        rnd = random.Random(seed)
        w, h = imaging.DEDUP_SIZE
        a = bytes(rnd.randrange(256) for _ in range(w * h))
        b = bytearray(a)
        for _ in range(changes):
            i = rnd.randrange(len(b))
            b[i] = rnd.randrange(256)
        return a, bytes(b)

    def test_same_answer_as_comparing_every_pixel(self):
        for seed, changes in [(1, 0), (2, 5), (3, 140), (4, 150), (5, 3000), (6, 14400)]:
            a, b = self.pair(seed, changes)
            self.assertAlmostEqual(imaging.changed_percent(a, b), changed_every_pixel(a, b))
            for threshold in (0.01, 1.0, 10.0):
                expected = 0 if changed_every_pixel(a, b) <= threshold else None
                self.assertEqual(imaging.find_duplicate(b, [a], threshold), expected,
                                 (seed, changes, threshold))

    def test_first_matching_screen_is_reported(self):
        a, b = self.pair(7, 2)
        other, _ = self.pair(8, 0)
        self.assertEqual(imaging.find_duplicate(b, [other, a, a], 1.0), 1)

    def test_change_box_matches_every_pixel_version(self):
        w, h = imaging.CHANGE_SIZE
        prev = bytes(200 for _ in range(w * h))
        cur = bytearray(prev)
        for y in range(40, 60):          # a changed field
            for x in range(100, 180):
                cur[y * w + x] = 20
        cur[170 * w + 5] = 0              # a lone changed pixel (cursor-like)
        box = imaging.change_box(prev, bytes(cur), 1920, 1080)
        self.assertIsNotNone(box)
        x, y, bw, bh = box
        self.assertLessEqual(x, 600)
        self.assertGreaterEqual(x + bw, 1080)
        self.assertLessEqual(y, 240)
        self.assertGreaterEqual(y + bh, 360)
        self.assertIsNone(imaging.change_box(prev, prev, 1920, 1080))


if __name__ == "__main__":
    unittest.main()
