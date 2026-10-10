#!/usr/bin/env bash
#
# make_pkgbuild.sh
# 2026-10-10
# Version: v1.0.0
#
# PURPOSE:
# Writes the Arch Linux PKGBUILD for one version from PKGBUILD.in.
#   make_pkgbuild.sh VERSION OUTDIR            release: source is the GitHub
#                                              tag archive (downloaded to hash it)
#   make_pkgbuild.sh VERSION OUTDIR TARBALL    test build: a local source archive
#                                              (git archive), copied next to it

set -euo pipefail

VERSION="${1:?usage: make_pkgbuild.sh VERSION OUTDIR [TARBALL]}"
OUT="${2:?usage: make_pkgbuild.sh VERSION OUTDIR [TARBALL]}"
TARBALL="${3:-}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
[[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo "Version must be X.Y.Z" >&2; exit 2; }
mkdir -p "$OUT"

if [ -n "$TARBALL" ]; then
    name="screencap-documentation-tool-$VERSION.tar.gz"
    cp "$TARBALL" "$OUT/$name"
    source="$name"
    sha="$(sha256sum "$OUT/$name" | cut -d' ' -f1)"
else
    url="https://github.com/ILikeHostingServices/Screencap-Documentation-Tool/archive/refs/tags/v$VERSION.tar.gz"
    source="screencap-documentation-tool-$VERSION.tar.gz::$url"
    sha="$(curl -fsSL "$url" | sha256sum | cut -d' ' -f1)"
fi
sed -e "s|@VERSION@|$VERSION|" -e "s|@SOURCE@|$source|" -e "s|@SHA256@|$sha|" \
    "$HERE/PKGBUILD.in" > "$OUT/PKGBUILD"
echo "Wrote $OUT/PKGBUILD (source $source, sha256 $sha)"
