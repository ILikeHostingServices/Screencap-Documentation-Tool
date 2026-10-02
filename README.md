README.md v1.10.0 (Last Rev: 2026-10-02)

# Screencap Documentation Tool

## Overview

Record your screen while you install or configure a program, drop the recording in a folder, and this tool pulls out a screenshot of every step for you. No more scrubbing through video to find the right frames.

For each recording you get:

- One full resolution screenshot per step, numbered in order.
- A `steps.md` file listing every step with its timestamp, its screenshot, and its caption, ready to turn into documentation.
- A red box around what changed since the previous step, so readers see where to click or what appeared.
- Duplicate screenshots (for example when you go back to a screen you already captured) are removed automatically, and can be restored.
- Adjustable cropping, for the whole recording or one step, by dragging a rectangle on the picture.
- A step editor in the GUI to remove, reorder, and caption steps. Every original frame is kept, so nothing you do in the editor is permanent.

You can run it from a desktop GUI or from the command line. Both use the same engine and produce the same output. It works with `.mp4`, `.mov`, and `.mkv` recordings and runs on Windows 11 (the primary target), Linux, and macOS. The only requirements are Python 3.8+ and [FFmpeg](https://ffmpeg.org/), both free and open source.

### How It Finds The Steps

Think of it like monitoring that alerts on state changes instead of polling on a timer: rather than grabbing a frame every N seconds, the tool only takes a screenshot when the screen actually changes state.

1. **Detect changes.** FFmpeg samples the video (5 frames per second at 640 px wide, which keeps it fast) and scores how different each frame is from the one before. A score above the sensitivity threshold counts as a change.
2. **Group bursts.** Changes that happen close together, like typing, a window animating open, or a fade, are merged into a single change. You get one screenshot per step, not twenty.
3. **Capture the step.** The stable stretch between two changes is one step. By default the screenshot is taken just before the next change starts, so each step is shown finished: fields filled in, progress bar complete, mouse on the button about to be clicked. Screenshots come from the original video at full resolution.
4. **Box what changed.** Each screenshot is compared with the previous step's, and a red box is drawn around the area that changed. A whole-screen change (a new window) gets no box, and small changes far from the main one, typically the mouse cursor, are left out.
5. **Drop duplicates.** Each screenshot is compared with the ones already kept. If it is virtually identical to one of them (you went back to a screen you already captured), it is set aside as a deleted step you can restore.

## Files

| Path | Purpose |
| --- | --- |
| `Run-Screencap-GUI.bat` | Double-click to start the GUI on Windows. |
| `Run-Screencap.bat` | Double-click to run the command line version on Windows. Passes any arguments through to `screencap.py`. |
| `install.ps1` | One-step Windows installer used by the Quick Start command. |
| `install.sh` | One-step Linux and macOS installer used by the Quick Start commands. |
| `Install-Prerequisites.ps1` | Installs Python 3 and FFmpeg with `winget` if they are missing, for the current user or (with `-Scope machine`) all users. Called by `install.ps1`. |
| `screencap_gui.pyw` | The GUI (Tkinter, included with Python). |
| `screencap.py` | The detection engine and command line tool. |
| `stepdoc.py` | The step document: loads and saves `steps.json`, renders screenshots from the originals, and writes `steps.md`. |
| `gui_editor.py` | The GUI's Steps tab (step editor). |
| `imaging.py` | Image comparisons (duplicate detection and the "what changed" box) using FFmpeg and the Python standard library. |
| `tests/` | Automated tests. Run `python -m unittest discover -s tests -v` from the repository root (needs FFmpeg). |
| `ROADMAP.md` | Ideas on hold until they have been discussed further. |
| `assets/` | Application icon (`icon.ico` for Windows, `icon.png` for Linux and macOS) and `make_icon.py`, which regenerates both from code (needs Pillow). |
| `CHANGELOG.md` | What changed in every release. |
| `.github/workflows/release.yml` | Creates version tags from `.github/releases/` and publishes a GitHub release for each one. |
| `source/` | Default folder for your recordings. |
| `output/` | Default folder for results, one subfolder per recording. |
| `tools/ffmpeg/bin/` | Optional spot for a portable `ffmpeg.exe` and `ffprobe.exe` (see [Portable FFmpeg](#portable-ffmpeg-no-admin-rights)). |

Each run creates these files in the output folder:

| Path | Purpose |
| --- | --- |
| `output/<video>/step_001_00-00-03.750.png` | Screenshot for each step, rendered from its original. The name holds the step number and timestamp. |
| `output/<video>/originals/` | The untouched full frames captured from the video. Never modified, so edits can always be redone. |
| `output/<video>/steps.md` | The steps in order, with screenshots, timestamps, and captions. Generated from `steps.json`. |
| `output/<video>/steps.json` | The step document: order, captions, deleted steps, and the settings used. This is the source of truth. |
| `output/<video>/steps.hand-edited-*.md` | Backup of `steps.md`, made automatically if you edited it by hand and then saved from the editor. |
| `output/<video>/previous-*/` | The previous results, moved here (not deleted) when a recording is reprocessed with `--force`. |
| `output/screencap.log` | Detailed log of every run. Check here first when something goes wrong. |

The GUI remembers your last folders and settings in `%APPDATA%\ScreencapDocTool\gui_settings.json` on Windows, or `~/.config/screencap-doc-tool/gui_settings.json` on Linux and macOS (outside the install folder). Delete that file to reset the GUI.

Switches worth knowing for diagnostics (the full list is in the [Command Line Reference](#command-line-reference)):

- `--dry-run` lists the steps that would be captured without saving anything.
- `-v` shows debug output on screen, including the exact FFmpeg commands.
- `--force` reprocesses recordings that already have output.

## Quick Start

Each command below is a single copy and paste. It installs the prerequisites, downloads the latest version of the tool from GitHub, and sets up launchers. Running the same command again later updates the tool and keeps your recordings and screenshots.

### Windows 11

One command works for both kinds of install. The installer checks whether PowerShell is running as Administrator and picks the scope for you:

```powershell
& ([scriptblock]::Create((irm https://raw.githubusercontent.com/ILikeHostingServices/Screencap-Documentation-Tool/HEAD/install.ps1)))
```

| Paste it into | You get |
| --- | --- |
| A normal PowerShell window | **Just you.** Python and FFmpeg are installed in your user profile, and the shortcuts go on your Start Menu and Desktop. No admin rights needed. Best for a single-user workstation. |
| An **Administrator** PowerShell window (right-click Start > **Terminal (Admin)**) | **Everyone on this PC.** Python and FFmpeg are installed system-wide, the shortcuts go on the All Users Start Menu and Public Desktop, and every user can save into the default `source` and `output` folders. Best for shared or lab PCs. |

The first line of the installer's output confirms which scope it chose. To choose explicitly instead, add a switch to the end of the command:

```powershell
# Just you, even from an Administrator window
& ([scriptblock]::Create((irm https://raw.githubusercontent.com/ILikeHostingServices/Screencap-Documentation-Tool/HEAD/install.ps1))) -UserOnly

# Everyone on this PC (must be an Administrator window)
& ([scriptblock]::Create((irm https://raw.githubusercontent.com/ILikeHostingServices/Screencap-Documentation-Tool/HEAD/install.ps1))) -SystemWide
```

Either way the tool goes in `C:\DATA\Tools\Screencap-Documentation-Tool`. To install somewhere else, add `-InstallDir 'D:\Tools\Screencap'` to the end of the command. Add `-NoShortcuts` to skip the shortcuts.

To pin the app to the taskbar, right-click its Start Menu entry and choose **Pin to taskbar** (or right-click the running app's taskbar button).

If the installer reports that a prerequisite was not detected yet, close PowerShell, open a new window, and paste the command again. Windows only picks up newly installed programs in new windows.

### Linux

Paste into a terminal (works on Debian/Ubuntu, Fedora, and Arch based distributions):

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/ILikeHostingServices/Screencap-Documentation-Tool/HEAD/install.sh)"
```

This installs FFmpeg, Python 3, and Tkinter with your package manager, installs the tool in `/opt/Screencap-Documentation-Tool`, and adds the `screencap-gui` and `screencap` commands plus an application menu entry. The program files are owned by root; the `source` and `output` folders belong to you, so you can use the tool without `sudo`.

### macOS

Paste into Terminal as your normal user (no `sudo`):

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/ILikeHostingServices/Screencap-Documentation-Tool/HEAD/install.sh)"
```

This installs [Homebrew](https://brew.sh) if you do not have it (it will ask for your password), installs FFmpeg, Python, and Tkinter with Homebrew, installs the tool in `~/Applications/Screencap-Documentation-Tool`, and adds the `screencap-gui` and `screencap` commands. In Finder you can also double-click `Screencap GUI.command` in that folder.

`~/Applications` is the standard macOS location for apps installed for just your user account, so no admin rights are needed after Homebrew is set up. To use a different folder on Linux or macOS, put `SCREENCAP_DIR=/your/path` in front of `bash`, for example `sudo SCREENCAP_DIR=/srv/screencap bash -c "..."`.

### First Run

1. Put your recordings in the `source` folder inside the install folder, or point the GUI at the folder your recorder already saves to.
2. Start the GUI (Start Menu shortcut on Windows, `screencap-gui` on Linux and macOS) and click **Process All**.
3. Clean up the steps in the **Steps** tab (delete extras, reorder, add captions) and click **Save Changes**, then click **steps.md** to open the document. VS Code, Obsidian, Typora, or any Markdown viewer shows the screenshots inline.

Prefer the command line? Run `screencap` on Linux and macOS, or `Run-Screencap.bat` in the install folder on Windows.

### Reviewing The Installer First

Piping a script from the internet straight into a shell means trusting it. To read it before running it, download it, review it, then run the local copy:

```powershell
irm https://raw.githubusercontent.com/ILikeHostingServices/Screencap-Documentation-Tool/HEAD/install.ps1 -OutFile install.ps1
notepad install.ps1
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

```bash
curl -fsSL -o install.sh https://raw.githubusercontent.com/ILikeHostingServices/Screencap-Documentation-Tool/HEAD/install.sh
less install.sh
sudo bash install.sh        # macOS: bash install.sh
```

## After Install Configuration

### Using The GUI

The window is laid out top to bottom in the order you use it:

1. **Folders.** Choose where recordings come from and where results go. **Browse...** changes a folder and **Open** shows it in Explorer. Tick **Include subfolders** to scan the source folder recursively.
2. **Videos.** Lists every recording found, with its status (New, Queued, Processing, Done, Failed, Cancelled) and step count. Click **Process All**, or Ctrl+click / Shift+click to pick several and click **Process Selected**. **Cancel** stops the run, and double-clicking a row opens its output folder.
3. **Detection Settings.** Pick a **Sensitivity** preset (High, Normal, Low) or type your own threshold. **Screenshot taken** chooses between the finished state of each step (default) and right after each change. **Remove duplicate screenshots** drops screenshots that look the same as an earlier one. **Highlight what changed in each step** draws the red box. Tick **Dry run** to count steps without saving anything. **Reset Defaults** restores the recommended values.
4. **Steps tab.** The step editor for the selected recording (see [Editing Steps](#editing-steps) below).
5. **Log tab.** Shows the run as it happens, with errors in red. The same log is saved to `output\screencap.log`.

Your folders and settings are saved when you process or close the window and restored the next time you open it.

### Editing Steps

Select a processed recording in the **Videos** list and the **Steps** tab shows its steps.

| Control | What it does |
| --- | --- |
| Step list | Every step with its time and caption. **< Prev** / **Next >** page through them. |
| **Move Up** / **Move Down** | Change the order of steps. |
| **Delete Step** (or the Delete key) | Remove a step. Its original frame is kept. |
| **Restore Deleted** | Put every deleted step back at its place in the video's timeline. |
| **Caption** | The text shown under the step in `steps.md`, replacing the `_Notes:_` placeholder. |
| **Highlight changes** (top right) | Turn the red "what changed" box on or off for the whole recording. |
| **Highlight this step** | Turn the box on or off for the selected step only. This overrides the recording-wide setting. |
| **Crop: All Steps / This Step** | Drag a rectangle on the picture around the area to keep. **All Steps** sets the crop for the whole recording; **This Step** gives the selected step its own crop. Press Esc to cancel. |
| **No Crop Here** | Leave the selected step uncropped even when the recording has a crop. |
| **Clear All Crops** | Remove the recording-wide crop and every per-step crop. |
| **Show: Screenshot / Original frame** | Preview the step as it will be saved, or the untouched frame from the video. |
| **Save Changes** | Re-render the screenshots from the originals and regenerate `steps.md` and `steps.json`. |
| **Discard Changes** | Go back to the last saved version. |

On **Original frame**, a dashed blue outline shows the crop and a dashed red outline shows the "what changed" box, so you can see what will be applied. Cropping only affects the rendered screenshots: the frames in `originals/` are never changed, so a crop can be adjusted or removed at any time.

Nothing is written until you click **Save Changes**. If you switch recordings, start processing, or close the window with unsaved changes, the GUI asks whether to save them first.

`steps.md` is generated from `steps.json`, so write captions in the editor rather than in `steps.md`. If you do edit `steps.md` by hand and then save from the editor, your edited copy is kept as `steps.hand-edited-<date>-<time>.md` next to it.

Output from v1.4.0 and earlier is upgraded automatically the first time you open it: the screenshots move into `originals/` and the old `steps.md` is kept as `steps.pre-upgrade-<date>-<time>.md`.

### Tuning For Your Recordings

The defaults are tuned for typical setup wizards. If a recording gives you too many or too few screenshots, do a dry run first so you can experiment without writing files (GUI: tick **Dry run**; command line: `--dry-run`), then adjust:

| Problem | GUI setting | Command line |
| --- | --- | --- |
| Too many near-duplicate screenshots (hover effects, small redraws) | Sensitivity **Low**, or raise **Merge changes within** to 2 | `--threshold 0.015` and/or `--debounce 2` |
| Missing steps (a checkbox or small text change not caught) | Sensitivity **High**, or set **Analyze width** to 0 | `--threshold 0.002` and/or `--analyze-width 0` |
| A screenshot you wanted was removed as a duplicate | Click **Restore Deleted** in the Steps tab, or lower **Duplicate if differs by (%)** (for example to 0.005), or untick **Remove duplicate screenshots** | `--dedup-threshold 0.005`, or `--no-dedup` |
| The red box is in the wrong place or not useful | Untick **Highlight this step** for that step in the Steps tab, or untick **Highlight what changed in each step** before processing | `--no-highlight` |
| Screenshots show a half-drawn window | **Screenshot taken**: Finished state, or raise **Settle after change** | `--capture-point end`, or raise `--settle` |

After changing settings, reprocess with **Reprocess videos that are already done** ticked (command line: `--force`).

### Recording Tips For Best Results

- Pause for about a second after each meaningful step. The tool looks for moments when the screen is still.
- Record a single window or monitor rather than a multi-monitor desktop. If you do record several monitors, crop to the one that matters with **Crop: All Steps** in the Steps tab, or `--crop` on the command line.
- Turn on Do Not Disturb so notification popups do not show up as extra steps.
- [OBS Studio](https://obsproject.com/) (free, open source) and the built-in Windows Snipping Tool recorder both work well. In OBS, record to `.mkv`, which survives a crash mid-recording, and remux to `.mp4` if needed.

### Keeping Sensitive Data Out Of Git

Setup recordings often capture passwords, license keys, API tokens, internal hostnames, and IP addresses. This repository is public, so `.gitignore` excludes everything in `source/` and `output/`, all video and image files, logs, and the `tools/` folder. Before you commit anything, run:

```powershell
git status --short
```

and confirm that no media, logs, or files containing secrets are listed. Also review, and blur or redact, screenshots before publishing documentation built from them.

### Updating And Uninstalling

**Update:** paste the same Quick Start command again. It downloads the latest version over the top of the old one. Nothing in `source` or `output` is deleted, and GUI settings are kept.

**Uninstall:** move any recordings or screenshots you want to keep out of the install folder first, because removing the folder deletes them.

```powershell
# Windows, just-you install
Remove-Item -Recurse -Force 'C:\DATA\Tools\Screencap-Documentation-Tool', "$env:APPDATA\ScreencapDocTool"
Remove-Item -Force "$([Environment]::GetFolderPath('Programs'))\Screencap Documentation Tool.lnk", "$([Environment]::GetFolderPath('Desktop'))\Screencap Documentation Tool.lnk"

# Windows, everyone install (Administrator window). Each user's GUI settings stay in their own %APPDATA%\ScreencapDocTool.
Remove-Item -Recurse -Force 'C:\DATA\Tools\Screencap-Documentation-Tool'
Remove-Item -Force "$([Environment]::GetFolderPath('CommonPrograms'))\Screencap Documentation Tool.lnk", "$([Environment]::GetFolderPath('CommonDesktopDirectory'))\Screencap Documentation Tool.lnk"
```

```bash
# Linux
sudo rm -rf /opt/Screencap-Documentation-Tool /usr/local/bin/screencap /usr/local/bin/screencap-gui /usr/share/applications/screencap-documentation-tool.desktop
rm -rf ~/.config/screencap-doc-tool

# macOS
rm -rf ~/Applications/Screencap-Documentation-Tool "$(brew --prefix)/bin/screencap" "$(brew --prefix)/bin/screencap-gui" ~/.config/screencap-doc-tool
```

Python and FFmpeg are left installed because other programs may use them. Remove them with `winget uninstall`, your Linux package manager, or `brew uninstall` if you no longer need them.

### Switching A Windows PC From Just You To Everyone

Paste the Quick Start command into an **Administrator** PowerShell window. It installs system-wide copies of Python and FFmpeg (copies that only exist in one user's profile do not count, because other accounts cannot use them), moves the shortcuts to the All Users locations, and opens up the `source` and `output` folders to all users. Your recordings and settings are kept.

The old per-user copies of Python and FFmpeg keep working but are no longer needed. To remove them, run this in a normal (not Administrator) window:

```powershell
winget uninstall --id Gyan.FFmpeg --scope user
winget uninstall --id Python.Python.3.12 --scope user
```

### Releases And Versions

Each release is an annotated git tag (`v1.4.0`, for example) with notes on the [Releases page](https://github.com/ILikeHostingServices/Screencap-Documentation-Tool/releases) and in `CHANGELOG.md`. The tag is the version of the project as a whole. Each script also carries its own version in its header, which only changes when that script changes.

To cut a new release, add a `vX.Y.Z <commit SHA>` line to `.github/releases/manifest.txt` and the notes in `.github/releases/vX.Y.Z.md`, push, then run **Actions > Publish releases > Run workflow** on GitHub. The workflow creates the annotated tag and the release; anything that already exists is skipped.

The Quick Start commands always install the latest code on the default branch. To install a specific release instead, for example to keep several PCs on the same version:

```powershell
& ([scriptblock]::Create((irm https://raw.githubusercontent.com/ILikeHostingServices/Screencap-Documentation-Tool/v1.4.0/install.ps1))) -Ref v1.4.0
```

```bash
sudo SCREENCAP_REF=v1.4.0 bash -c "$(curl -fsSL https://raw.githubusercontent.com/ILikeHostingServices/Screencap-Documentation-Tool/v1.4.0/install.sh)"   # macOS: drop sudo
```

### Portable FFmpeg (No Admin Rights)

If you cannot install FFmpeg system-wide, download a Windows build from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) or [BtbN](https://github.com/BtbN/FFmpeg-Builds/releases), extract it, and copy `ffmpeg.exe` and `ffprobe.exe` into `tools\ffmpeg\bin\` inside this folder. The tool checks there before it checks the PATH.

### Command Line Reference

Everything in the GUI is also available as a switch. On Linux and macOS use the `screencap` command (for example `screencap --threshold 0.01 --force`). On Windows run `Run-Screencap.bat` from the install folder, or `py -3 .\screencap.py`, with the same switches.

| Switch | Default | What it does |
| --- | --- | --- |
| `-s`, `--source` | `./source` | Folder to read recordings from. |
| `-o`, `--output` | `./output` | Folder to write results to. |
| `-r`, `--recursive` | off | Also scan subfolders of the source folder. Output mirrors the folder layout. |
| `-t`, `--threshold` | `0.005` | Sensitivity, 0 to 1. Lower catches smaller changes (more screenshots); higher ignores them (fewer screenshots). |
| `--debounce` | `1.0` | Changes closer together than this many seconds are merged into one step. |
| `-c`, `--capture-point` | `end` | `end` takes the screenshot just before the next change (finished state). `start` takes it shortly after each change. |
| `--lead` | `0.25` | With `end`: how many seconds before the next change to take the screenshot. |
| `--settle` | `0.5` | With `start`: how many seconds to wait after a change so animations can finish. |
| `--max-wait` | `10` | Splits a non-stop change (scrolling, video playback) into a new step at least this often. |
| `--min-gap` | `1.0` | Never takes two screenshots closer together than this many seconds. |
| `--analyze-fps` | `5` | Frames per second examined. `0` examines every frame (slower, rarely needed). |
| `--analyze-width` | `640` | Width used for analysis only. `0` uses full size. Screenshots are always full resolution. |
| `--no-dedup` | off | Keep screenshots that look identical to an earlier one. |
| `--dedup-threshold` | `0.01` | Two screenshots are duplicates when at most this percent of the picture differs. The default only matches virtually identical screens, so small changes such as a ticked checkbox are kept. Removed duplicates are kept as deleted steps and can be restored in the Steps tab. |
| `--crop` | none | Crop every screenshot to `X:Y:W:H` (pixels of the recording), for example `0:0:1920:1080` for the left monitor of a dual-screen recording. Width and height are rounded down to even numbers. Originals stay uncropped, and the crop can be changed in the Steps tab. |
| `--no-highlight` | off | Do not draw the red "what changed" box. It can still be switched on later in the Steps tab, because the changed area is always worked out and saved. |
| `-f`, `--format` | `png` | `png` keeps text sharp, which is best for docs. `jpg` makes smaller files. |
| `--force` | off | Reprocesses recordings that already have output. The previous results, including captions, are moved into a `previous-<date>-<time>` folder rather than deleted. Without it, finished recordings are skipped. |
| `--dry-run` | off | Lists the steps that would be captured without saving anything. |
| `--ffmpeg`, `--ffprobe` | auto | Explicit paths to the FFmpeg executables. |
| `-v`, `--verbose` | off | Shows debug output on screen, including the exact FFmpeg commands. |

Exit codes: `0` success, `1` one or more recordings failed, `2` setup problem (FFmpeg not found), `130` cancelled with Ctrl+C.

## Troubleshooting

Start with the log. Every run appends to `output/screencap.log`, with timestamps in `YYYY-MM-DD HH:MM:SS` (24 hour) format. In the GUI the same information is on the **Log** tab; on the command line, add `-v` to see debug detail on screen. Each recording is processed independently, so one failure does not stop the rest: look for the `FAILED` line to see which recording failed and why.

### Setup Problems

| Symptom | Cause / Fix |
| --- | --- |
| `A system-wide install needs an Administrator PowerShell window` | You used `-SystemWide` in a normal window. Right-click Start > **Terminal (Admin)** and paste the command again, or drop `-SystemWide` to install just for you. |
| `Use either -SystemWide or -UserOnly, not both` | Pick one switch, or leave both off and let the installer decide. |
| `Run this installer with sudo on Linux` | The Linux installer needs root to install packages and write to `/opt`. Use the `sudo bash -c ...` command from the Quick Start. |
| `Do not use sudo on macOS` | Homebrew refuses to run as root. Run the macOS command without `sudo`. |
| `dnf could not install ...` | On RHEL, Rocky, or Alma Linux, FFmpeg comes from EPEL and RPM Fusion. Enable those repositories, then run the installer again. |
| `Unsupported package manager` | Your distribution is not one the installer knows. Install `ffmpeg`, Python 3.8+, and Python Tkinter yourself, then run the installer again; it will skip straight to installing the tool. |
| `FFmpeg was not found` (exit code 2) | FFmpeg is not installed or not on the PATH. Open a **new** terminal and paste the Quick Start command again. Alternatively, use a portable copy in `tools\ffmpeg\bin\` or pass `--ffmpeg` / `--ffprobe`. |
| `Python was not found; run without arguments to install from the Microsoft Store` | This is the Windows "App execution alias" placeholder, not real Python. Paste the Quick Start command again to install real Python, or turn the alias off in Settings > Apps > Advanced app settings > App execution aliases. |
| `running scripts is disabled on this system` | PowerShell execution policy is blocking the script. The Quick Start command is not affected. For a local script, use the `powershell -ExecutionPolicy Bypass -File .\install.ps1` form shown in [Reviewing The Installer First](#reviewing-the-installer-first). |
| `No module named 'tkinter'` | Python was installed without Tcl/Tk, which the GUI needs. Re-run the python.org installer, choose **Modify**, and tick **tcl/tk and IDLE**. The winget package includes it by default. |

### GUI Problems

| Symptom | Cause / Fix |
| --- | --- |
| Double-clicking `Run-Screencap-GUI.bat` does nothing | The GUI hit an error before its window opened, and GUI apps have no console to show it. Run `py -3 C:\DATA\Tools\Screencap-Documentation-Tool\screencap_gui.pyw` from a terminal to see the error. |
| Taskbar shows the Python icon instead of the app icon | The shortcut was created by an older installer. Paste the Quick Start command again to recreate it, unpin the old taskbar entry, and pin the app again from the Start Menu. |
| Preview says `Preview unavailable` | Previews are drawn with FFmpeg. Check that the **Log** tab shows `Using FFmpeg: ...` at startup. |

### Processing Problems

| Symptom | Cause / Fix |
| --- | --- |
| `Skipping <video> (already processed ...)` | Output already exists. Tick **Reprocess videos that are already done** (command line: `--force`). |
| `0 raw changes` for a recording | The threshold is too high for this recording. Use Sensitivity **High** (command line: `--threshold 0.002`). |
| `ffprobe failed: ... moov atom not found` | The `.mp4` or `.mov` was never finalized, because the recording crashed or is still being written. Recording to `.mkv` in OBS avoids this. |
| `no video stream found` | The file is audio-only or damaged. |
| Very slow on long 4K recordings | Decoding the video is the bottleneck. Keep `--analyze-fps` at 5, or lower it to 2. |
