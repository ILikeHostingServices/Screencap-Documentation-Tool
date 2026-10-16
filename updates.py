#!/usr/bin/env python3
#
# updates.py
# 2026-10-16
# Version: v1.4.1
#
# PURPOSE:
# Project links (repository, issues, releases, documentation) and the update
# check. The check asks GitHub for the newest release of this project and
# compares its version with the one running. It only runs when the user asks
# (Help > Check for Updates) or has turned on automatic checks, and it sends
# nothing about the PC or its files: it is a plain request for the public
# release list, like opening the Releases page in a browser.
#
# A copy installed with the Windows installer can also update itself:
# Update Now downloads the new installer from this project's GitHub release,
# checks it against the release's SHA256SUMS.txt (a damaged or altered file
# is refused and never run), and starts it silently for the same scope (just
# me or everyone). The installer replaces this copy in place, keeping the
# settings and folders, and opens the app again.
#
# Administrators can switch update checks off for everyone by setting the
# environment variable SCREENCAP_NO_UPDATE_CHECK=1 (for example with Group
# Policy or an Intune configuration profile).

import hashlib
import json
import os
import re
import subprocess
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

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
# Update Now only downloads from this project's own release files
DOWNLOAD_PREFIX = f"{RELEASES_URL}/download/"
CHECKSUMS_NAME = "SHA256SUMS.txt"
MAX_DOWNLOAD = 500 * 1024 * 1024    # far bigger than any real installer
UPDATE_DIR = Path(tempfile.gettempdir()) / "ScreencapUpdate"
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
            data = json.loads(response.read().decode("utf-8-sig"))
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


def windows_arch():
    """'arm64' on Windows on ARM (also when this copy is the x64 build running
    under emulation), else 'x64'."""
    if os.name != "nt":
        return "x64"
    try:
        import ctypes
        from ctypes import wintypes
        kernel32 = ctypes.windll.kernel32
        process, native = wintypes.USHORT(), wintypes.USHORT()
        if kernel32.IsWow64Process2(kernel32.GetCurrentProcess(), ctypes.byref(process),
                                    ctypes.byref(native)):
            return "arm64" if native.value == 0xAA64 else "x64"   # IMAGE_FILE_MACHINE_ARM64
    except (AttributeError, OSError):
        pass                       # Windows 10 before 1709 has no IsWow64Process2
    return "arm64" if "ARM64" in (os.environ.get("PROCESSOR_ARCHITECTURE", "") +
                                  os.environ.get("PROCESSOR_ARCHITEW6432", "")).upper() else "x64"


def download_for(latest, kind=None, arch=None):
    """The best download link for this kind of install (and, on Windows, for
    this PC's processor: the ARM64 build on Windows on ARM when the release
    has one, otherwise the x64 build, which ARM PCs run under emulation)."""
    kind = kind or install_kind()
    windows = {"installer": "-windows-{}-setup.exe", "portable": "-windows-{}-portable.zip"}
    if kind in windows:
        arch = arch or windows_arch()
        suffixes = [windows[kind].format(a) for a in dict.fromkeys((arch, "x64"))]
    else:
        suffixes = [{"deb": "_all.deb", "rpm": ".noarch.rpm",
                     "arch": "-any.pkg.tar.zst"}.get(kind)]
    for suffix in suffixes:
        if not suffix:
            continue
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


# ---------------------------------------------------------------------------
# Update Now (Windows installer copies)
# ---------------------------------------------------------------------------

class UpdateCancelled(UpdateError):
    """The user cancelled the download."""


def can_install(kind=None):
    """True when Update Now can download and run the installer itself: a
    copy installed with the Windows installer, and not switched off by the
    administrator."""
    return os.name == "nt" and (kind or install_kind()) == "installer" and \
        not disabled_by_policy()


def installer_asset(latest, arch=None):
    """(file name, link) of the setup program for this PC, or None."""
    arch = arch or windows_arch()
    for a in dict.fromkeys((arch, "x64")):
        for name, link in latest["assets"].items():
            if name.endswith(f"-windows-{a}-setup.exe") and link:
                return name, link
    return None


def read_checksums(text):
    """{file name: sha256} from a sha256sum-style list ("<hash>  <name>",
    or "<hash> *<name>")."""
    sums = {}
    for line in (text or "").splitlines():
        m = re.match(r"^([0-9a-fA-F]{64})\s+\*?(.+?)\s*$", line)
        if m:
            sums[m.group(2)] = m.group(1).lower()
    return sums


def _open(url, timeout, allowed):
    if not url.startswith(allowed):
        raise UpdateError(f"Refusing to download from an unexpected address: {url}")
    request = urllib.request.Request(url, headers={
        "User-Agent": f"ScreencapDocumentationTool/{version.RELEASE}"})
    try:
        return urllib.request.urlopen(request, timeout=timeout)  # noqa: S310
    except urllib.error.HTTPError as exc:
        raise UpdateError(f"The download failed: GitHub answered {exc.code} "
                          f"{exc.reason}.") from exc
    except (urllib.error.URLError, OSError) as exc:
        reason = getattr(exc, "reason", exc)
        raise UpdateError(f"The download failed ({reason}). Check the internet "
                          "connection or proxy.") from exc


def download_installer(latest, progress=None, cancel=None, dest_dir=None, arch=None,
                       allowed=DOWNLOAD_PREFIX, timeout=60):
    """Download the new setup program and check it against the release's
    SHA256SUMS.txt. Returns its path. progress(done_bytes, total_bytes) is
    called as it downloads; cancel is a threading.Event. Raises UpdateError
    (UpdateCancelled when cancelled) and never leaves a partial or
    unverified installer behind."""
    asset = installer_asset(latest, arch)
    if not asset:
        raise UpdateError("This release has no Windows installer.")
    name, link = asset
    if Path(name).name != name or "\\" in name:
        raise UpdateError(f"Refusing an installer with an unexpected file name: {name!r}")
    sums_link = latest["assets"].get(CHECKSUMS_NAME)
    if not sums_link:
        raise UpdateError("This release has no checksum list, so the download "
                          "could not be checked.")
    with _open(sums_link, timeout, allowed) as response:
        expected = read_checksums(response.read(1024 * 1024).decode("utf-8", "replace")).get(name)
    if not expected:
        raise UpdateError(f"{name} is not in the release's checksum list, so it "
                          "could not be checked.")
    dest_dir = Path(dest_dir or UPDATE_DIR)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / name
    part = dest.with_name(name + ".part")
    digest, done = hashlib.sha256(), 0
    try:
        with _open(link, timeout, allowed) as response, open(part, "wb") as out:
            total = int(response.headers.get("Content-Length") or 0)
            while True:
                if cancel is not None and cancel.is_set():
                    raise UpdateCancelled("The download was cancelled.")
                chunk = response.read(256 * 1024)
                if not chunk:
                    break
                done += len(chunk)
                if done > MAX_DOWNLOAD:
                    raise UpdateError("The download is far bigger than expected and was stopped.")
                digest.update(chunk)
                out.write(chunk)
                if progress is not None:
                    progress(done, total)
        if digest.hexdigest() != expected:
            raise UpdateError("The downloaded installer does not match the release's "
                              "checksum, so it was deleted and not run. Try again later, "
                              "or download it from the Releases page.")
        os.replace(part, dest)
    except (OSError, urllib.error.URLError) as exc:
        if isinstance(exc, UpdateError):
            raise
        raise UpdateError(f"The download failed: {exc}") from exc
    finally:
        try:
            part.unlink()
        except OSError:
            pass
    return dest


def install_scope(app_dir=None):
    """'ALLUSERS' when this copy is in Program Files (installed for
    everyone), else 'CURRENTUSER' (installed for one user)."""
    app = os.path.normcase(os.path.abspath(str(app_dir or apppaths.APP_DIR)))
    for var in ("ProgramW6432", "ProgramFiles", "ProgramFiles(x86)"):
        base = os.environ.get(var)
        if base and app.startswith(os.path.normcase(os.path.abspath(base)).rstrip("\\/") + os.sep):
            return "ALLUSERS"
    return "CURRENTUSER"


def installer_args(scope, log, relaunch=True):
    """Command line for a silent update. The installer keeps the folders
    and options chosen last time; /RELAUNCH=1 opens the app again after."""
    args = ["/SILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/CLOSEAPPLICATIONS",
            f"/{scope}", f"/LOG={log}"]
    if relaunch:
        args.append("/RELAUNCH=1")
    return args


def start_installer(setup, app_dir=None, relaunch=True):
    """Start the downloaded installer for this copy's scope and return its
    log file. Windows asks for administrator permission when the copy is
    installed for everyone. The app should close right after, so its files
    can be replaced."""
    if os.name != "nt":
        raise UpdateError("Installing updates is only possible on Windows.")
    setup = Path(setup)
    log = setup.with_suffix(".log")
    try:
        log.unlink()      # a fresh log for this update, not one from an earlier try
    except OSError:
        pass
    args = subprocess.list2cmdline(installer_args(install_scope(app_dir), log, relaunch))
    try:
        # ShellExecute, so Windows can show the administrator prompt
        os.startfile(str(setup), "open", args)
    except OSError as exc:
        raise UpdateError(f"The installer could not be started: {exc}") from exc
    return log


def clean_downloads(folder=None):
    """Remove installers left from an earlier update (best effort; one that
    is still running is removed next time). The installers' logs are kept
    for troubleshooting; each update overwrites its own."""
    folder = Path(folder or UPDATE_DIR)
    if folder.is_dir():
        for f in folder.iterdir():
            if f.suffix.lower() in (".exe", ".part"):
                try:
                    f.unlink()
                except OSError:
                    pass


PACKAGE_NAME = "screencap-documentation-tool"


def update_command(kind=None, new_version="X.Y.Z"):
    """The command that updates this kind of install, for copying, or None."""
    kind = kind or install_kind()
    return {
        "deb": f"sudo apt install ./{PACKAGE_NAME}_{new_version}-1_all.deb",
        "rpm": f"sudo dnf install ./{PACKAGE_NAME}-{new_version}-1.noarch.rpm",
        "arch": f"yay -Syu {PACKAGE_NAME}",
        "snap": f"sudo snap refresh {PACKAGE_NAME}",
        "brew": f"brew update && brew upgrade {PACKAGE_NAME}",
        "installer": f"winget upgrade --id {WINGET_ID} -e",
    }.get(kind)
