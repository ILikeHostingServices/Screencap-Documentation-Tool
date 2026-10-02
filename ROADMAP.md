ROADMAP.md v1.0.0 (Last Rev: 2026-10-02)

# Roadmap

Ideas that were approved in principle but are on hold until they have been discussed further. Nothing here is being built yet.

## On Hold: Needs Discussion First

| # | Idea | Why it is on hold | Questions to settle |
| --- | --- | --- | --- |
| 5 | **Narration to captions.** Transcribe spoken narration offline with Whisper (whisper.cpp) and attach the words to each step by timestamp as a first-draft caption. | Too ambitious for now. Adds a large download (speech model) and noticeable processing time. | Which model size (accuracy vs speed)? Run automatically or only on request? Should captions be overwritten or only filled when empty? |
| 7 | **Watch folder.** Automatically process new recordings as soon as the recorder finishes writing them. | Needs a design discussion. | Background service, scheduled task, or only while the GUI is open? How to detect that a recording is finished (OBS still writing)? Notifications when done? Which machines run it? |
| 11 | **Automated testing on real Windows.** A GitHub Actions job that runs the test suite and the installer on a Windows runner. | Needs a discussion about GitHub Actions permissions and cost first. | Run on every push or only before releases? Test both the per-user and Administrator installs? What should the workflow token be allowed to do? |
| 12 | **Single-file Windows app.** Package the tool as one `.exe` with PyInstaller so Python does not need to be installed. | Needs a discussion. Unsigned executables often trigger antivirus or SmartScreen warnings. | Code signing certificate? Keep the Python install as the main path, or switch? How are updates delivered? |

## Done

See `CHANGELOG.md` for everything that has shipped.
