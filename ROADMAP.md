ROADMAP.md v1.1.0 (Last Rev: 2026-10-02)

# Roadmap

Ideas that were approved in principle but are on hold until they have been discussed further. Nothing here is being built yet.

## On Hold: Needs Discussion First

| # | Idea | Why it is on hold | Questions to settle |
| --- | --- | --- | --- |
| 5 | **Narration to captions.** Transcribe spoken narration offline with Whisper (whisper.cpp) and attach the words to each step by timestamp as a first-draft caption. | Too ambitious for now. Adds a large download (speech model) and noticeable processing time. | Which model size (accuracy vs speed)? Run automatically or only on request? Should captions be overwritten or only filled when empty? |
| 7 | **Watch folder.** Automatically process new recordings as soon as the recorder finishes writing them. | Needs a design discussion. | Background service, scheduled task, or only while the GUI is open? How to detect that a recording is finished (OBS still writing)? Notifications when done? Which machines run it? |
| 12 | **Single-file Windows app.** Package the tool as one `.exe` with PyInstaller so Python does not need to be installed. | Needs a discussion. Unsigned executables often trigger antivirus or SmartScreen warnings. | Code signing certificate? Keep the Python install as the main path, or switch? How are updates delivered? |

## Done

| # | Idea | Decisions |
| --- | --- | --- |
| 11 | **Automated testing on real Windows** (shipped in v1.13.0) | Tests and the GUI test run on Windows and Linux on every push and pull request. The installers run on Windows (just-you and system-wide), Linux, and macOS when an installer changes, weekly, and on demand. Read-only workflow token, no secrets, free for public repositories. See "Automated Testing" in `README.md`. |

See `CHANGELOG.md` for everything that has shipped.
