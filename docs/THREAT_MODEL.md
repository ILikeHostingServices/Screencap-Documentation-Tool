THREAT_MODEL.md v1.0.0 (Last Rev: 2026-10-17)

# Security Assessment And Threat Model

The most likely and most damaging security problems for ScreenCap Docs, where they could come from, and what protects against each one. It builds on the design in [ARCHITECTURE.md](ARCHITECTURE.md). The maintainer reviews this page before each feature release and whenever a feature adds a new interface, file type, or network use.

## What Needs Protecting

1. **What is on screen.** Recordings and screenshots can show passwords, license keys, tokens, internal hostnames, and personal data. This is the most sensitive asset.
2. **The computers that run the app.** The app and its installers run on work PCs and servers, sometimes with administrator rights during setup.
3. **The release pipeline.** Anyone who could change a release could reach every computer that installs or updates the app.

## Attack Surface

| Entry point | Trust | Notes |
|---|---|---|
| Video files and `steps.json` opened by the user | Untrusted | Could come from someone else. Parsed by FFmpeg and Python's `json`. |
| `<recording>.events.json` | Untrusted | Read when the steps are found. |
| Text read from screenshots (OCR) | Untrusted | Ends up in captions and exports. |
| Captions and labels typed by the user | Untrusted | Written into HTML, Word, PDF, and PowerPoint. |
| Update check and Update Now | Network | Responses from `api.github.com` and GitHub's download host. |
| Install scripts | Network | Download the app and its helpers. |
| Pull requests and issues | Untrusted | Run in CI. |
| Release workflow | Privileged | Holds the signing key and store tokens. |

## Threats And Controls

| Threat | Impact | Controls |
|---|---|---|
| A secret on screen ends up readable in a shared guide | High | Automatic blur of passwords, keys, tokens, and addresses; boxes are clamped to the frame so none are skipped; unblurred copies are kept apart and exports made from them carry a warning; typed characters are never stored, only key names; administrators can turn off key notes (`SCREENCAP_NO_KEYS=1`). |
| A crafted caption or file name injects markup into an export | Medium | Captions are escaped for HTML and Markdown before export (Word is made from Markdown), and the PowerPoint writer escapes XML. |
| Update Now installs a tampered file | High | Downloads only from this project's release on GitHub over HTTPS; refuses other hosts and unexpected file names; checks the SHA256 against `SHA256SUMS.txt` before running; can be turned off by administrators. |
| A non-administrator replaces program files after an all-users install | High | Setup installs to Program Files, which only administrators can change; the install script removes inherited write access from custom folders. |
| The install folder on PATH lets another program be found first | Low | The folder is only writable by administrators for all-users installs, and by the user for just-me installs. |
| A vulnerable bundled component | Medium | The app uses only the Python standard library; the Windows build's components are listed in the SBOM; Dependabot and dependency review flag known vulnerabilities. |
| A pull request steals secrets or changes a release | High | Pull request runs get no secrets and a read-only token; no `pull_request_target`; workflow inputs are passed through environment variables; third-party actions are pinned to a commit; `main` is protected by a ruleset; release jobs run only from `main`. |
| A release is changed after it is built | High | SHA256 checksums, build provenance attestations, and signed apt and dnf repositories. |
| A maintainer account is taken over | High | Two-factor authentication is required for the organization; one account holds admin access; secrets are not readable after they are saved. |

## Accepted Risks

- The Windows programs are not code signed yet, so SmartScreen warns on first start. Checksums and attestations are the substitute. See [CODE_SIGNING_POLICY.md](../CODE_SIGNING_POLICY.md).
- Helper programs (FFmpeg, Tesseract, Pandoc, browsers, VLC) are updated by their own installers or package managers, not by this project.
- One maintainer: changes are not reviewed by a second person. Every change still passes the full test suite, CodeQL, and the dependency review before it is merged.
