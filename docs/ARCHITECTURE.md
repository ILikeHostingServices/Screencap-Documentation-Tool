ARCHITECTURE.md v1.0.0 (Last Rev: 2026-10-17)

# How ScreenCap Docs Works

The design of ScreenCap Docs: the actors, what each one does, where data flows, and every interface the released app exposes. For the file by file list, see [Files](../README.md#files) in the README. For the security analysis built on this page, see [THREAT_MODEL.md](THREAT_MODEL.md).

## Actors

| Actor | What it does |
|---|---|
| The person using the app | Records a task, edits the steps, and exports the guide. Runs the app as an ordinary user. |
| The administrator | Installs the app (optionally for all users) and sets the controls in [SECURITY_FOR_IT.md](SECURITY_FOR_IT.md#administrator-controls). |
| The app (Python, Tkinter) | The GUI (`screencap_gui.pyw`) and the command line tool (`screencap.py`). Starts helper programs and reads and writes files in the chosen folders. |
| Helper programs | FFmpeg and ffprobe (recording, frames, screenshots), Tesseract (reading text to blur and to caption), Pandoc (Word), Microsoft Edge, Chrome, or Chromium in headless mode (PDF), VLC (playback), and the optional faster-whisper speech recognition. They run as the same user with no network use of their own, except the speech model download. |
| GitHub | Hosts the code, runs the builds and tests (GitHub Actions), and serves releases and the update check. |
| Package stores | winget, the Snap Store, Homebrew, the AUR, and the signed apt and dnf repositories on GitHub Pages. |

## Main Flow

1. **Record.** `recorder.py` runs FFmpeg to capture the screen and notes clicks and key names with the system's own functions (`<recording>.events.json`). Any other recorder's video works too.
2. **Find the steps.** `screencap.py` samples the video with FFmpeg, finds where the screen changed, and saves a full resolution screenshot of each step (see [How It Finds The Steps](../README.md#how-it-finds-the-steps)).
3. **Blur and caption.** `redact.py` reads each screenshot with Tesseract and blurs text that matches the sensitive patterns. `actions.py` turns the clicks and keys into first-draft captions; `transcribe.py` can add captions from narration.
4. **Edit.** The Steps tab (`gui_editor.py`) edits `steps.json`; `stepdoc.py` renders each screenshot again from the untouched original with the boxes, blur, and annotations.
5. **Export.** `export.py` writes HTML, Word, PDF, or PowerPoint, plus `steps.md`, into the output folder.

Everything stays in the source and output folders on the computer. Nothing is uploaded.

## External Interfaces

| Interface | Documented in |
|---|---|
| GUI | [Using The GUI](../README.md#using-the-gui) and **Help** in the app |
| Command line (`screencap`, `screencap.py`) | [Command Line Reference](../README.md#command-line-reference) and `screencap --help` |
| Files read and written (`steps.json`, `<recording>.events.json`, exports, settings) | [Files And Settings](SECURITY_FOR_IT.md#files-and-settings) |
| Environment variables for administrators | [Administrator Controls](SECURITY_FOR_IT.md#administrator-controls) |
| Network use (update check, Update Now, speech model) | [Network Use](SECURITY_FOR_IT.md#network-use) |
| Installer options (silent install, PATH, folders) | [Administrator Controls](SECURITY_FOR_IT.md#administrator-controls) and the README Quick Start |

The app has no network listener, no service, no plugin system, and no API for other programs.

## Build And Release

GitHub Actions builds every release from a tagged commit on `main`: PyInstaller and Inno Setup on Windows runners, nfpm, makepkg, and snapcraft on Linux runners. Each file gets a SHA256 checksum and a build provenance attestation, and the Windows release gets an SBOM. Release jobs are the only jobs that can write to the repository or read secrets.
