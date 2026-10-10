#!/usr/bin/env python3
#
# updates.py
# 2026-10-10
# Version: v1.2.2
#
# PURPOSE:
# Project links (repository, issues, releases, documentation) and the update
# check. The check asks GitHub for the newest release of this project and
# compares its version with the one running. It only runs when the user asks
# (Help > Check for Updates) or has turned on automatic checks, and it sends
# nothing about the PC or its files: it is a plain request for the public
# release list, like opening the Releases page in a browser.
#
# Administrators can switch update checks off for everyone by setting the
# environment variable SCREENCAP_NO_UPDATE_CHECK=1 (for example with Group
# Policy or an Intune configuration profile).

import json
import os
import re
import urllib.error
import urllib.request

import apppaths
import version

REPO = "ILikeHostingServices/Screencap-Documentation-Tool"
REPO_URL = f"https://github.com/{REPO}"
ISSUES_URL = f"{REPO_URL}/issues"
NEW_ISSUE_URL = f"{REPO_URL}/issues/new/choose"
BUG_REPORT_URL = f"{REPO_URL}/issues/new?template=bug_report.yml"
IDEA_URL = f"{REPO_URL}/issues/new?template=feature_request.yml"
RELEASES_URL = f"{REPO_URL}/releases"
LATEST_URL = f"{RELEASES_URL}/latest"
DOCS_URL = f"{REPO_URL}#readme"
SECURITY_URL = f"{REPO_URL}/security/policy"
LATEST_API = f"https://api.github.com/repos/{REPO}/releases/latest"
WINGET_ID = "ILHS.ScreencapDocumentationTool"
TIMEOUT = 10
VERSION_RE = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)$")


class UpdateError(Exception):
    """The update check could not reach GitHub or understand its answer."""


def disabled_by_policy():
    return os.environ.get("SCREENCAP_NO_UPDATE_CHECK", "").strip().lower() in ("1", "true", "yes")


def parse_version(text):
    """'v1.2.3' or '1.2.3' -> (1, 2, 3); anything else -> None."""
    m = VERSION_RE.match((text or "").strip())
    return tuple(int(part) for part in m.groups()) if m else None


def is_newer(latest, current=version.RELEASE):
    a, b = parse_version(latest), parse_version(current)
    return bool(a and b and a > b)


def install_kind():
    """How this copy was installed, which decides how to update it:
    'installer' (Windows setup), 'portable' (Windows zip), 'deb', 'rpm',
    'arch', 'snap' (Linux packages), 'brew' (Homebrew), or 'python'."""
    if apppaths.PACKAGE_KIND:
        return apppaths.PACKAGE_KIND
    if not apppaths.FROZEN:
        return "python"
    return "installer" if (apppaths.APP_DIR / "unins000.exe").is_file() else "portable"


INSTALL_KIND_NAMES = {
    "installer": "Windows installer", "portable": "Windows portable (zip)",
    "deb": "Debian/Ubuntu package (.deb)", "rpm": "Fedora/RHEL/openSUSE package (.rpm)",
    "arch": "Arch Linux package", "snap": "Snap", "brew": "Homebrew",
    "python": "Python source",
}


def install_kind_name(kind=None):
    """install_kind() in words, for the About window."""
    kind = kind or install_kind()
    return INSTALL_KIND_NAMES.get(kind, kind)


def check_latest(url=LATEST_API, timeout=TIMEOUT):
    """The newest published release: dict with version, tag, name, url,
    published (YYYY-MM-DD), notes, and assets {file name: download URL}."""
    request = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": f"ScreencapDocumentationTool/{version.RELEASE}",
    })
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise UpdateError(f"GitHub answered {exc.code} {exc.reason}.") from exc
    except (urllib.error.URLError, OSError) as exc:
        reason = getattr(exc, "reason", exc)
        raise UpdateError(f"Could not reach GitHub ({reason}). Check the internet "
                          "connection or proxy, or open the Releases page in a browser.") from exc
    except ValueError as exc:
        raise UpdateError("GitHub sent an answer that could not be read.") from exc
    tag = str(data.get("tag_name") or "")
    parsed = parse_version(tag)
    if not parsed:
        raise UpdateError(f"The newest release has an unexpected version: {tag!r}.")
    return {
        "version": ".".join(map(str, parsed)),
        "tag": tag,
        "name": data.get("name") or tag,
        "url": data.get("html_url") or LATEST_URL,
        "published": str(data.get("published_at") or "")[:10],
        "notes": data.get("body") or "",
        "assets": {a.get("name"): a.get("browser_download_url")
                   for a in data.get("assets") or [] if a.get("name")},
    }


def download_for(latest, kind=None):
    """The best download link for this kind of install."""
    kind = kind or install_kind()
    suffix = {"installer": "-windows-x64-setup.exe",
              "portable": "-windows-x64-portable.zip",
              "deb": "_all.deb", "rpm": ".noarch.rpm",
              "arch": "-any.pkg.tar.zst"}.get(kind)
    if suffix:
        for name, link in latest["assets"].items():
            if name.endswith(suffix) and link:
                return link
    return latest["url"]


def how_to_update(kind=None):
    """One or two sentences on updating this kind of install."""
    kind = kind or install_kind()
    if kind == "installer":
        return ("Download and run the new installer; it updates this copy in place and "
                f"keeps your settings. With winget: winget upgrade {WINGET_ID}")
    if kind == "portable":
        return ("Download the new portable zip and replace this folder with it. Your "
                "settings and recordings are kept (they are not in the app folder).")
    if kind == "deb":
        return ("Download the new .deb and install it over this one: "
                "sudo apt install ./screencap-documentation-tool_X.Y.Z-1_all.deb")
    if kind == "rpm":
        return ("Download the new .rpm and install it over this one: "
                "sudo dnf install ./screencap-documentation-tool-X.Y.Z-1.noarch.rpm "
                "(openSUSE: sudo zypper install ...)")
    if kind == "arch":
        return ("Update from the AUR with your AUR helper (for example yay -Syu), or "
                "download the new package and run sudo pacman -U on it.")
    if kind == "snap":
        return "Snaps update by themselves; to update now: sudo snap refresh"
    if kind == "brew":
        return ("Update with Homebrew: brew update && brew upgrade "
                "screencap-documentation-tool")
    return ("Run the Quick Start install command from the README again; it updates this "
            "copy and keeps your settings.")


def release_notes_excerpt(notes, limit=900):
    """The release notes as plain text, shortened for a dialog."""
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", notes or "")
    text = re.sub(r"`([^`]*)`", r"\1", text).strip()
    return text if len(text) <= limit else text[:limit].rsplit("\n", 1)[0] + "\n..."
