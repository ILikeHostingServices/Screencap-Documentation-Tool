#!/usr/bin/env python3
#
# redact.py
# 2026-10-04
# Version: v1.0.1
#
# PURPOSE:
# Finds sensitive information in screenshots so it can be blurred: reads the
# text with Tesseract OCR (free, open source) and matches it against
# patterns for IP and MAC addresses, email addresses, GUIDs, license keys,
# API tokens and other secret-looking strings, masked passwords, and values
# that follow labels such as "Password:". Extra patterns can be added.
#
# Tesseract is optional: without it, automatic detection is skipped and
# manual blur boxes still work.

import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
import apppaths  # noqa: E402

SCRIPT_DIR = apppaths.APP_DIR

TESSERACT_MISSING_HELP = (
    "Tesseract OCR was not found, so sensitive text cannot be detected "
    "automatically (manual blur boxes still work). Install it with:\n"
    "  Windows 11:  winget install --id UB-Mannheim.TesseractOCR -e\n"
    "  Linux:       sudo apt install tesseract-ocr\n"
    "  macOS:       brew install tesseract")

# Pattern name -> regex, matched against each line of text read from the screen
PATTERNS = {
    "IP address": r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)"
                  r"(?:/\d{1,2}|:\d{1,5})?\b",
    "IPv6 address": r"\b(?:[0-9a-fA-F]{1,4}:){2,7}(?::|[0-9a-fA-F]{1,4})\b",
    "MAC address": r"\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b",
    "email address": r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b",
    "GUID": r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b",
    "license key": r"\b[A-Z0-9]{4,6}(?:-[A-Z0-9]{4,6}){2,}\b",
    "token": r"\b(?:gh[pousr]_|github_pat_|sk-|xox[abprs]-|AKIA|AIza|eyJ)[\w\-.=+/]{8,}",
    "secret-looking string": r"(?<![\w/])(?=[\w\-+/=]*\d)(?=[\w\-+/=]*[A-Za-z])"
                             r"[\w\-+/=]{24,}(?![\w/])",
    "masked password": r"[\u2022\u25cf\u00b7*]{4,}",   # bullets, dots, asterisks
}

# Words that label a secret; everything after them on the same line is blurred
LABEL_RE = re.compile(
    r"^(?:password|passwd|pwd|passphrase|pass|secret|token|pin|api[-_]?key|"
    r"key|license|licence|serial|product\s?key|client\s?secret|access\s?key)"
    r"\s*[:=]$", re.IGNORECASE)
LABEL_PAIRS = re.compile(r"^(?:product|client|access|api|secret|license|recovery)$",
                         re.IGNORECASE)


def find_tesseract(explicit=None):
    """Explicit path, a portable copy in tools/tesseract, the PATH, then the
    usual Windows install folders (the installer does not add itself to PATH)."""
    if explicit:
        return explicit if Path(explicit).is_file() else None
    exe = "tesseract.exe" if os.name == "nt" else "tesseract"
    candidates = [SCRIPT_DIR / "tools" / "tesseract" / exe]
    found = shutil.which("tesseract")
    if found:
        return found
    if os.name == "nt":
        for base in (os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)"),
                     os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs")):
            if base:
                candidates.append(Path(base) / "Tesseract-OCR" / exe)
    for c in candidates:
        if c.is_file():
            return str(c)
    return None


def read_words(tesseract, image):
    """OCR an image. Returns lines: lists of (text, [x, y, w, h])."""
    with tempfile.TemporaryDirectory(prefix="screencap_ocr_") as tmp:
        res = subprocess.run([tesseract, str(image), str(Path(tmp) / "ocr"), "--psm", "3",
                              "tsv"],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                             errors="replace", stdin=subprocess.DEVNULL,
                             creationflags=NO_WINDOW)
        tsv = Path(tmp) / "ocr.tsv"
        if res.returncode != 0 or not tsv.is_file():
            raise RuntimeError(f"Tesseract failed: {res.stderr.strip()[-300:]}")
        rows = tsv.read_text(encoding="utf-8", errors="replace").splitlines()
    lines = {}
    for row in rows[1:]:
        cols = row.split("\t")
        if len(cols) < 12 or not cols[11].strip():
            continue
        try:
            if float(cols[10]) < 0:
                continue
            key = (int(cols[2]), int(cols[3]), int(cols[4]))
            box = [int(cols[6]), int(cols[7]), int(cols[8]), int(cols[9])]
        except ValueError:
            continue
        lines.setdefault(key, []).append((cols[11].strip(), box))
    return [lines[k] for k in sorted(lines)]


def union(boxes, pad, width, height):
    x0 = min(b[0] for b in boxes) - pad
    y0 = min(b[1] for b in boxes) - pad
    x1 = max(b[0] + b[2] for b in boxes) + pad
    y1 = max(b[1] + b[3] for b in boxes) + pad
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(width, x1), min(height, y1)
    return [x0, y0, x1 - x0, y1 - y0]


def find_sensitive(lines, width, height, extra_patterns=()):
    """Regions to blur: list of {"box": [x, y, w, h], "reason": str}."""
    patterns = [(name, re.compile(rx)) for name, rx in PATTERNS.items()]
    for rx in extra_patterns:
        if rx.strip():
            patterns.append(("custom pattern", re.compile(rx, re.IGNORECASE)))
    pad = max(3, width // 400)
    found = []
    for words in lines:
        # Line text with each word's character span, so a match can be
        # mapped back to the words (and boxes) it covers
        text, spans = "", []
        for word, box in words:
            if text:
                text += " "
            spans.append((len(text), len(text) + len(word), box))
            text += word
        for name, rx in patterns:
            for m in rx.finditer(text):
                hit = [box for start, end, box in spans if start < m.end() and end > m.start()]
                if hit:
                    found.append({"box": union(hit, pad, width, height), "reason": name})
        # "Password: value" -> blur everything after the label on that line
        for i, (word, _box) in enumerate(words):
            label = LABEL_RE.match(word)
            if not label and i > 0 and LABEL_PAIRS.match(words[i - 1][0]):
                label = LABEL_RE.match(words[i - 1][0] + " " + word)
            if label and i + 1 < len(words):
                found.append({"box": union([b for _, b in words[i + 1:]], pad, width, height),
                              "reason": f"value after '{word}'"})
    return dedupe(found)


def dedupe(regions):
    """Drop regions fully inside another region."""
    out = []
    for r in sorted(regions, key=lambda r: -r["box"][2] * r["box"][3]):
        x, y, w, h = r["box"]
        inside = any(o["box"][0] <= x and o["box"][1] <= y and
                     x + w <= o["box"][0] + o["box"][2] and y + h <= o["box"][1] + o["box"][3]
                     for o in out)
        if not inside:
            out.append(r)
    return out


def scan_image(tesseract, image, width, height, extra_patterns=()):
    return find_sensitive(read_words(tesseract, image), width, height, extra_patterns)
