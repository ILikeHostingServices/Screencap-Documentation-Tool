#!/usr/bin/env python3
#
# export.py
# 2026-10-02
# Version: v1.0.1
#
# PURPOSE:
# Turns a recording's saved steps into a finished document: a single
# self-contained HTML file (images embedded), a Word .docx (via Pandoc), or
# a PDF (printed by a headless Microsoft Edge, Google Chrome, or Chromium).
# Each document starts with a header block: title, version, date, author.
#
# Exports use the blurred screenshots. The unblurred set can be exported on
# request; those files get "UNREDACTED" in the name and a warning inside.

import base64
import html
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import stepdoc

NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
EXPORT_DIR = "export"
FORMATS = ("html", "docx", "pdf")
TOOL_NAME = "Screencap Documentation Tool"

PANDOC_MISSING_HELP = (
    "Pandoc was not found, so Word export is unavailable. Install it with:\n"
    "  Windows 11:  winget install --id JohnMacFarlane.Pandoc -e\n"
    "  Linux:       sudo apt install pandoc\n"
    "  macOS:       brew install pandoc")
BROWSER_MISSING_HELP = (
    "No Microsoft Edge, Google Chrome, or Chromium was found, so PDF export is "
    "unavailable. Windows 11 includes Edge; on Linux install Chromium, or open "
    "the HTML export in any browser and print it to PDF.")


# ---------------------------------------------------------------------------
# Finding the helper programs
# ---------------------------------------------------------------------------

def find_pandoc(explicit=None):
    if explicit:
        return explicit if Path(explicit).is_file() else None
    found = shutil.which("pandoc")
    if found:
        return found
    if os.name == "nt":
        for base in (os.environ.get("LOCALAPPDATA"), os.environ.get("ProgramFiles")):
            if base and (Path(base) / "Pandoc" / "pandoc.exe").is_file():
                return str(Path(base) / "Pandoc" / "pandoc.exe")
    return None


def find_browser(explicit=None):
    """A Chromium-based browser that can print HTML to PDF without a window."""
    explicit = explicit or os.environ.get("SCREENCAP_BROWSER")
    if explicit:
        return explicit if Path(explicit).is_file() else None
    candidates = []
    if os.name == "nt":
        for base in (os.environ.get("ProgramFiles(x86)"), os.environ.get("ProgramFiles"),
                     os.environ.get("LOCALAPPDATA")):
            if base:
                candidates += [Path(base) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
                               Path(base) / "Google" / "Chrome" / "Application" / "chrome.exe"]
    elif sys.platform == "darwin":
        for app in ("Microsoft Edge", "Google Chrome", "Chromium"):
            candidates.append(Path(f"/Applications/{app}.app/Contents/MacOS/{app}"))
    else:
        for name in ("microsoft-edge", "google-chrome", "google-chrome-stable",
                     "chromium", "chromium-browser"):
            found = shutil.which(name)
            if found:
                return found
    for c in candidates:
        if c.is_file():
            return str(c)
    return None


# ---------------------------------------------------------------------------
# Document content
# ---------------------------------------------------------------------------

def metadata(doc):
    meta = doc.get("document", {})
    return {
        "title": meta.get("title") or Path(doc.get("source_video", "Steps")).stem,
        "version": meta.get("version") or "v1.0.0",
        "author": meta.get("author") or "",
        "date": time.strftime("%Y-%m-%d"),
    }


def safe_name(title):
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "_", title).strip(" .")
    return name or "steps"


def image_path(out_dir, step, unredacted):
    folder = Path(out_dir) / stepdoc.UNREDACTED_DIR if unredacted else Path(out_dir)
    path = folder / step["file"]
    if not path.is_file():
        raise RuntimeError(f"Screenshot {path.name} is missing. Save the steps in the "
                           "Steps tab (or reprocess) and export again.")
    return path


def warning_text():
    return ("UNREDACTED COPY: these screenshots are not blurred and may show passwords, "
            "keys, or internal addresses. Do not publish or share this document.")


def build_html(out_dir, doc, unredacted=False, embed=True):
    meta = metadata(doc)
    e = html.escape
    parts = [
        "<!DOCTYPE html>", '<html lang="en">', "<head>", '<meta charset="utf-8">',
        f"<title>{e(meta['title'])}</title>",
        "<style>",
        "body{font-family:Segoe UI,Arial,Helvetica,sans-serif;color:#1b1b1b;max-width:960px;"
        "margin:24px auto;padding:0 16px;line-height:1.45}",
        "header{border-bottom:2px solid #2563eb;margin-bottom:24px;padding-bottom:8px}",
        "h1{margin:0 0 8px}.meta{color:#555;font-size:0.95em}",
        ".warn{background:#fdecea;border:1px solid #e53935;color:#8e1b17;padding:10px;"
        "margin:12px 0;font-weight:bold}",
        "section.step{margin:0 0 28px;page-break-inside:avoid;break-inside:avoid}",
        "h2{font-size:1.15em;margin:0 0 8px}.time{color:#777;font-weight:normal;font-size:0.85em}",
        "img{max-width:100%;border:1px solid #ccc}",
        "p.caption{margin:8px 0 0;white-space:pre-wrap}",
        "footer{color:#888;font-size:0.8em;border-top:1px solid #ddd;margin-top:32px;padding-top:8px}",
        "</style>", "</head>", "<body>", "<header>",
        f"<h1>{e(meta['title'])}</h1>",
        f'<div class="meta">Version {e(meta["version"])} &middot; {e(meta["date"])}'
        + (f" &middot; {e(meta['author'])}" if meta["author"] else "") + "</div>",
        "</header>",
    ]
    if unredacted:
        parts.append(f'<div class="warn">{e(warning_text())}</div>')
    for i, step in enumerate(doc["steps"], 1):
        img = image_path(out_dir, step, unredacted)
        if embed:
            mime = "image/jpeg" if img.suffix.lower() == ".jpg" else "image/png"
            src = f"data:{mime};base64,{base64.b64encode(img.read_bytes()).decode('ascii')}"
        else:
            src = img.as_uri()
        parts += ['<section class="step">',
                  f'<h2>Step {i} <span class="time">({stepdoc.fmt_ts(step["time"])})</span></h2>',
                  f'<img src="{src}" alt="Step {i}">']
        caption = (step.get("caption") or "").strip()
        if caption:
            parts.append(f'<p class="caption">{e(caption)}</p>')
        parts.append("</section>")
    parts += [f"<footer>Created with {TOOL_NAME} from {e(doc.get('source_video', ''))}</footer>",
              "</body>", "</html>"]
    return "\n".join(parts)


def build_markdown(out_dir, doc, unredacted=False):
    """Pandoc Markdown with a metadata block, for the Word export."""
    meta = metadata(doc)

    def yaml(value):
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'

    lines = ["---", f"title: {yaml(meta['title'])}",
             f"subtitle: {yaml('Version ' + meta['version'])}",
             f"date: {yaml(meta['date'])}"]
    if meta["author"]:
        lines.append(f"author: {yaml(meta['author'])}")
    lines += ["---", ""]
    if unredacted:
        lines += [f"**{warning_text()}**", ""]
    for i, step in enumerate(doc["steps"], 1):
        img = image_path(out_dir, step, unredacted).as_posix()
        lines += [f"## Step {i}", "", f"![]({img}){{width=100%}}", ""]
        caption = (step.get("caption") or "").strip()
        if caption:
            lines += [caption, ""]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

def export(out_dir, doc, fmt, unredacted=False, pandoc=None, browser=None):
    """Write one export and return its path."""
    out_dir = Path(out_dir)
    if unredacted and not (out_dir / stepdoc.UNREDACTED_DIR).is_dir():
        raise RuntimeError("There are no unblurred screenshots for this recording "
                           "(blurring is off, so the normal export already shows everything).")
    dest_dir = out_dir / EXPORT_DIR
    dest_dir.mkdir(exist_ok=True)
    stem = safe_name(metadata(doc)["title"]) + ("-UNREDACTED" if unredacted else "")
    dest = dest_dir / f"{stem}.{fmt}"

    if fmt == "html":
        dest.write_text(build_html(out_dir, doc, unredacted), encoding="utf-8")
    elif fmt == "docx":
        pandoc = pandoc or find_pandoc()
        if not pandoc:
            raise RuntimeError(PANDOC_MISSING_HELP)
        with tempfile.TemporaryDirectory(prefix="screencap_export_") as tmp:
            md = Path(tmp) / "steps.md"
            md.write_text(build_markdown(out_dir, doc, unredacted), encoding="utf-8")
            _run([pandoc, str(md), "-f", "markdown", "-o", str(dest),
                  f"--resource-path={out_dir}"], "Pandoc")
    elif fmt == "pdf":
        browser = browser or find_browser()
        if not browser:
            raise RuntimeError(BROWSER_MISSING_HELP)
        with tempfile.TemporaryDirectory(prefix="screencap_export_") as tmp:
            page = Path(tmp) / "steps.html"
            page.write_text(build_html(out_dir, doc, unredacted), encoding="utf-8")
            if dest.exists():
                dest.unlink()
            cmd = [browser, "--headless=new", "--disable-gpu", "--no-first-run",
                   "--no-pdf-header-footer", "--print-to-pdf-no-header",
                   f"--user-data-dir={Path(tmp) / 'profile'}",
                   f"--print-to-pdf={dest}", page.as_uri()]
            if (hasattr(os, "geteuid") and os.geteuid() == 0) or os.environ.get("SCREENCAP_NO_SANDBOX"):
                # Chromium refuses to run as root, and some Linux CI machines
                # block its sandbox; SCREENCAP_NO_SANDBOX=1 is set only there
                cmd.insert(1, "--no-sandbox")
            _run(cmd, "The browser", timeout=180)
            if not dest.is_file():
                raise RuntimeError("The browser did not produce a PDF.")
    else:
        raise ValueError(f"Unknown export format: {fmt}")
    return dest


def _run(cmd, what, timeout=300):
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                         errors="replace", stdin=subprocess.DEVNULL, creationflags=NO_WINDOW,
                         timeout=timeout)
    if res.returncode != 0:
        raise RuntimeError(f"{what} failed: {res.stderr.strip()[-400:]}")
    return res
