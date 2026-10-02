#!/usr/bin/env python3
#
# version.py
# 2026-10-02
# Version: v1.0.0
#
# PURPOSE:
# The release version of the Screencap Documentation Tool as a whole. It
# matches the git tag and the GitHub release, and is shown in the GUI title
# bar and footer and by screencap.py --version. Each script also keeps its
# own version in its header, which only changes when that file changes.
#
# Bump RELEASE and RELEASE_DATE in the same commit that a release tag will
# point at (see "Releases And Versions" in README.md).

RELEASE = "1.12.1"
RELEASE_DATE = "2026-10-02"
APP_NAME = "Screencap Documentation Tool"
