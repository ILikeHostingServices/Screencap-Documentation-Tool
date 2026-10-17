THREAT_MODEL.md v1.1.0 (Last Rev: 2026-10-17)

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

## Security Requirements

What you can expect from ScreenCap Docs, and what you cannot:

- **Can expect:** recordings, screenshots, and documents never leave the computer; text that matches the sensitive patterns is blurred in exported screenshots; typed characters are never stored; the app runs without administrator rights; updates install only files from this project's GitHub release whose SHA256 matches the release's checksum list; every release file can be traced to the commit and workflow that built it.
- **Cannot expect:** that every secret on screen is found (OCR can miss small, stylized, or partly hidden text, so review each step before sharing); protection of the unblurred copies, which are kept on purpose and are only as safe as the folder they are in; protection from someone who already controls the computer or the signed-in account; security fixes for releases older than the latest.

## Trust Boundaries

| Boundary | What crosses it | How it is checked |
|---|---|---|
| Files opened by the user into the app | Videos, `steps.json`, `<recording>.events.json` | Parsed as data only (FFmpeg, Python's `json`), never executed; blur boxes are clamped to the frame |
| The app to helper programs | Command lines for FFmpeg, Tesseract, Pandoc, browsers, VLC | Started with argument lists, never through a shell, so file names cannot inject commands |
| The app to the network | Update check and Update Now | HTTPS only, certificate verification on, fixed hosts and file names, SHA256 check before anything runs |
| Contributors to the repository | Pull requests | No secrets and a read-only token for pull request runs; ruleset on `main`; required tests, CodeQL, DCO, and dependency review |
| The repository to users | Release files and package repositories | Built only by workflows from `main`; checksums, build provenance, SBOM, signed apt and dnf repositories |

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

## Assurance Case

Why the security requirements above are met:

1. **The threat model is written down and kept current:** the assets, attack surface, and threats are listed on this page, which is reviewed before each feature release.
2. **Trust boundaries are known and each has a check:** see the table above. Untrusted data never reaches a shell, an `eval`, or a deserializer that can run code.
3. **Secure design principles are applied:**
   - Least privilege: runs as the user; release jobs are the only jobs with write access or secrets.
   - Secure defaults: no network use beyond the update check; key notes can be turned off by policy.
   - Economy of mechanism: the Python standard library only, no plugin system, no listener.
   - Complete mediation: every update download is checked by host, file name, and hash.
   - Separation of duties is the one principle a single maintainer cannot fully apply; required automated checks stand in for a second reviewer.
4. **Common weaknesses are countered**, with tests where they apply:

| Weakness | Where it could happen | Countered by |
|---|---|---|
| CWE-78 OS command injection | Starting FFmpeg and other helpers | Argument lists, no shell (checked by CodeQL) |
| CWE-22 Path traversal | Update downloads | Fixed file name pattern; unexpected names refused (fixed in 1.35.1, tested) |
| CWE-79 and CWE-74 Injection into exports | Captions and labels in HTML, Word, PowerPoint | HTML, Markdown, and XML escaping (fixed in 1.35.1, tested) |
| CWE-494 Download of code without integrity check | Update Now | SHA256 against the release's checksum list before running |
| CWE-295 Improper certificate validation | Update check | Python's default HTTPS verification, never disabled |
| CWE-200 and CWE-359 Exposure of sensitive information | Screenshots and exports | Automatic blur, key names only, unblurred copies kept apart with a warning |
| CWE-732 Incorrect permission assignment | Install folder | Program Files permissions; the install script removes inherited write access (fixed in 1.35.1) |
| CWE-829 and supply chain | GitHub Actions | Third-party actions pinned to a commit, Dependabot, dependency review, Scorecard |

5. **The checks keep running:** CodeQL, Ruff, the test suite (80% statement coverage or more), the dependency review, and Scorecard run on every change, and a finding blocks the merge as [SECURITY.md](../SECURITY.md) describes.
