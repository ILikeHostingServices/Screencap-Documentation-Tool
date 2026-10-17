#!/usr/bin/env bash
#
# make_repos.sh
# 2026-10-17
# Version: v1.0.2
#
# PURPOSE:
# Builds the signed apt and dnf (rpm-md) package repositories that are
# published on GitHub Pages, so `sudo apt install screencap-documentation-tool`
# and `sudo dnf install screencap-documentation-tool` work and updates arrive
# with the system's normal updates. The .deb and .rpm files are the ones
# attached to the GitHub releases. Output layout (under --out):
#   ilhs-archive-keyring.gpg   public key for apt (binary, for Signed-By)
#   ilhs-archive-key.asc       public key for dnf and zypper (armored)
#   apt/pool/main/*.deb
#   apt/dists/stable/{Release,Release.gpg,InRelease}
#   apt/dists/stable/main/binary-<arch>/Packages(.gz)
#   apt/screencap-docs.sources the apt source file users download
#   rpm/*.rpm                  signed with the same key
#   rpm/repodata/ (+ repomd.xml.asc)
#   rpm/screencap-docs.repo    the dnf/zypper repository file users download
# The signing key must already be in the gpg keyring (GNUPGHOME); its
# passphrase is read from --passphrase-file and never printed. Every
# signature is checked again before the script ends.
#
# Needs: gpg, apt-ftparchive (apt-utils), createrepo_c, rpmsign (rpm).
#
# Usage:
#   make_repos.sh --key FINGERPRINT --passphrase-file FILE \
#       --url https://screencap.ilhs.app \
#       --out site/ PACKAGE.deb ... PACKAGE.rpm ...

set -euo pipefail

KEY="" PASSFILE="" URL="" OUT=""
while [ $# -gt 0 ]; do
    case "$1" in
        --key) KEY="$2"; shift 2 ;;
        --passphrase-file) PASSFILE="$2"; shift 2 ;;
        --url) URL="${2%/}"; shift 2 ;;
        --out) OUT="$2"; shift 2 ;;
        --) shift; break ;;
        -*) echo "Unknown option: $1" >&2; exit 2 ;;
        *) break ;;
    esac
done
if [ -z "$KEY" ] || [ -z "$PASSFILE" ] || [ -z "$URL" ] || [ -z "$OUT" ] || [ $# -eq 0 ]; then
    sed -n '/^# Usage:/,/^$/p' "$0" >&2
    exit 2
fi
[ -r "$PASSFILE" ] || { echo "Passphrase file not readable: $PASSFILE" >&2; exit 2; }
PASSFILE="$(cd "$(dirname "$PASSFILE")" && pwd)/$(basename "$PASSFILE")"   # used after cd

ARCHES="all amd64 arm64 armhf i386"
GPG=(gpg --batch --yes --pinentry-mode loopback --passphrase-file "$PASSFILE" --local-user "$KEY")

mkdir -p "$OUT/apt/pool/main" "$OUT/rpm"
OUT="$(cd "$OUT" && pwd)"

debs=0 rpms=0
for f in "$@"; do
    case "$f" in
        *.deb) cp "$f" "$OUT/apt/pool/main/"; debs=$((debs + 1)) ;;
        *.rpm) cp "$f" "$OUT/rpm/"; rpms=$((rpms + 1)) ;;
        *) echo "Not a .deb or .rpm, skipped: $f" >&2 ;;
    esac
done
if [ "$debs" -eq 0 ] || [ "$rpms" -eq 0 ]; then
    echo "Need at least one .deb and one .rpm" >&2
    exit 1
fi
echo "Packages: $debs .deb, $rpms .rpm"

# The public key, in the two forms the package managers want
gpg --batch --yes --export "$KEY" > "$OUT/ilhs-archive-keyring.gpg"
gpg --batch --yes --armor --export "$KEY" > "$OUT/ilhs-archive-key.asc"

# apt: one Packages index (the packages are "all"), listed for every
# architecture so apt finds it whatever the machine is
(
    cd "$OUT/apt"
    apt-ftparchive packages pool > Packages.tmp
    for arch in $ARCHES; do
        dir="dists/stable/main/binary-$arch"
        mkdir -p "$dir"
        cp Packages.tmp "$dir/Packages"
        gzip -9n -c Packages.tmp > "$dir/Packages.gz"
    done
    rm Packages.tmp
    cd dists/stable
    apt-ftparchive \
        -o APT::FTPArchive::Release::Origin="ILHS" \
        -o APT::FTPArchive::Release::Label="ScreenCap Docs" \
        -o APT::FTPArchive::Release::Suite="stable" \
        -o APT::FTPArchive::Release::Codename="stable" \
        -o APT::FTPArchive::Release::Architectures="$ARCHES" \
        -o APT::FTPArchive::Release::Components="main" \
        -o APT::FTPArchive::Release::Description="ScreenCap Docs packages from ILHS Software, LLC" \
        release . > Release.tmp
    mv Release.tmp Release
    "${GPG[@]}" --clearsign --digest-algo SHA512 -o InRelease Release
    "${GPG[@]}" --detach-sign --armor --digest-algo SHA512 -o Release.gpg Release
)
cat > "$OUT/apt/screencap-docs.sources" <<EOF
Types: deb
URIs: $URL/apt
Suites: stable
Components: main
Signed-By: /etc/apt/keyrings/ilhs-archive-keyring.gpg
EOF

# rpm: sign each package, then the repository metadata
rpmsign --addsign \
    --define "_gpg_name $KEY" \
    --define "_gpg_path ${GNUPGHOME:-$HOME/.gnupg}" \
    --define "_gpg_sign_cmd_extra_args --batch --pinentry-mode loopback --passphrase-file $PASSFILE" \
    --define "_gpg_digest_algo sha256" \
    "$OUT"/rpm/*.rpm > /dev/null
createrepo_c --quiet --update "$OUT/rpm"
"${GPG[@]}" --detach-sign --armor --digest-algo SHA512 -o "$OUT/rpm/repodata/repomd.xml.asc" "$OUT/rpm/repodata/repomd.xml"
cat > "$OUT/rpm/screencap-docs.repo" <<EOF
[screencap-docs]
name=ScreenCap Docs
baseurl=$URL/rpm
enabled=1
gpgcheck=1
repo_gpgcheck=1
gpgkey=$URL/ilhs-archive-key.asc
EOF

# Check every signature with only the public key, as a user's PC would
CHECK="$(mktemp -d)"
trap 'rm -rf "$CHECK"' EXIT
mkdir -m 700 "$CHECK/gpg"
gpg --batch --quiet --homedir "$CHECK/gpg" --import "$OUT/ilhs-archive-key.asc"
for sig in "apt/dists/stable/InRelease" "apt/dists/stable/Release.gpg apt/dists/stable/Release" \
           "rpm/repodata/repomd.xml.asc rpm/repodata/repomd.xml"; do
    # shellcheck disable=SC2086
    (cd "$OUT" && gpg --batch --status-fd 1 --homedir "$CHECK/gpg" --verify $sig 2>/dev/null | grep -q "^\[GNUPG:\] VALIDSIG") \
        || { echo "Signature check failed: $sig" >&2; exit 1; }
done
rpm --dbpath "$CHECK/rpmdb" --initdb
rpm --dbpath "$CHECK/rpmdb" --import "$OUT/ilhs-archive-key.asc"
for f in "$OUT"/rpm/*.rpm; do
    rpm --dbpath "$CHECK/rpmdb" --checksig "$f" | grep -q "digests signatures OK" \
        || { echo "Package signature check failed: $f" >&2; rpm --dbpath "$CHECK/rpmdb" -Kv "$f" >&2; exit 1; }
done
echo "Repositories written to $OUT and every signature checked."
