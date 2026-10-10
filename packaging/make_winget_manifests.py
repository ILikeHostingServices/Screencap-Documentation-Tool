#!/usr/bin/env python3
#
# make_winget_manifests.py
# 2026-10-10
# Version: v1.0.1
#
# PURPOSE:
# Writes the Windows Package Manager (winget) manifest for one release: the
# three YAML files that microsoft/winget-pkgs expects (version, installer,
# and en-US locale), filled in from the templates in packaging/winget/. The
# installer's SHA-256 is read from the release's SHA256SUMS.txt (or computed
# from a local file), so the manifest always matches the published download.
#
# Run from the repository root:
#   python packaging/make_winget_manifests.py --version 1.16.0 \
#       --sha256-file release/SHA256SUMS.txt --out build/winget
# Output: build/winget/<version>/ILHS.ScreencapDocumentationTool*.yaml

import argparse
import datetime
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "packaging" / "winget"
PACKAGE_ID = "ILHS.ScreencapDocumentationTool"
REPO_URL = "https://github.com/ILikeHostingServices/Screencap-Documentation-Tool"
SETUP_NAME = "Screencap-Documentation-Tool-v{version}-windows-x64-setup.exe"
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")


def installer_sha256(version, sha256_file=None, installer=None):
    """The installer's SHA-256 (upper case, as winget writes it)."""
    name = SETUP_NAME.format(version=version)
    if installer:
        return hashlib.sha256(Path(installer).read_bytes()).hexdigest().upper()
    for line in Path(sha256_file).read_text(encoding="ascii").splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1].lstrip("*") == name:
            return parts[0].upper()
    raise SystemExit(f"{name} is not listed in {sha256_file}")


def write_manifests(version, sha256, out_dir, release_date=None):
    if not VERSION_RE.match(version):
        raise SystemExit(f"Version must be X.Y.Z (got {version})")
    if not re.fullmatch(r"[0-9A-F]{64}", sha256):
        raise SystemExit(f"Not a SHA-256 hash: {sha256}")
    values = {
        "PACKAGE_ID": PACKAGE_ID,
        "VERSION": version,
        "REPO_URL": REPO_URL,
        "INSTALLER_URL": f"{REPO_URL}/releases/download/v{version}/"
                         + SETUP_NAME.format(version=version),
        "SHA256": sha256,
        "RELEASE_DATE": release_date or datetime.date.today().isoformat(),
    }
    target = Path(out_dir) / version
    target.mkdir(parents=True, exist_ok=True)
    written = []
    for template in sorted(TEMPLATES.glob("*.yaml")):
        text = template.read_text(encoding="utf-8")
        for key, value in values.items():
            text = text.replace("{" + key + "}", value)
        left = re.findall(r"\{[A-Z_]+\}", text)
        if left:
            raise SystemExit(f"{template.name}: unknown placeholders {left}")
        path = target / template.name.replace("PACKAGE", PACKAGE_ID)
        path.write_text(text, encoding="utf-8", newline="\n")
        written.append(path)
    return written


def main(argv=None):
    p = argparse.ArgumentParser(description="Write the winget manifest for one release.")
    p.add_argument("--version", required=True, help="Release version, X.Y.Z")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--sha256-file", help="The release's SHA256SUMS.txt")
    src.add_argument("--installer", help="The setup .exe (hashed locally)")
    p.add_argument("--release-date", help="YYYY-MM-DD (default: today)")
    p.add_argument("--out", default="build/winget", help="Output folder")
    args = p.parse_args(argv)
    sha = installer_sha256(args.version, args.sha256_file, args.installer)
    for path in write_manifests(args.version, sha, args.out, args.release_date):
        print(path)


if __name__ == "__main__":
    sys.exit(main())
