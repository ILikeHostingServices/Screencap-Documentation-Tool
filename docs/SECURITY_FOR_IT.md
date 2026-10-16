SECURITY_FOR_IT.md v1.0.0 (Last Rev: 2026-10-16)

# ScreenCap Docs for IT and Security Teams

What ScreenCap Docs does on a computer, what it sends over the network, what it stores, and how to control and verify it. Use this page to approve the app, write allow-list rules, or answer a security questionnaire. To report a security problem, see [SECURITY.md](../SECURITY.md).

## At A Glance

| Question | Answer |
|---|---|
| Does it send data anywhere? | No recordings, screenshots, documents, or usage data ever leave the PC. The only network use is the optional update check, Update Now, and the one-time speech model download (below). |
| Does it run as administrator? | No. The app runs as the signed-in user. Only installing for all users needs administrator rights. |
| Does it record keystrokes? | It notes key **names** (Enter, Tab, Ctrl+S) while a recording runs, never typed characters. Administrators can switch this off (below). |
| Does it run in the background? | No. Nothing runs at sign-in, and there is no service or scheduled task. |
| Is the source available? | Yes, MIT license. Every release is built by GitHub Actions from this repository. |
| Is it code signed? | Not yet. See [Verifying A Download](#verifying-a-download). |

## Network Use

| When | Address | What |
|---|---|---|
| Help > Check for Updates, or automatic checks if turned on | `api.github.com` | Reads the public list of releases. Nothing about the PC is sent beyond a normal HTTPS request (User-Agent `ScreencapDocumentationTool/<version>`). |
| Update Now (Windows installer copies) | `github.com`, then GitHub's download host (`objects.githubusercontent.com` or `release-assets.githubusercontent.com`) | Downloads the new installer and `SHA256SUMS.txt` from this project's release only; any other address is refused. |
| Captions From Narration, first use | `huggingface.co` and its download hosts | Downloads the speech recognition model once. Speech is recognized on the PC; audio is never uploaded. |
| Help menu links | `github.com` | Opens pages in the browser. |
| Install scripts and the setup's optional extras | `github.com`, `raw.githubusercontent.com`, `api.github.com`, and winget's sources | Only while installing. |

Proxies: the app uses the system's proxy settings (the standard `HTTPS_PROXY` variable is honored).

## Files And Settings

| What | Where |
|---|---|
| Program | Installer: `C:\Program Files\ILHS\Screencap-Documentation-Tool` (all users) or `%LOCALAPPDATA%\Programs\ILHS\Screencap-Documentation-Tool` (just me). Linux packages: `/usr/share/screencap-documentation-tool`. |
| Settings and presets | Windows: `%APPDATA%\ScreencapDocTool`. Linux and macOS: `~/.config/screencap-doc-tool`. |
| Recordings and output | `Documents\ScreenCap Docs\source` and `output` by default, or the folders chosen in the installer or the app. |
| Unblurred copies | When blurring is on, the original screenshots are kept in an `unredacted` folder beside the blurred ones, and exports made from them carry a warning. Delete that folder, or exclude it from file sharing, where screenshots may show sensitive data. |
| Click and key events | `<recording>.events.json` next to each recording made with the built-in recorder: click positions, key names, and timings. |
| Installer settings | `HKLM` or `HKCU\Software\ILHS\Screencap Documentation Tool` (folders chosen in setup). |
| Update downloads | `%TEMP%\ScreencapUpdate` (installer and its log; the installer is removed after use). |

## Administrator Controls

Set these as system environment variables (Group Policy Preferences, Intune, or a login script):

| Variable | Effect |
|---|---|
| `SCREENCAP_NO_UPDATE_CHECK=1` | Turns off update checks and Update Now. Use when updates are deployed centrally. |
| `SCREENCAP_NO_KEYS=1` | Stops the recorder from noting keys; clicks are still noted. The Record window shows the option as switched off by the administrator. |

Silent install for deployment: `Screencap-Documentation-Tool-vX.Y.Z-windows-x64-setup.exe /VERYSILENT /ALLUSERS /NORESTART` (or `/CURRENTUSER`), or `winget install --id ILHS.ScreencapDocumentationTool -e` once the winget listing is approved. Uninstall from Apps or with `unins000.exe /VERYSILENT` in the program folder.

## Behaviors Security Tools May Notice

All of these happen only while the user is recording or exporting, and all are expected:

| Behavior | Why |
|---|---|
| Polls the keyboard and mouse state (`GetAsyncKeyState`, `GetCursorPos`) about 60 times a second | Notes where you click and which named keys you press, to caption the steps. Stops when the recording stops. Typed characters are never stored. |
| Captures the screen with `ffmpeg.exe` (gdigrab) | The recording itself. |
| Hides its small Recording window from screen capture (`SetWindowDisplayAffinity`) | So the recorder's own Stop button is not in the recording. |
| Starts `ffmpeg.exe`, `ffprobe.exe`, `tesseract.exe`, `pandoc.exe`, and Microsoft Edge or Chrome in headless mode, without a console window | Making screenshots, reading text to blur, and the Word and PDF exports. |
| The setup starts `winget` through `cmd.exe` (hidden) when FFmpeg, Tesseract, or Pandoc are chosen | Installs those helpers. |
| Update Now downloads an `.exe` to `%TEMP%` and runs it | The new installer, after its SHA256 is checked against the release's checksum list. Switch off with `SCREENCAP_NO_UPDATE_CHECK=1`. |

Suggested allow-list scope: the program folder above, by path, until releases are code signed.

## Verifying A Download

Every release file is built by GitHub Actions from the tagged source, and the release lists their SHA256 checksums (`SHA256SUMS.txt`, `SHA256SUMS-linux.txt`).

1. Check the checksum: `(Get-FileHash .\<file>).Hash` (Windows) or `sha256sum <file>` (Linux and macOS) must match the line in the checksum file.
2. Check where it was built (releases from 1.36.0 on): `gh attestation verify <file> --repo ILikeHostingServices/Screencap-Documentation-Tool`. This proves the file was built by this repository's GitHub Actions workflow from a specific commit, and was not changed afterwards.
3. Each Windows release (from 1.36.0 on) also lists the components of the app (an SBOM in CycloneDX format, `*-windows-sbom.cdx.json`) for vulnerability scanners and procurement reviews.

The Linux apt and dnf repositories are signed with the ILHS package signing key, published with them.

## How It Is Built And Checked

- Every change is tested on Windows and Linux, and every release is installed and tested on Windows (x64 and ARM64), several Linux distributions, and macOS before it is published.
- GitHub CodeQL and the OpenSSF Scorecard scan the repository; third-party build actions are pinned to exact commits.
- Security problems: report privately as described in [SECURITY.md](../SECURITY.md).
