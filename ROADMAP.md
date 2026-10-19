ROADMAP.md v1.8.1 (Last Rev: 2026-10-19)

# Roadmap

What ScreenCap Docs plans to do over the next year, what it will not do, and ideas on hold. Plans can change; each release's notes and `CHANGELOG.md` say what actually shipped.

## Planned For The Next Year (Through 2027-10)

| Area | Plan |
| --- | --- |
| Recording | Choose what to record, like the Windows Snipping Tool: the whole screen, one window, or a region you draw; and record system sound, switchable on and off (v1.37.0). |
| Distribution | Publish the Microsoft Store listing, finish the winget listing, publish to the AUR once account sign-ups reopen, and evaluate Flathub. |
| Website | Keep https://screencap.ilhs.app current with each release, and replace its screenshots with ones taken on a clean Windows 11 PC. |
| Trust | Reapply for free code signing for the Windows programs; attach an SBOM to every compiled download, snaps included; keep the OpenSSF Best Practices and Baseline results current. |
| Quality | Keep statement coverage at 80% or more on Windows and Linux combined, and every bug fix with a test. |

## Not Planned

These are out of scope; requests for them will be closed with a pointer here.

| Idea | Why not |
| --- | --- |
| Uploading, cloud sync, or accounts | Recordings can contain passwords and internal details. Everything stays on the computer, and there is no server to trust. |
| Usage tracking or telemetry | Same reason; the only network use is the update check and the speech model download. |
| Paid editions or features behind a license key | The app is free and MIT licensed. |
| Editing video | The app turns recordings into step-by-step guides; video editors already do the rest. |
| Recording on Wayland directly | Wayland does not let apps capture the screen without the desktop's own portal. Record with the desktop's recorder and process the file. Revisited when the portals are widely available. |

Ideas below were approved in principle but are on hold until they have been discussed further.

## On Hold: Needs Discussion First

| # | Idea | Why it is on hold | Questions to settle |
| --- | --- | --- | --- |
| 12 | **Single-file Windows app.** Package the tool as one `.exe` with PyInstaller so Python does not need to be installed. | In progress. v1.15.0: unsigned packaged app (portable zip) built and tested in GitHub Actions and attached to each release. v1.16.0: Windows installer (per-user or all users, silent install supported), also built and tested in GitHub Actions. Code signing: **on hold** (2026-10-06). SignPath Foundation declined the free certificate until the project has more public visibility (stars, forks, outside mentions); it can reapply later. The other options (paid SignPath, Azure Artifact Signing, a certificate from a certificate authority, winget or Microsoft Store distribution) are compared in the maintainer notes. Releases stay unsigned with SHA-256 checksums. | The Python install stays the main path; the packaged app is an extra download. Updates: download the new release. FFmpeg, Tesseract, Pandoc, and VLC stay separate installs (their licenses). |

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
