#!/usr/bin/env python3
#
# workers.py
# 2026-10-14
# Version: v1.0.0
#
# PURPOSE:
# Runs the per-screenshot work (FFmpeg and Tesseract processes) on several
# CPU cores at once. Each job starts its own process, so threads are enough:
# Python waits on the process while the operating system runs it.

import os
import threading
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait

MAX_WORKERS = 8   # more parallel FFmpeg/Tesseract processes mostly add memory use


def count():
    """How many jobs run at once: one per CPU core, at most MAX_WORKERS.
    SCREENCAP_WORKERS overrides it (1 runs everything one at a time)."""
    try:
        wanted = int(os.environ.get("SCREENCAP_WORKERS", ""))
    except ValueError:
        wanted = 0
    if wanted > 0:
        return wanted
    return max(1, min(MAX_WORKERS, os.cpu_count() or 1))


class Cancelled(Exception):
    """The cancel event was set while jobs were running."""


def run_all(fn, items, cancel=None, done=None):
    """fn(item) for every item, several at a time, returning the results in
    the order of items. done(finished, total) is called (from this thread)
    as jobs finish. When cancel (a threading.Event) is set, or a job fails,
    jobs not started yet are dropped and Cancelled or the job's error is
    raised once the running ones end."""
    items = list(items)
    if not items:
        return []
    results = [None] * len(items)
    workers = min(count(), len(items))
    if workers == 1:
        for i, item in enumerate(items):
            if cancel is not None and cancel.is_set():
                raise Cancelled()
            results[i] = fn(item)
            if done is not None:
                done(i + 1, len(items))
        return results
    stop = threading.Event()

    def job(i):
        if stop.is_set() or (cancel is not None and cancel.is_set()):
            return
        results[i] = fn(items[i])

    error, finished = None, 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        pending = {pool.submit(job, i) for i in range(len(items))}
        while pending:
            complete, pending = wait(pending, timeout=0.2, return_when=FIRST_COMPLETED)
            for future in complete:
                exc = future.exception()
                if exc is not None and error is None:
                    error = exc
                finished += 1
            if error is not None or (cancel is not None and cancel.is_set()):
                stop.set()
            elif complete and done is not None:
                done(finished, len(items))
    if error is not None:
        raise error
    if cancel is not None and cancel.is_set():
        raise Cancelled()
    return results
