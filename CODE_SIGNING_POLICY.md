CODE_SIGNING_POLICY.md v1.0.0 (Last Rev: 2026-10-04)

# Code Signing Policy

Free code signing provided by [SignPath.io](https://about.signpath.io), certificate by [SignPath Foundation](https://signpath.org).

Code signing is being set up. Releases up to and including v1.16.0 are not signed; check them against the `SHA256SUMS.txt` file attached to each release (see [README.md](README.md#windows-app-no-python-needed)).

## What Is Signed

Only the Windows programs attached to the [GitHub releases](https://github.com/ILikeHostingServices/Screencap-Documentation-Tool/releases) of this repository:

- `Screencap Documentation Tool.exe` (the GUI) and `screencap.exe` (the command line), inside the portable zip and the installer.
- `Screencap-Documentation-Tool-vX.Y.Z-windows-x64-setup.exe` (the installer).

They are built only by the `Windows build` GitHub Actions workflow (`.github/workflows/build-windows.yml`) from the source code in this repository, from a release tag on `main`. Nothing built anywhere else, and nothing from another project, is signed. FFmpeg, Tesseract OCR, Pandoc, and VLC are separate programs from their own publishers; they are not included or signed.

## Team Roles

| Role | Who |
| --- | --- |
| Committers and reviewers | Members of the [ILikeHostingServices](https://github.com/ILikeHostingServices) GitHub organization with write access to this repository |
| Approvers | [ILHS-Owner](https://github.com/ILHS-Owner) |

Every change reaches `main` through a pull request whose automated tests must pass. Every signing request is approved by hand by an approver. All accounts with write access use two-factor authentication, which the organization requires.

## Privacy

This program will not transfer any information to other networked systems unless specifically requested by the user or the person installing or operating it.

In practice: recordings, screenshots, captions, and settings stay on the PC. The program only goes online when the person using it asks for something that needs it: the installers download the tool and its prerequisites (FFmpeg, and optionally Tesseract OCR, Pandoc, and speech recognition), and the optional Captions From Narration feature downloads its speech model once from Hugging Face. Speech recognition itself runs offline. There is no telemetry, analytics, or update check.

## Reporting Problems

Report a security problem, or a signed file you believe was not built from this repository, privately as described in [SECURITY.md](SECURITY.md).
