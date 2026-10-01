README.md v1.2.0 (Last Rev: 2026-10-01)

# Screencap Documentation Tool

## Overview

Record your screen while you install or configure a program, drop the recording in a folder, and this tool pulls out a screenshot of every step for you. No more scrubbing through video to find the right frames.

For each recording you get:

- One full resolution screenshot per step, numbered in order.
- A `steps.md` file listing every step with its timestamp, its screenshot, and a blank notes spot, ready to turn into documentation.

You can run it from a desktop GUI or from the command line. Both use the same engine and produce the same output. It works with `.mp4`, `.mov`, and `.mkv` recordings and runs on Windows 11 (the primary target), Linux, and macOS. The only requirements are Python 3.8+ and [FFmpeg](https://ffmpeg.org/), both free and open source.

### How It Finds The Steps

Think of it like monitoring that alerts on state changes instead of polling on a timer: rather than grabbing a frame every N seconds, the tool only takes a screenshot when the screen actually changes state.

1. **Detect changes.** FFmpeg samples the video (5 frames per second at 640 px wide, which keeps it fast) and scores how different each frame is from the one before. A score above the sensitivity threshold counts as a change.
2. **Group bursts.** Changes that happen close together, like typing, a window animating open, or a fade, are merged into a single change. You get one screenshot per step, not twenty.
3. **Capture the step.** The stable stretch between two changes is one step. By default the screenshot is taken just before the next change starts, so each step is shown finished: fields filled in, progress bar complete, mouse on the button about to be clicked. Screenshots come from the original video at full resolution.

## Files

| Path | Purpose |
| --- | --- |
| `Run-Screencap-GUI.bat` | Double-click to start the GUI on Windows. |
| `Run-Screencap.bat` | Double-click to run the command line version on Windows. Passes any arguments through to `screencap.py`. |
| `Install-Prerequisites.ps1` | Installs Python 3 and FFmpeg with `winget` if they are missing. |
| `screencap_gui.pyw` | The GUI (Tkinter, included with Python). |
| `screencap.py` | The detection engine and command line tool. |
| `source/` | Default folder for your recordings. |
| `output/` | Default folder for results, one subfolder per recording. |
| `tools/ffmpeg/bin/` | Optional spot for a portable `ffmpeg.exe` and `ffprobe.exe` (see [Portable FFmpeg](#portable-ffmpeg-no-admin-rights)). |

Each run creates these files in the output folder:

| Path | Purpose |
| --- | --- |
| `output/<video>/step_001_00-00-03.750.png` | Screenshot for each step. The name holds the step number and timestamp. |
| `output/<video>/steps.md` | The steps in order, with screenshots, timestamps, and notes placeholders. |
| `output/<video>/steps.json` | The same data in machine-readable form, plus the settings used. |
| `output/screencap.log` | Detailed log of every run. Check here first when something goes wrong. |

The GUI remembers your last folders and settings in `%APPDATA%\ScreencapDocTool\gui_settings.json` (outside the repo). Delete that file to reset the GUI.

Switches worth knowing for diagnostics (the full list is in the [Command Line Reference](#command-line-reference)):

- `--dry-run` lists the steps that would be captured without saving anything.
- `-v` shows debug output on screen, including the exact FFmpeg commands.
- `--force` reprocesses recordings that already have output.

## Quick Start

### Windows 11

1. Download or clone this repository, for example to `C:\Tools\Screencap-Documentation-Tool`.
2. Open PowerShell in that folder and install the prerequisites:
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\Install-Prerequisites.ps1
   ```
   This installs Python 3 (`Python.Python.3.12`) and FFmpeg (`Gyan.FFmpeg`) if they are not already present. If it reports that something was not detected yet, close PowerShell, open a new window, and run it again so the updated PATH is picked up.
3. Copy your recordings into the `source` folder, or point the GUI at the folder your recorder already saves to.
4. Double-click `Run-Screencap-GUI.bat`, then click **Process All**.
5. Review the results in the **Preview** tab, then click **Open steps.md** and start writing. VS Code, Obsidian, Typora, or any Markdown viewer shows the screenshots inline.

Prefer the command line? Double-click `Run-Screencap.bat`, or run:

```powershell
py -3 .\screencap.py
```

### Linux / macOS

```bash
sudo apt install ffmpeg python3      # macOS: brew install ffmpeg python
python3 screencap.py                 # or: python3 screencap_gui.pyw
```

## After Install Configuration

### Using The GUI

The window is laid out top to bottom in the order you use it:

1. **Folders.** Choose where recordings come from and where results go. **Browse...** changes a folder and **Open** shows it in Explorer. Tick **Include subfolders** to scan the source folder recursively.
2. **Videos.** Lists every recording found, with its status (New, Queued, Processing, Done, Failed, Cancelled) and step count. Click **Process All**, or Ctrl+click / Shift+click to pick several and click **Process Selected**. **Cancel** stops the run, and double-clicking a row opens its output folder.
3. **Detection Settings.** Pick a **Sensitivity** preset (High, Normal, Low) or type your own threshold. **Screenshot taken** chooses between the finished state of each step (default) and right after each change. Tick **Dry run** to count steps without saving anything. **Reset Defaults** restores the recommended values.
4. **Preview tab.** Page through the captured steps with **< Prev** and **Next >**. Double-click a step or click **Open Image** to see it full size, and click **Open steps.md** to start writing.
5. **Log tab.** Shows the run as it happens, with errors in red. The same log is saved to `output\screencap.log`.

Your folders and settings are saved when you process or close the window and restored the next time you open it.

### Tuning For Your Recordings

The defaults are tuned for typical setup wizards. If a recording gives you too many or too few screenshots, do a dry run first so you can experiment without writing files (GUI: tick **Dry run**; command line: `--dry-run`), then adjust:

| Problem | GUI setting | Command line |
| --- | --- | --- |
| Too many near-duplicate screenshots (hover effects, small redraws) | Sensitivity **Low**, or raise **Merge changes within** to 2 | `--threshold 0.015` and/or `--debounce 2` |
| Missing steps (a checkbox or small text change not caught) | Sensitivity **High**, or set **Analyze width** to 0 | `--threshold 0.002` and/or `--analyze-width 0` |
| Screenshots show a half-drawn window | **Screenshot taken**: Finished state, or raise **Settle after change** | `--capture-point end`, or raise `--settle` |

After changing settings, reprocess with **Reprocess videos that are already done** ticked (command line: `--force`).

### Recording Tips For Best Results

- Pause for about a second after each meaningful step. The tool looks for moments when the screen is still.
- Record a single window or monitor rather than a multi-monitor desktop.
- Turn on Do Not Disturb so notification popups do not show up as extra steps.
- [OBS Studio](https://obsproject.com/) (free, open source) and the built-in Windows Snipping Tool recorder both work well. In OBS, record to `.mkv`, which survives a crash mid-recording, and remux to `.mp4` if needed.

### Keeping Sensitive Data Out Of Git

Setup recordings often capture passwords, license keys, API tokens, internal hostnames, and IP addresses. This repository is public, so `.gitignore` excludes everything in `source/` and `output/`, all video and image files, logs, and the `tools/` folder. Before you commit anything, run:

```powershell
git status --short
```

and confirm that no media, logs, or files containing secrets are listed. Also review, and blur or redact, screenshots before publishing documentation built from them.

### Portable FFmpeg (No Admin Rights)

If you cannot install FFmpeg system-wide, download a Windows build from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) or [BtbN](https://github.com/BtbN/FFmpeg-Builds/releases), extract it, and copy `ffmpeg.exe` and `ffprobe.exe` into `tools\ffmpeg\bin\` inside this folder. The tool checks there before it checks the PATH.

### Command Line Reference

Everything in the GUI is also available as a switch, either with `py -3 .\screencap.py` or through `Run-Screencap.bat` (for example `Run-Screencap.bat --threshold 0.01 --force`).

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
| `-f`, `--format` | `png` | `png` keeps text sharp, which is best for docs. `jpg` makes smaller files. |
| `--force` | off | Reprocesses recordings that already have output. Without it, finished recordings are skipped. |
| `--dry-run` | off | Lists the steps that would be captured without saving anything. |
| `--ffmpeg`, `--ffprobe` | auto | Explicit paths to the FFmpeg executables. |
| `-v`, `--verbose` | off | Shows debug output on screen, including the exact FFmpeg commands. |

Exit codes: `0` success, `1` one or more recordings failed, `2` setup problem (FFmpeg not found), `130` cancelled with Ctrl+C.

## Troubleshooting

Start with the log. Every run appends to `output/screencap.log`, with timestamps in `YYYY-MM-DD HH:MM:SS` (24 hour) format. In the GUI the same information is on the **Log** tab; on the command line, add `-v` to see debug detail on screen. Each recording is processed independently, so one failure does not stop the rest: look for the `FAILED` line to see which recording failed and why.

### Setup Problems

| Symptom | Cause / Fix |
| --- | --- |
| `FFmpeg was not found` (exit code 2) | FFmpeg is not installed or not on the PATH. Run `Install-Prerequisites.ps1`, then open a **new** terminal. Alternatively, use a portable copy in `tools\ffmpeg\bin\` or pass `--ffmpeg` / `--ffprobe`. |
| `Python was not found; run without arguments to install from the Microsoft Store` | This is the Windows "App execution alias" placeholder, not real Python. Run `Install-Prerequisites.ps1`, or turn the alias off in Settings > Apps > Advanced app settings > App execution aliases. |
| `running scripts is disabled on this system` | PowerShell execution policy is blocking the script. Use the `powershell -ExecutionPolicy Bypass -File .\Install-Prerequisites.ps1` form from the Quick Start. |
| `No module named 'tkinter'` | Python was installed without Tcl/Tk, which the GUI needs. Re-run the python.org installer, choose **Modify**, and tick **tcl/tk and IDLE**. The winget package includes it by default. |

### GUI Problems

| Symptom | Cause / Fix |
| --- | --- |
| Double-clicking `Run-Screencap-GUI.bat` does nothing | The GUI hit an error before its window opened, and GUI apps have no console to show it. Run `py -3 .\screencap_gui.pyw` from a terminal to see the error. |
| Preview says `Preview unavailable` | Previews are drawn with FFmpeg. Check that the **Log** tab shows `Using FFmpeg: ...` at startup. |

### Processing Problems

| Symptom | Cause / Fix |
| --- | --- |
| `Skipping <video> (already processed ...)` | Output already exists. Tick **Reprocess videos that are already done** (command line: `--force`). |
| `0 raw changes` for a recording | The threshold is too high for this recording. Use Sensitivity **High** (command line: `--threshold 0.002`). |
| `ffprobe failed: ... moov atom not found` | The `.mp4` or `.mov` was never finalized, because the recording crashed or is still being written. Recording to `.mkv` in OBS avoids this. |
| `no video stream found` | The file is audio-only or damaged. |
| Very slow on long 4K recordings | Decoding the video is the bottleneck. Keep `--analyze-fps` at 5, or lower it to 2. |
