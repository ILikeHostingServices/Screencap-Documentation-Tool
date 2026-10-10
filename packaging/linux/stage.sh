#!/usr/bin/env bash
#
# stage.sh
# 2026-10-10
# Version: v1.0.0
#
# PURPOSE:
# Installs the Screencap Documentation Tool into a staging folder with the
# layout every Linux package uses, so the .deb, .rpm, Arch (PKGBUILD), and
# snap packages are built from one recipe:
#   /usr/share/screencap-documentation-tool/   the program (Python files, icon)
#   /usr/bin/screencap, /usr/bin/screencap-gui launchers
#   /usr/share/applications/...desktop          application menu entry
#   /usr/share/metainfo/...metainfo.xml         software center details
#   /usr/share/icons/hicolor/256x256/apps/      icon
#   /usr/share/licenses/..., /usr/share/doc/... license and README
# The package-kind file tells the program it was installed from a package,
# so its default folders go in ~/Documents (see apppaths.py).
#
# Usage, from the repository root:
#   packaging/linux/stage.sh DESTDIR KIND      (KIND: deb, rpm, arch, snap)

set -euo pipefail

DEST="${1:?usage: stage.sh DESTDIR deb|rpm|arch|snap}"
KIND="${2:?usage: stage.sh DESTDIR deb|rpm|arch|snap}"
case "$KIND" in deb|rpm|arch|snap) ;; *) echo "Unknown package kind: $KIND" >&2; exit 2 ;; esac
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
NAME=screencap-documentation-tool
APPID=io.github.ILikeHostingServices.ScreencapDocumentationTool
SHARE="$DEST/usr/share/$NAME"

install -d "$SHARE/assets" "$DEST/usr/bin" "$DEST/usr/share/applications" \
           "$DEST/usr/share/metainfo" "$DEST/usr/share/icons/hicolor/256x256/apps" \
           "$DEST/usr/share/licenses/$NAME" "$DEST/usr/share/doc/$NAME"

# The program: every Python module at the top level of the repository
for f in "$ROOT"/*.py "$ROOT"/screencap_gui.pyw; do
    install -m 644 "$f" "$SHARE/"
done
install -m 755 "$ROOT/screencap.py" "$SHARE/screencap.py"
install -m 755 "$ROOT/screencap_gui.pyw" "$SHARE/screencap_gui.pyw"
install -m 644 "$ROOT/assets/icon.png" "$SHARE/assets/icon.png"
install -m 644 "$ROOT/LICENSE" "$SHARE/LICENSE"
printf '%s\n' "$KIND" > "$SHARE/package-kind"
chmod 644 "$SHARE/package-kind"

# Launchers. The system Python, where the package dependencies put Tkinter,
# with -B so no cache files are written into the package folder
# (not whatever python3 comes first on PATH); the snap brings its own
# shellcheck disable=SC2016  # $SNAP must expand when the launcher runs, not now
if [ "$KIND" = snap ]; then PY='"$SNAP/usr/bin/python3"'; PREFIX='$SNAP'; else PY=/usr/bin/python3; PREFIX=''; fi
for pair in "screencap:screencap.py" "screencap-gui:screencap_gui.pyw"; do
    cmd="${pair%%:*}"; script="${pair#*:}"
    cat > "$DEST/usr/bin/$cmd" <<LAUNCHER
#!/bin/sh
# $cmd: start the Screencap Documentation Tool (installed by the $KIND package)
exec $PY -B "$PREFIX/usr/share/$NAME/$script" "\$@"
LAUNCHER
    chmod 755 "$DEST/usr/bin/$cmd"
done

install -m 644 "$ROOT/packaging/linux/$APPID.desktop" "$DEST/usr/share/applications/$APPID.desktop"
install -m 644 "$ROOT/packaging/linux/$APPID.metainfo.xml" "$DEST/usr/share/metainfo/$APPID.metainfo.xml"
install -m 644 "$ROOT/assets/icon.png" "$DEST/usr/share/icons/hicolor/256x256/apps/$APPID.png"
install -m 644 "$ROOT/LICENSE" "$DEST/usr/share/licenses/$NAME/LICENSE"
install -m 644 "$ROOT/LICENSE" "$DEST/usr/share/doc/$NAME/copyright"
install -m 644 "$ROOT/README.md" "$DEST/usr/share/doc/$NAME/README.md"
