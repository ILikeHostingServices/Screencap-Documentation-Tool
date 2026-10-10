#!/usr/bin/env python3
#
# build_packages.py
# 2026-10-10
# Version: v1.0.0
#
# PURPOSE:
# Builds the .deb (Debian, Ubuntu, Mint, Pop!_OS) and .rpm (Fedora, RHEL
# and its rebuilds, openSUSE) packages with nfpm. Each package is staged
# with packaging/linux/stage.sh (the same layout as the Arch and snap
# packages), then nfpm is given an explicit list of every file, so the
# package owns exactly those files and its own folders.
#
# Needs nfpm (https://nfpm.goreleaser.com). Run from the repository root:
#   python3 packaging/linux/build_packages.py --out release
# Output: screencap-documentation-tool_<version>_all.deb and
#         screencap-documentation-tool-<version>-1.noarch.rpm

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import version  # noqa: E402

NAME = "screencap-documentation-tool"
OWN_DIRS = (f"/usr/share/{NAME}", f"/usr/share/{NAME}/assets",
            f"/usr/share/licenses/{NAME}", f"/usr/share/doc/{NAME}")
DESCRIPTION = (
    "Turns screen recordings into step-by-step screenshot documentation.\n"
    "Finds every step in a recording with FFmpeg scene detection and saves a\n"
    "screenshot of each one. Review the steps, add captions, crop, blur\n"
    "sensitive information, and export to HTML, Word, or PDF. Everything runs\n"
    "locally, with no telemetry.")

# Package names differ between distributions; rpm "rich" dependencies
# (A or B) cover Fedora/RHEL and openSUSE in one package
DEPENDS = {
    "deb": {
        "depends": ["python3 (>= 3.8)", "python3-tk", "ffmpeg"],
        "recommends": ["tesseract-ocr", "tesseract-ocr-eng", "pandoc", "xdg-utils"],
        "suggests": ["vlc", "chromium | chromium-browser | google-chrome-stable"],
    },
    "rpm": {
        "depends": ["python3 >= 3.8", "(python3-tkinter or python3-tk)",
                    "/usr/bin/ffmpeg", "/usr/bin/ffprobe"],
        "recommends": ["(tesseract or tesseract-ocr)", "pandoc", "xdg-utils",
                       "(dejavu-sans-fonts or dejavu-fonts)"],
        "suggests": ["vlc"],
    },
}


def nfpm_config(kind, stage):
    contents = [{"dst": d, "type": "dir", "file_info": {"mode": 0o755}} for d in OWN_DIRS]
    for path in sorted(p for p in stage.rglob("*") if p.is_file()):
        dst = "/" + path.relative_to(stage).as_posix()
        mode = 0o755 if os.access(path, os.X_OK) else 0o644
        contents.append({"src": str(path), "dst": dst, "file_info": {"mode": mode}})
    deps = DEPENDS[kind]
    config = {
        "name": NAME,
        "arch": "all" if kind == "deb" else "noarch",
        "platform": "linux",
        "version": version.RELEASE,
        "release": "1",
        "section": "graphics",
        "priority": "optional",
        "maintainer": "ILikeHostingServices <337515992+ILHS-Owner@users.noreply.github.com>",
        "vendor": "ILikeHostingServices",
        "homepage": "https://github.com/ILikeHostingServices/Screencap-Documentation-Tool",
        "license": "MIT",
        "description": DESCRIPTION,
        "depends": deps["depends"],
        "recommends": deps["recommends"],
        "suggests": deps["suggests"],
        "contents": contents,
    }
    if kind == "rpm":
        config["rpm"] = {"group": "Applications/Multimedia", "summary":
                         "Turns screen recordings into step-by-step screenshot documentation"}
    return config


def build(kind, out, nfpm):
    work = ROOT / "build" / "linux" / kind
    shutil.rmtree(work, ignore_errors=True)
    stage = work / "stage"
    subprocess.run(["bash", str(ROOT / "packaging/linux/stage.sh"), str(stage), kind], check=True)
    config = work / "nfpm.json"      # JSON is valid YAML, which nfpm reads
    config.write_text(json.dumps(nfpm_config(kind, stage), indent=2), encoding="utf-8")
    out.mkdir(parents=True, exist_ok=True)
    packager = "deb" if kind == "deb" else "rpm"
    subprocess.run([nfpm, "package", "--config", str(config), "--packager", packager,
                    "--target", str(out)], check=True)


def main(argv=None):
    p = argparse.ArgumentParser(description="Build the .deb and .rpm packages.")
    p.add_argument("--out", default="release", help="Output folder (default: release)")
    p.add_argument("--kind", choices=("deb", "rpm"), action="append",
                   help="Build only this kind (default: both)")
    p.add_argument("--nfpm", default=shutil.which("nfpm") or "nfpm", help="Path to nfpm")
    args = p.parse_args(argv)
    for kind in args.kind or ("deb", "rpm"):
        build(kind, (ROOT / args.out).resolve(), args.nfpm)
    for f in sorted((ROOT / args.out).glob(f"{NAME}*")):
        print(f.name)


if __name__ == "__main__":
    sys.exit(main())
