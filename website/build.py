#!/usr/bin/env python3
#
# build.py
# 2026-10-22
# Version: v1.0.0
#
# PURPOSE:
# Builds the website at https://screencap.ilhs.app: one page per menu link,
# all sharing the header, menu, and footer written once in layout.html (the
# same way the ilhs.app site is built). Writes the pages and copies the
# styles, the scripts, the icon (assets/icon.png), and the screenshots
# (docs/screenshots/) into one folder, then checks that every link between
# the pages, and to their pictures and section ids, exists.
# Run by .github/workflows/package-repos.yml, which publishes the folder to
# GitHub Pages with the apt and dnf repositories. Python 3.8+, standard
# library only.
#
# INPUTS:
#   website/site.json      Menu items and site URL.
#   website/layout.html    The shared page frame, with {{placeholders}}.
#   website/pages/*.html   One file per page, starting with
#                            <!--
#                            title: Download
#                            description: One sentence for search results.
#                            -->
#                          then the page's content. Write links between pages
#                          and to files as {{root}}download/ or
#                          {{root}}screenshots/..., never with a leading slash.
#                          {{version}} is the release the download links point
#                          at, and {{download}} that release's download folder.
#                          index.html is the home page, 404.html the page
#                          GitHub Pages shows for a missing address.
#   website/assets/        site.css and site.js.
#
# USAGE:
#   python3 website/build.py --out DIR [--version 1.36.1] [--allow-missing NAME ...]
#   --version defaults to the version in version.py; the workflow passes the
#   newest published release. --allow-missing names a file another step adds
#   to the same folder (the workflow needs none: the repositories are there).
#   Preview: python3 -m http.server 8080 --directory DIR

import argparse
import hashlib
import html
import json
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DOWNLOAD = "https://github.com/ILikeHostingServices/Screencap-Documentation-Tool/releases/download/v{}/"

META_RE = re.compile(r"\A<!--\n(?P<meta>.*?)\n-->\n", re.DOTALL)
PLACEHOLDER_RE = re.compile(r"\{\{(\w+)\}\}")
LINK_RE = re.compile(r'(?:href|src)="([^"]*)"')
ID_RE = re.compile(r'\sid="([^"]+)"')


class BuildError(Exception):
    pass


def release_version():
    text = (ROOT / "version.py").read_text(encoding="utf-8")
    return re.search(r'^RELEASE = "([^"]+)"', text, re.MULTILINE).group(1)


def load_page(path):
    text = path.read_text(encoding="utf-8")
    m = META_RE.match(text)
    if not m:
        raise BuildError(f"{path.name} must start with a <!-- title: / description: --> block")
    meta = {}
    for line in m.group("meta").splitlines():
        key, sep, value = line.partition(":")
        if not sep:
            raise BuildError(f"{path.name}: bad metadata line {line!r}")
        meta[key.strip()] = value.strip()
    for key in ("title", "description"):
        if key not in meta:
            raise BuildError(f"{path.name}: missing '{key}'")
    return meta, text[m.end():].rstrip("\n")


def fill(template, values, where):
    def sub(m):
        if m.group(1) not in values:
            raise BuildError(f"{where}: unknown placeholder {{{{{m.group(1)}}}}}")
        return values[m.group(1)]
    return PLACEHOLDER_RE.sub(sub, template)


def fingerprint(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()[:10]


def render(version):
    """Return {output path: page HTML} for every page."""
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise BuildError(f"version {version!r} is not Major.Minor.Patch")
    config = json.loads((HERE / "site.json").read_text(encoding="utf-8"))
    layout = (HERE / "layout.html").read_text(encoding="utf-8")
    pages = sorted((HERE / "pages").glob("*.html"))
    slugs = [p.stem for p in pages]
    for required in ["index", "404"] + [item["slug"] for item in config["nav"]]:
        if required not in slugs:
            raise BuildError(f"website/pages/{required}.html is missing")
    css = fingerprint(HERE / "assets" / "site.css")
    js = fingerprint(HERE / "assets" / "site.js")

    out = {}
    for path in pages:
        slug = path.stem
        meta, body = load_page(path)
        if slug == "404":
            root, target = "/", "404.html"     # shown at any depth
        elif slug == "index":
            root, target = "", "index.html"
        else:
            root, target = "../", f"{slug}/index.html"
        nav = "\n".join(
            f'      <a href="{root}{item["slug"]}/"'
            + (' aria-current="page"' if item["slug"] == slug else "")
            + f'>{html.escape(item["label"])}</a>'
            for item in config["nav"])
        title = config["home_title"] if slug == "index" else f'{meta["title"]} | {config["site_name"]}'
        desc = html.escape(meta["description"], quote=True)
        if slug == "404":
            head_extra = '\n<meta name="robots" content="noindex">'
        else:
            url = config["base_url"] + ("" if slug == "index" else f"{slug}/")
            head_extra = (f'\n<link rel="canonical" href="{url}">'
                          f'\n<meta property="og:title" content="{html.escape(title, quote=True)}">'
                          f'\n<meta property="og:description" content="{desc}">'
                          f'\n<meta property="og:url" content="{url}">'
                          '\n<meta property="og:type" content="website">')
        content = fill(body, {"root": root, "version": version,
                              "download": DOWNLOAD.format(version)}, f"pages/{path.name}")
        out[target] = fill(layout, {
            "page": slug, "title": html.escape(title), "description": desc,
            "head_extra": head_extra, "root": root, "home": root or "./",
            "nav": nav, "content": content, "css_version": css, "js_version": js,
        }, "layout.html")
    return out


def check_links(site, allow_missing=()):
    """Every local link in the built pages must reach a file, and a link
    with #id must reach an element with that id. Returns the problems."""
    problems = []
    site = Path(site).resolve()
    ids = {page: set(ID_RE.findall(page.read_text(encoding="utf-8"))) for page in site.rglob("*.html")}
    for page in sorted(ids):
        name = page.relative_to(site).as_posix()
        for link in LINK_RE.findall(page.read_text(encoding="utf-8")):
            if re.match(r"[a-z]+:", link) or link.startswith("//"):
                continue    # another site
            path, _, frag = link.partition("#")
            path = path.split("?")[0]
            if not path:
                target = page
            else:
                target = (site / path.lstrip("/")) if path.startswith("/") else (page.parent / path)
                if path.endswith("/") or target.is_dir():
                    target = target / "index.html"
                target = target.resolve()
            if not target.exists():
                if target.name not in allow_missing:
                    problems.append(f"{name} links to {link}, which is not in the site")
            elif frag and target in ids and frag not in ids[target]:
                problems.append(f"{name} links to {link}, but that page has no id {frag!r}")
    return problems


def build(out, version, allow_missing=()):
    out = Path(out)
    for rel, text in render(version).items():
        target = out / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    (out / "assets").mkdir(parents=True, exist_ok=True)
    for name in ("site.css", "site.js"):
        shutil.copy2(HERE / "assets" / name, out / "assets" / name)
    shutil.copy2(ROOT / "assets" / "icon.png", out / "icon.png")
    (out / "screenshots").mkdir(exist_ok=True)
    for png in (ROOT / "docs" / "screenshots").glob("*.png"):
        shutil.copy2(png, out / "screenshots" / png.name)
    return check_links(out, allow_missing)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build the screencap.ilhs.app pages.")
    parser.add_argument("--out", required=True, type=Path, help="folder to write the site into")
    parser.add_argument("--version", help="release the download links point at (default: version.py)")
    parser.add_argument("--allow-missing", action="append", default=[], metavar="NAME",
                        help="a linked file that another step adds to the folder")
    args = parser.parse_args(argv)
    try:
        problems = build(args.out, args.version or release_version(), args.allow_missing)
    except BuildError as e:
        print(f"build.py: error: {e}", file=sys.stderr)
        return 2
    for p in problems:
        print(f"::error::{p}")
    if problems:
        return 1
    print(f"Built the website in {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
