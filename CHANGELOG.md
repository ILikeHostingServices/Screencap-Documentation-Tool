CHANGELOG.md v1.4.1 (Last Rev: 2026-10-01)

# Changelog

Every release of the Screencap Documentation Tool, newest first. Each version is a git tag (Major.Minor.Patch), and the same notes appear on the GitHub Releases page.

## v1.4.0 - Automatic per-user or system-wide install on Windows (2026-10-01)

**New**
- The Windows install command now chooses the scope for you:
  - Normal PowerShell window: installs for the current user only, as before. No admin needed.
  - Administrator PowerShell window: installs for everyone on the PC. Python and FFmpeg are installed system-wide, shortcuts go on the All Users Start Menu and Public Desktop, and all users can save into the default `source` and `output` folders.
- `-SystemWide` and `-UserOnly` switches override the automatic choice.
- `Install-Prerequisites.ps1` gains `-Scope user|machine`. In machine mode, copies installed only in one user's profile are not counted, because other accounts cannot use them.
- Upgrading a PC from per-user to system-wide removes your old per-user shortcuts so the app does not appear twice.
- GitHub releases are now published automatically for every version tag, and `CHANGELOG.md` lists every release.

**Documentation**
- README covers the single command, both explicit variants, switching a PC to system-wide, and uninstalling either kind of install.

## v1.3.0 - Custom application icon (2026-10-01)

**New**
- Custom icon (a monitor with amber capture brackets) for the window title bar, taskbar, Alt+Tab, Start Menu and Desktop shortcuts, and the Linux menu entry.
- On Windows the GUI has its own taskbar identity, so it shows its icon instead of grouping under the generic Python icon.
- Windows shortcuts now launch through the Python launcher (`pyw.exe`), so they can be pinned to the taskbar and keep working after Python upgrades.
- `assets/make_icon.py` rebuilds the icon from code if you want to tweak it (needs Pillow, which the tool itself does not).

**Upgrade note**
- Paste the Quick Start command again to get the new shortcuts. If you pinned the old version, unpin it and pin again from the Start Menu.

## v1.2.1 - Installer fixes and copy-and-paste Quick Start (2026-10-01)

Install everything (prerequisites and the tool) with a single copy-and-paste command. Running the same command again updates the tool and never deletes your recordings or screenshots.

**Installers**
- Windows (`install.ps1`): installs to `C:\DATA\Tools\Screencap-Documentation-Tool`, installs Python 3 and FFmpeg with winget, and adds Start Menu and Desktop shortcuts. No admin rights needed, and it works even when PowerShell's default policy blocks script files. Supports `-InstallDir`, `-NoShortcuts`, and `-SkipPrerequisites`.
- Linux (`install.sh`, run with sudo): installs FFmpeg, Python, and Tkinter with apt, dnf, or pacman, installs to `/opt/Screencap-Documentation-Tool`, and adds `screencap` and `screencap-gui` commands plus a menu entry. `source` and `output` belong to your user, so no sudo is needed afterwards.
- macOS (`install.sh`, no sudo): installs Homebrew if needed, plus FFmpeg, Python, and the matching Tkinter, installs to `~/Applications/Screencap-Documentation-Tool`, and adds `screencap` and `screencap-gui` commands and a double-clickable `Screencap GUI.command`.

**Fixed (since v1.2.0)**
- The Linux installer now picks a Python that has Tkinter, so the GUI starts.
- The Linux installer no longer reinstalls curl.

**Documentation**
- Quick Start commands for each OS, a "review the installer first" option, and update and uninstall steps.

## v1.2.0 - First one-step installers (2026-10-01)

First version of the copy-and-paste installers. Use v1.2.1 instead: in this version the Linux installer could pick a Python without Tkinter, so the GUI might not start, and it also reinstalled curl unnecessarily.

**New**
- `install.ps1` for Windows: downloads the tool, installs Python and FFmpeg with winget, and creates shortcuts.
- `install.sh` for Linux (`/opt`) and macOS (`~/Applications`).

## v1.1.1 - README reorganized for easier reading (2026-10-01)

**Documentation**
- The README now leads with what you get, then quick start, then reference material.
- GUI walkthrough in the order the window is laid out.
- Tuning advice shows the GUI setting and the command line switch side by side.
- Troubleshooting is grouped into setup, GUI, and processing problems.

No code changes.

## v1.1.0 - Desktop GUI (2026-10-01)

**New**
- `screencap_gui.pyw` desktop GUI, launched with `Run-Screencap-GUI.bat` on Windows. Uses Tkinter, which ships with Python, so there is nothing extra to install.
- Pick source and output folders, see every recording with its status and step count, and process all or selected recordings with a live progress bar and Cancel.
- Sensitivity presets (High, Normal, Low) and every command line setting, with input validation and Reset Defaults.
- Preview tab to page through captured steps, open images full size, and open `steps.md`.
- Log tab with errors highlighted.
- Settings are remembered per user (in `%APPDATA%\ScreencapDocTool` on Windows), outside the repository.

**Changed**
- `screencap.py` v1.1.0: no console windows flash up when FFmpeg runs from the GUI on Windows. Command line behavior is unchanged.

## v1.0.0 - Initial release: automatic step screenshots from screen recordings (2026-10-01)

Drop screen recordings in a folder and get a screenshot of every step, plus a ready-to-write Markdown index.

**What's included**
- `screencap.py` command line tool (Python 3.8+ standard library and FFmpeg only).
- Finds `.mp4`, `.mov`, and `.mkv` recordings in the `source` folder (optionally including subfolders).
- FFmpeg scene detection tuned for screen recordings. Bursts of changes such as typing or window animations are merged into one step.
- Each screenshot shows the finished state of a step, captured just before the next change (`--capture-point start` captures right after each change instead).
- Full resolution PNG or JPG screenshots, plus `steps.md` and `steps.json` per recording.
- Skips recordings that are already processed (`--force` to redo), `--dry-run` for tuning, and a log in `output/screencap.log`.
- Windows 11 launcher (`Run-Screencap.bat`) and prerequisite installer (`Install-Prerequisites.ps1`, uses winget).
- `.gitignore` keeps recordings, screenshots, and logs, which may contain sensitive data, out of the repository.
