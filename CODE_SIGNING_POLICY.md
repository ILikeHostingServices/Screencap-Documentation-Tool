CODE_SIGNING_POLICY.md v2.0.0 (Last Rev: 2026-10-06)

# Code Signing Policy

The Windows programs attached to this repository's [GitHub releases](https://github.com/ILikeHostingServices/Screencap-Documentation-Tool/releases) are **not code signed**. Code signing is on hold (see roadmap item #12 in [ROADMAP.md](ROADMAP.md)). Because they are not signed, Windows SmartScreen may show **Windows protected your PC** when one is started for the first time.

## How To Check A Download

Each release has a `SHA256SUMS.txt` file listing the checksum of every file attached to it. In PowerShell, in the folder you downloaded to:

```powershell
(Get-FileHash .\Screencap-Documentation-Tool-vX.Y.Z-windows-x64-setup.exe).Hash
```

The result must match the line for that file in `SHA256SUMS.txt` (ignoring upper and lower case). If it matches, choose **More info > Run anyway**. If it does not, delete the file and download it again from the Releases page only.

## How The Programs Are Built

- `Screencap Documentation Tool.exe` (the GUI) and `screencap.exe` (the command line), in the portable zip and the installer, and the installer `Screencap-Documentation-Tool-vX.Y.Z-windows-x64-setup.exe` itself.
- They are built only by the `Windows build` GitHub Actions workflow (`.github/workflows/build-windows.yml`) on GitHub's own Windows machines, from the source code in this repository at a release tag on `main`, and tested before they are attached. Nothing is built on a personal PC.
- Every change reaches `main` through a pull request whose automated tests must pass. All accounts with write access use two-factor authentication, which the organization requires.
- FFmpeg, Tesseract OCR, Pandoc, and VLC are separate programs from their own publishers; they are not included.

## Privacy

This program will not transfer any information to other networked systems unless specifically requested by the user or the person installing or operating it.

In practice: recordings, screenshots, captions, and settings stay on the PC. The program only goes online when the person using it asks for something that needs it: the installers download the tool and its prerequisites (FFmpeg, and optionally Tesseract OCR, Pandoc, and speech recognition), and the optional Captions From Narration feature downloads its speech model once from Hugging Face. Speech recognition itself runs offline. There is no telemetry, analytics, or update check.

## Reporting Problems

Report a security problem, or a file on the Releases page whose checksum does not match `SHA256SUMS.txt`, privately as described in [SECURITY.md](SECURITY.md).
