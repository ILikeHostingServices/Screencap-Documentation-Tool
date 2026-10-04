ROADMAP.md v1.6.0 (Last Rev: 2026-10-04)

# Roadmap

Ideas that were approved in principle but are on hold until they have been discussed further. Nothing here is being built yet.

## On Hold: Needs Discussion First

| # | Idea | Why it is on hold | Questions to settle |
| --- | --- | --- | --- |
| 12 | **Single-file Windows app.** Package the tool as one `.exe` with PyInstaller so Python does not need to be installed. | In progress. v1.15.0: unsigned packaged app (portable zip) built and tested in GitHub Actions and attached to each release. v1.16.0: Windows installer (per-user or all users, silent install supported), also built and tested in GitHub Actions. Next: code signing through SignPath Foundation (free for open source projects; the MIT License was added in v1.13.1 to qualify; steps in `HANDOFF.md`). | The Python install stays the main path; the packaged app is an extra download. Updates: download the new release. FFmpeg, Tesseract, Pandoc, and VLC stay separate installs (their licenses). |

## Dropped

| # | Idea | Decision |
| --- | --- | --- |
| 7 | **Watch folder.** Automatically process new recordings as soon as they finish. | Not worth the added complexity; processing stays a manual click. |

## Done

| # | Idea | Decisions |
| --- | --- | --- |
| 5 | **Captions from narration** (shipped in v1.14.0) | Optional and off by default: recordings are not narrated today, but may be later. Offline speech recognition with faster-whisper in its own `whisper-env`, added with `-WithWhisper` or `SCREENCAP_WITH_WHISPER=1`. Only empty captions are filled. Default model `base`. See "Captions From Narration" in `README.md`. |
| 11 | **Automated testing on real Windows** (shipped in v1.13.0) | Tests and the GUI test run on Windows and Linux on every push and pull request. The installers run on Windows (just-you and system-wide), Linux, and macOS when an installer changes, weekly, and on demand. Read-only workflow token, no secrets, free for public repositories. See "Automated Testing" in `README.md`. |

See `CHANGELOG.md` for everything that has shipped.
