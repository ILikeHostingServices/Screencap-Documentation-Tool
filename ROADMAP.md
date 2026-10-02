ROADMAP.md v1.2.0 (Last Rev: 2026-10-02)

# Roadmap

Ideas that were approved in principle but are on hold until they have been discussed further. Nothing here is being built yet.

## On Hold: Needs Discussion First

| # | Idea | Why it is on hold | Questions to settle |
| --- | --- | --- | --- |
| 12 | **Single-file Windows app.** Package the tool as one `.exe` with PyInstaller so Python does not need to be installed. | Researching code signing options (cost, identity checks, SmartScreen). | Which signing route, if any? Keep the Python install as the main path, or switch? How are updates delivered? |

## Parked

| # | Idea | Decision |
| --- | --- | --- |
| 5 | **Narration to captions.** Transcribe spoken narration offline with Whisper and use it as first-draft captions. | Optional, not planned: recordings are not narrated. Revisit only if that changes. |

## Dropped

| # | Idea | Decision |
| --- | --- | --- |
| 7 | **Watch folder.** Automatically process new recordings as soon as they finish. | Not worth the added complexity; processing stays a manual click. |

## Done

| # | Idea | Decisions |
| --- | --- | --- |
| 11 | **Automated testing on real Windows** (shipped in v1.13.0) | Tests and the GUI test run on Windows and Linux on every push and pull request. The installers run on Windows (just-you and system-wide), Linux, and macOS when an installer changes, weekly, and on demand. Read-only workflow token, no secrets, free for public repositories. See "Automated Testing" in `README.md`. |

See `CHANGELOG.md` for everything that has shipped.
