#!/usr/bin/env python3
#
# make_winget_manifests.py
# 2026-10-11
# Version: v1.1.0
#
# PURPOSE:
# Writes the Windows Package Manager (winget) manifest for one release: the
# three YAML files that microsoft/winget-pkgs expects (version, installer,
# and en-US locale), filled in from the templates in packaging/winget/. The
# installers' SHA-256 values are read from the release's SHA256SUMS.txt (or
# computed from local files), so the manifest always matches the published
# downloads. The Windows on ARM (arm64) installers are listed when the
# release has one; winget then picks the right one for each PC.
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
SETUP_NAME = "Screencap-Documentation-Tool-v{version}-windows-{arch}-setup.exe"
ARM64_BLOCK = re.compile(r"^# arm64 begin.*?^# arm64 end\n", re.M | re.S)
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")


def installer_sha256(version, sha256_file=None, installer=None, arch="x64", required=True):
    """The installer's SHA-256 (upper case, as winget writes it), or None for
    an optional installer the release does not have."""
    name = SETUP_NAME.format(version=version, arch=arch)
    if installer:
        return hashlib.sha256(Path(installer).read_bytes()).hexdigest().upper()
    if sha256_file:
        for line in Path(sha256_file).read_text(encoding="ascii").splitlines():
            parts = line.split()
            if len(parts) == 2 and parts[1].lstrip("*") == name:
                return parts[0].upper()
    if required:
        raise SystemExit(f"{name} is not listed in {sha256_file}")
    return None


def write_manifests(version, sha256, out_dir, release_date=None, arm64_sha256=None):
    if not VERSION_RE.match(version):
        raise SystemExit(f"Version must be X.Y.Z (got {version})")
    for value in filter(None, (sha256, arm64_sha256)):
        if not re.fullmatch(r"[0-9A-F]{64}", value):
            raise SystemExit(f"Not a SHA-256 hash: {value}")
    download = f"{REPO_URL}/releases/download/v{version}/"
    values = {
        "PACKAGE_ID": PACKAGE_ID,
        "VERSION": version,
        "REPO_URL": REPO_URL,
        "INSTALLER_URL": download + SETUP_NAME.format(version=version, arch="x64"),
        "SHA256": sha256,
        "ARM64_INSTALLER_URL": download + SETUP_NAME.format(version=version, arch="arm64"),
        "ARM64_SHA256": arm64_sha256 or "",
        "RELEASE_DATE": release_date or datetime.date.today().isoformat(),
    }
    target = Path(out_dir) / version
    target.mkdir(parents=True, exist_ok=True)
    written = []
    for template in sorted(TEMPLATES.glob("*.yaml")):
        text = template.read_text(encoding="utf-8")
        text = ARM64_BLOCK.sub(lambda m: m.group(0) if arm64_sha256 else "", text)
        text = re.sub(r"^# arm64 (begin|end).*\n", "", text, flags=re.M)
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
    src.add_argument("--installer", help="The x64 setup .exe (hashed locally)")
    p.add_argument("--arm64-installer", help="The arm64 setup .exe (hashed locally; optional)")
    p.add_argument("--release-date", help="YYYY-MM-DD (default: today)")
    p.add_argument("--out", default="build/winget", help="Output folder")
    args = p.parse_args(argv)
    sha = installer_sha256(args.version, args.sha256_file, args.installer)
    arm64 = installer_sha256(args.version, args.sha256_file if not args.arm64_installer else None,
                             args.arm64_installer, arch="arm64", required=False)
    for path in write_manifests(args.version, sha, args.out, args.release_date, arm64):
        print(path)


if __name__ == "__main__":
    sys.exit(main())
