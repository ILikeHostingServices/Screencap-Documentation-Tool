CHANGELOG.md v1.14.0 (Last Rev: 2026-10-02)

# Changelog

Every release of the Screencap Documentation Tool, newest first. Each version is a git tag (Major.Minor.Patch), and the same notes appear on the GitHub Releases page.

## v1.13.0 - Automated testing on real Windows, Linux, and macOS (2026-10-02)

**New**
- Every push and pull request runs the full test suite on real Windows 11-class (windows-latest) and Linux machines through GitHub Actions: screenshot detection, duplicate removal, highlight boxes, cropping, blurring with Tesseract, HTML/Word/PDF export, presets, launching VLC, and the GUI itself (processing a recording, step navigation with the arrow keys, reordering, saving captions). A run fails if any test was skipped, so a missing tool cannot hide a problem.
- The one-step installers are tested on clean machines whenever an installer changes, every Monday, and on demand (**Actions > Installers > Run workflow**): Windows both per-user and system-wide, Linux, and macOS. Each run checks the installed files and version, the Start Menu shortcut's icon and taskbar identity, that the Users group can write to a system-wide install, that the installed tool processes and exports a recording, and that re-running the installer (an update) keeps your recordings and output.
- Both workflows use a read-only token and no secrets. GitHub Actions is free for public repositories.
- README has a new **Automated Testing** section, and roadmap item #11 is done.

**Fixed**
- GUI: **Process All** and **Process Selected** did nothing except say "The source folder changed. Click Refresh" when the source folder was typed as a Windows short name (such as `C:\Users\RUNNER~1\...`), through a junction, or through a symbolic link. Found by the first Windows test run.
- PDF export works when the tool runs as root or in a locked-down Linux container (set `SCREENCAP_NO_SANDBOX=1` if Chrome refuses to start).

## v1.12.1 - Clearer step navigation and the release version in the footer (2026-10-02)

**Fixed**
- Steps tab: the arrow keys now always continue from the step being shown. Before, after using a button or **< Prev / Next >**, pressing Up or Down in the step list could jump to a different step than expected.
- **Up** and **Down** page through the steps from anywhere in the Steps tab (for example after clicking a button or the picture), not only when the step list has focus. They still behave normally while typing a caption or title.
- The reorder buttons are now named **Move Step Up** and **Move Step Down**, and the status bar says where the step moved. The moved step stays selected, which is why the picture does not change when reordering. **Ctrl+Up** and **Ctrl+Down** in the step list also reorder.

**Changed**
- The window title and footer show the release version (this release: v1.12.1) instead of the GUI file's own version. `screencap.py --version` shows it too, and the Log tab lists each component's version at startup.
- The release workflow can no longer delete tags or releases. That ability was only needed for the one-time renumbering in v1.4.0; it now only creates tags and releases.

## v1.12.0 - Saved presets (2026-10-02)

**New**
- **Preset** dropdown above Detection Settings fills in every setting at once for the kind of recording:
  - **Installer wizard:** the recommended defaults.
  - **Web console:** ignores spinners and slow-loading pages.
  - **Terminal / command line:** catches small text changes and merges bursts of typing.
  - **Fast clicking:** for recordings with short pauses between actions.
- **Save As...** saves the current settings, including **Also blur** patterns, as your own preset. **Delete** removes one. Built-in presets cannot be overwritten or deleted.
- Saved presets live in your profile (`presets.json` next to the GUI settings) and are shared with the command line.
- Command line: `--preset NAME` (not case-sensitive; options you add override the preset) and `--list-presets`.
- The last preset you used is remembered.

## v1.11.0 - Play a step in VLC (2026-10-02)

**New**
- **Play in VLC** in the Steps tab opens the original recording in VLC media player 3 seconds before the selected step's screen appeared, so you can watch the click or keystroke that led to it.
- VLC is found on the PATH or in its standard install folders (Windows `Program Files\VideoLAN\VLC`, macOS `/Applications/VLC.app`).
- Each new VLC window starts at the right moment even if VLC is set to allow only one instance.
- Processed recordings now remember where the source video is, so this keeps working when the recording is not selected in the Videos list.

## v1.10.0 - Export to HTML, Word, and PDF (2026-10-02)

**New**
- One-click export from the Steps tab to a finished document in the recording's `export/` folder:
  - **HTML:** a single self-contained file with the screenshots embedded, easy to email or put on a file share.
  - **Word (.docx):** made with Pandoc, with proper Title, Subtitle, Author, and Date styles.
  - **PDF:** printed by Microsoft Edge (included with Windows 11), Google Chrome, or Chromium, with no window shown.
- Every export starts with a header block: title, version, date (YYYY-MM-DD), and author. Set these in the Steps tab; the title defaults to the recording's name and the version to `v1.0.0`.
- Captions appear under each screenshot.
- Exports use the blurred screenshots. **Unblurred copy** exports the unblurred set after a confirmation, with `-UNREDACTED` in the file name and a warning inside.
- Command line: `--export html,docx,pdf` (also re-exports recordings that were already processed), `--doc-author`, `--doc-version`, `--pandoc`, `--browser`.
- The installers now install Pandoc as an optional component (Windows: `JohnMacFarlane.Pandoc`). HTML and PDF export do not need it.

## v1.9.0 - Automatic blurring of sensitive information (2026-10-02)

**New**
- Passwords, license and product keys, API tokens, GUIDs, IP, MAC and email addresses, masked passwords, and anything after labels such as `Password:` or `Token:` are found with Tesseract OCR and blurred automatically.
- **Two copies:** `steps.md` uses the blurred screenshots, and a complete unblurred set is kept in `unredacted/` with its own `steps-unredacted.md` (marked "do not publish"), in case a blurred detail is needed.
- **Toggles:** blurring can be switched on or off for a whole recording (**Blur sensitive info**) or a single step (**Blur this step**).
- **Fix mistakes by hand:** **Add Blur Box** blurs anything else, **Un-blur / Re-blur** switches off a false positive with a click, and **Re-scan All Steps for Sensitive Text** runs detection again. The Original frame view outlines every blur box.
- **Your own patterns:** **Also blur** in the GUI or `--redact-pattern` on the command line, for example an internal domain name.
- Blurred areas are pixelated and then blurred, so the text cannot be read back. The originals are never changed.
- Command line: `--no-redact`, `--redact-pattern`, `--tesseract`.
- The installers now install Tesseract OCR as an optional component (Windows: `UB-Mannheim.TesseractOCR`, which asks for administrator permission). Without it, everything else works and hand-drawn blur boxes still apply.

**Note**
- Automatic detection is a safety net, not a guarantee. Review screenshots before publishing them.

## v1.8.0 - Adjustable cropping (2026-10-02)

**New**
- Crop screenshots by dragging a rectangle on the picture in the Steps tab: **Crop: All Steps** for the whole recording, or **This Step** for one step. Press Esc to cancel.
- **No Crop Here** leaves one step uncropped, and **Clear All Crops** removes every crop.
- On **Original frame**, dashed outlines show the crop (blue) and the "what changed" box (red) that will be applied.
- Command line: `--crop X:Y:W:H`, for example `--crop 0:0:1920:1080` to keep the left monitor of a dual-screen recording.
- The originals are never cropped, so a crop can be adjusted or removed at any time and nothing is lost.
- Crop sizes are rounded down to even numbers and kept inside the frame, so every image format can save them.

## v1.7.0 - Red box around what changed (2026-10-02)

**New**
- Each screenshot gets a red box around the area that changed since the previous step, so readers can see where to click or what appeared.
- The box hugs the change: in testing it fit a 14 pixel checkbox with a 28 pixel box. Whole-screen changes (a new window) get no box, and small far-away changes such as a moving mouse cursor are left out.
- Steps tab: **Highlight changes** turns the box on or off for the whole recording, and **Highlight this step** overrides it for one step. The preview updates immediately.
- GUI: **Highlight what changed in each step** in Detection Settings. Command line: `--no-highlight`.
- The box is drawn only on the rendered screenshot. The original frame in `originals/` is never changed, so the box can be turned off again at any time.
- Output from earlier versions gets its change areas worked out the first time it is saved in the editor.

## v1.6.0 - Duplicate screenshot removal (2026-10-02)

**New**
- Screenshots that look virtually identical to one already kept, for example when you go back to a screen you already captured, are removed automatically.
- Removed duplicates are not deleted: they are kept as deleted steps with their original frames, and **Restore Deleted** in the Steps tab brings them back. The Steps tab shows how many were removed as duplicates.
- GUI: **Remove duplicate screenshots** checkbox and **Duplicate if differs by (%)** in Detection Settings.
- Command line: `--no-dedup` and `--dedup-threshold` (default 0.01 percent).
- The default only matches near-exact copies. In testing, a moving mouse cursor counted as no change while a ticked 14 pixel checkbox did not count as a duplicate, so small but real changes are kept.
- The final screenshot of a recording is always kept, so the end result is always documented.

## v1.5.0 - Step editor (2026-10-02)

**New**
- **Steps tab (step editor)** replaces the Preview tab. For the selected recording you can delete steps, restore deleted steps, move steps up or down, and write a caption for each step. Click **Save Changes** to re-render the screenshots and regenerate `steps.md`.
- Every captured frame is now kept untouched in `originals/`, and the screenshots in `steps.md` are rendered from those originals. Edits never destroy anything, and later features (crop, highlight, redaction) build on this.
- Captions replace the `_Notes:_` placeholder in `steps.md`.
- Unsaved edits are protected: the GUI asks before switching recordings, processing, or closing.
- `ROADMAP.md` records the ideas on hold for discussion: narration to captions, watch folder, Windows test automation, and a single-file Windows app.
- Automated tests in `tests/` (run with `python -m unittest discover -s tests -v`).

**Changed**
- Reprocessing with `--force` (or "Reprocess videos that are already done") now moves the previous results, including captions, into a `previous-<date>-<time>` folder instead of deleting them.
- If `steps.md` was edited by hand, saving from the editor keeps the hand-edited copy as `steps.hand-edited-<date>-<time>.md`.
- Output from v1.4.0 and earlier is upgraded automatically when opened. The old `steps.md` is kept as a backup.

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
