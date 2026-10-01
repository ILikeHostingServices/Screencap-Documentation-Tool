README.md v1.1.0 (Last Rev: 2026-10-01)

# Screencap Documentation Tool

## Overview

Record your screen while you install or configure a program, drop the video in the `source` folder, and this tool pulls out a screenshot of every step for you. No more scrubbing through a recording to find the right frames.

It uses [FFmpeg](https://ffmpeg.org/) (free, open source) to measure how much the picture changes from one moment to the next. When something on screen changes (a new window, a dialog, a page in a setup wizard), that marks the boundary between two steps. For each step the tool saves one full resolution screenshot and builds a Markdown file (`steps.md`) listing the steps in order with timestamps and a spot for your notes, ready to turn into documentation.

Use it from a desktop GUI (`Run-Screencap-GUI.bat`) or the command line (`screencap.py`). Both use the same engine and produce the same output.

Supported video formats: `.mp4`, `.mov`, `.mkv` (case does not matter).

Runs on Windows 11 (primary target), Linux, and macOS. Only needs Python 3.8+ and FFmpeg, both free. No Python packages to install.

### How Change Detection Works

1. **Analyze.** FFmpeg samples the video (5 frames per second, downscaled to 640 px wide, which keeps it fast) and scores how different each frame is from the previous one using its `scene` filter. A score above the threshold counts as a change.
2. **Group.** Bursts of changes close together (typing, a window animating open, a fade) are merged into one change so you get one screenshot per step, not twenty.
3. **Capture.** Between two changes the screen is stable; that stable period is one step. By default the screenshot is taken just before the next change begins, so it shows the step in its finished state (fields filled in, progress bar complete, mouse on the button about to be clicked). Screenshots are pulled from the original video at full resolution.

Think of it like a monitoring system that alerts on state changes rather than polling: instead of a screenshot every N seconds, you only get one when the "state" of the screen actually changes.

## Files

| Path | Purpose |
| --- | --- |
| `screencap.py` | The detection engine and command line tool. Run with `--help` for every option. |
| `screencap_gui.pyw` | Desktop GUI (Tkinter, included with Python). Runs without a console window. |
| `Run-Screencap-GUI.bat` | Windows double-click launcher for the GUI. |
| `Run-Screencap.bat` | Windows double-click launcher for the command line version. Passes any arguments through to `screencap.py`. |
| `Install-Prerequisites.ps1` | Windows 11 helper that installs Python 3 and FFmpeg with `winget` if missing. |
| `source/` | Put your recordings here. Contents are git-ignored. |
| `output/` | Screenshots land here, one subfolder per video. Contents are git-ignored. |
| `output/screencap.log` | Full log of every run, including debug detail. |
| `output/<video>/steps.md` | Ordered list of steps with screenshots, timestamps, and a notes placeholder. |
| `output/<video>/steps.json` | Same data in machine-readable form, plus the settings used. |
| `%APPDATA%\ScreencapDocTool\gui_settings.json` | GUI settings (last folders and detection values). Stored in your user profile, not the repo. Delete it to reset the GUI. |
| `tools/ffmpeg/bin/` | Optional. Put a portable `ffmpeg.exe` and `ffprobe.exe` here if you cannot install FFmpeg system-wide. Git-ignored. |

### Useful Commands And Switches

| Switch | Default | What it does |
| --- | --- | --- |
| `-s`, `--source` | `./source` | Folder to read videos from. |
| `-o`, `--output` | `./output` | Folder to write screenshots to. |
| `-r`, `--recursive` | off | Also scan subfolders of `source` (output mirrors the folder layout). |
| `-t`, `--threshold` | `0.005` | Change sensitivity, 0 to 1. Lower catches smaller changes (more screenshots). Higher ignores small changes (fewer screenshots). |
| `--debounce` | `1.0` | Changes closer together than this many seconds are treated as one step. |
| `-c`, `--capture-point` | `end` | `end` = screenshot the settled screen just before the next change. `start` = screenshot shortly after each change. |
| `--lead` | `0.25` | (`end` mode) Seconds before the next change to take the screenshot. |
| `--settle` | `0.5` | (`start` mode) Seconds to wait after a change so animations finish. |
| `--max-wait` | `10` | Split a non-stop change (scrolling, video playback) into steps at least this often. |
| `--min-gap` | `1.0` | Never take two screenshots closer together than this. |
| `--analyze-fps` | `5` | Frames per second examined. `0` = every frame (slower, rarely needed). |
| `--analyze-width` | `640` | Width used for analysis only. `0` = full size. |
| `-f`, `--format` | `png` | `png` (sharp text, best for docs) or `jpg` (smaller files). |
| `--force` | off | Reprocess videos that already have output. Without it, finished videos are skipped. |
| `--dry-run` | off | Show the steps that would be captured without saving anything. Good for tuning. |
| `--ffmpeg`, `--ffprobe` | auto | Explicit paths to the FFmpeg executables. |
| `-v`, `--verbose` | off | Show debug output (including the exact FFmpeg commands) on screen. |

Exit codes: `0` success, `1` one or more videos failed, `2` setup problem (FFmpeg missing), `130` cancelled with Ctrl+C.

## Quick Start

### Windows 11

1. Download or clone this repository, for example to `C:\Tools\Screencap-Documentation-Tool`.
2. Open PowerShell in that folder and install the prerequisites:
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\Install-Prerequisites.ps1
   ```
   This installs Python 3 (`Python.Python.3.12`) and FFmpeg (`Gyan.FFmpeg`) with `winget` if they are not already present. If it says something was not detected yet, close PowerShell, open a new window, and run it again so the updated PATH is picked up.
3. Copy your `.mp4`, `.mov`, or `.mkv` recordings into the `source` folder (or point the GUI at the folder your recorder saves to).
4. Double-click `Run-Screencap-GUI.bat`, then click **Process All**.
5. Review the screenshots in the **Preview** tab, then click **Open steps.md** (VS Code, Obsidian, Typora, or any Markdown viewer shows the images inline) and start writing.

Prefer the command line? Double-click `Run-Screencap.bat`, or from a terminal:

```powershell
py -3 .\screencap.py
```

### Using The GUI

| Area | What it does |
| --- | --- |
| **Folders** | Source and output folders. **Browse...** to change, **Open** to view in Explorer. **Include subfolders** scans the source recursively. |
| **Videos** | Every recording found, with its status (New, Queued, Processing %, Done, Failed, Cancelled) and step count. Ctrl+click or Shift+click to select several, then **Process Selected**; or **Process All**. Double-click a row to open its output folder. **Cancel** stops after the current FFmpeg step. |
| **Detection Settings** | **Sensitivity** presets (High / Normal / Low) fill in the threshold, or type your own. **Screenshot taken** picks finished state (default) or right after each change. Every option in the Useful Commands And Switches table above is available here. **Dry run** counts steps without saving, handy for tuning. **Reset Defaults** restores the recommended values. |
| **Preview tab** | Step list and a scaled preview of each screenshot. **< Prev / Next >** to page through, double-click a step or **Open Image** to view full size, **Open steps.md** to start writing. |
| **Log tab** | Live log of the run. Errors show in red. The same log is appended to `output\screencap.log`. |

Settings are saved when you process or close the window and restored next time.

### Linux / macOS

```bash
sudo apt install ffmpeg python3      # macOS: brew install ffmpeg python
python3 screencap.py
```

## After Install Configuration

### Tuning For Your Recordings

Start with a dry run to see how many steps are found without writing files:

```powershell
py -3 .\screencap.py --dry-run
```

- **Too many screenshots** (near duplicates, mouse hover effects): raise the threshold, for example `--threshold 0.01` or `0.02`, and/or raise `--debounce` to `2`.
- **Missing steps** (a checkbox or small text change not caught): lower the threshold, for example `--threshold 0.002`, or set `--analyze-width 0` so small details are not lost to downscaling.
- **Screenshots show a half-drawn window**: you are probably in `--capture-point start`; increase `--settle` or switch back to the default `end`.

Pass the same switches to the launcher: `Run-Screencap.bat --threshold 0.01 --force`.

### Recording Tips For Best Results

- Pause briefly (about 1 second) after each meaningful step. The tool keys off moments when the screen is still.
- Record a single window or monitor instead of a multi-monitor desktop, and turn off notifications (Windows Focus Assist / Do Not Disturb) so popups do not create false steps.
- Free, open source recorders that work well: [OBS Studio](https://obsproject.com/) (record to `.mkv` and remux to `.mp4` if needed, as MKV survives a crash mid-recording) or the built-in Windows Snipping Tool screen recorder.

### Keeping Sensitive Data Out Of Git

Setup recordings very often capture passwords, license keys, API tokens, internal hostnames, and IP addresses. This repository is public, so `.gitignore` excludes the contents of `source/` and `output/`, all video and image files, logs, and the `tools/` folder. Before you commit anything:

```powershell
git status --short
```

and confirm no media, logs, or configuration with secrets is listed. Review and blur/redact screenshots before publishing documentation built from them.

### Portable FFmpeg (No Admin Rights)

Download a Windows build from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) or [BtbN](https://github.com/BtbN/FFmpeg-Builds/releases), extract it, and copy `ffmpeg.exe` and `ffprobe.exe` into `tools\ffmpeg\bin\` inside this folder. The tool checks there before checking the PATH.

## Troubleshooting

Logs: every run appends to `output/screencap.log` (timestamps in `YYYY-MM-DD HH:MM:SS`, 24 hour). Add `-v` to also see debug detail, including the exact FFmpeg commands, on screen.

| Symptom | Cause / Fix |
| --- | --- |
| `FFmpeg was not found` (exit code 2) | FFmpeg is not installed or not on the PATH. Run `Install-Prerequisites.ps1`, then open a **new** terminal. Or use a portable copy in `tools\ffmpeg\bin\`, or pass `--ffmpeg` / `--ffprobe`. |
| `Python was not found; run without arguments to install from the Microsoft Store` | That is the Windows "App execution alias" stub, not real Python. Run `Install-Prerequisites.ps1`, or turn the alias off in Settings > Apps > Advanced app settings > App execution aliases. |
| `running scripts is disabled on this system` | PowerShell execution policy. Use the `powershell -ExecutionPolicy Bypass -File .\Install-Prerequisites.ps1` form shown above. |
| `Skipping <video> (already processed ...)` | Output already exists. Add `--force` to regenerate. |
| `ffprobe failed: ... moov atom not found` | The `.mp4`/`.mov` was not finalized (recording crashed or is still being written). Record to `.mkv` in OBS to avoid this, then remux. |
| `no video stream found` | The file is audio-only or damaged. |
| Video is found but `0 raw changes` | Threshold too high for this recording. Try `--threshold 0.002`. |
| Double-clicking `Run-Screencap-GUI.bat` does nothing | The GUI hit an error before its window opened (GUI apps have no console to show it). Run `py -3 .\screencap_gui.pyw` from a terminal to see the error. |
| `No module named 'tkinter'` | Python was installed without Tcl/Tk. Re-run the python.org installer, choose **Modify**, and tick **tcl/tk and IDLE**. The winget package includes it by default. |
| GUI preview says `Preview unavailable` | Previews are rendered with FFmpeg; make sure FFmpeg is found (the Log tab shows `Using FFmpeg: ...` at startup). |
| Very slow on long 4K recordings | Decoding is the bottleneck. Keep `--analyze-fps` at 5 or lower it to 2. |
| A video failed but others succeeded (exit code 1) | Each video is processed independently; check `output/screencap.log` for the `FAILED` line and the reason. |
