SECURITY.md v1.2.0 (Last Rev: 2026-10-17)

# Security Policy

## Supported Versions

Only the latest release (the one marked **Latest** on the Releases page) gets security fixes and support. A release stops getting security updates the moment the next release is published, so there is no separate end-of-life date to track. Update with **Help > Check for Updates** (Windows installer), your package manager, or the install command from `README.md`.

To check that a download is genuine (its checksum, and that it was built by this repository's release workflow), see [Verifying A Download](docs/SECURITY_FOR_IT.md#verifying-a-download).

For what the app does on a computer, what it sends over the network, the administrator settings, and how to verify a download, see [ScreenCap Docs for IT and Security Teams](docs/SECURITY_FOR_IT.md).

## Reporting A Vulnerability

Please report security problems privately, not in a public issue:

1. Open the repository's **Security** tab and click **Report a vulnerability**.
2. Describe the problem, the version (shown in the GUI footer or by `screencap.py --version`), and how to reproduce it.

Do not attach real recordings or screenshots: they can contain passwords, license keys, and internal hostnames. A synthetic example that shows the problem is enough.

## What Happens Next

This is a small, volunteer-maintained project, and these are the timeframes it works to:

| Step | Timeframe |
|---|---|
| Acknowledge the report | Within 14 days |
| Confirm or rule out the problem, and agree a disclosure date with you | Within 30 days |
| Release a fix, or publish an advisory with a workaround | Within 90 days |

Confirmed vulnerabilities are published as [GitHub Security Advisories](https://github.com/ILikeHostingServices/Screencap-Documentation-Tool/security/advisories), with a CVE when one is assigned, and listed in the release notes of the version that fixes them. You are credited unless you ask not to be.

When a vulnerability in a component does not affect ScreenCap Docs (for example, a flaw in a part of a library the app never calls), that is published as a VEX statement in the advisory or the release notes, so scanners that flag it can be answered.

## Scope

In scope: the tool's own code, its installers (`install.ps1`, `Install-Prerequisites.ps1`, `install.sh`), and its GitHub workflows. Examples: the installer downloading something it should not, blurred text being recoverable from an exported document, or sensitive files ending up somewhere other than the output folder.

Out of scope: vulnerabilities in FFmpeg, Python, Tesseract, Pandoc, VLC, or a browser. Report those to their own projects; the tool picks up their fixes when you update them.

## Security Practices

**Secrets.** Signing keys and store tokens are stored only as GitHub Actions secrets, never in the repository, issues, or logs. Only release jobs that run from `main` can read them, and pull request runs get none. Each secret is the narrowest token the store offers, is changed when anyone with access leaves or a leak is suspected, and is deleted when no longer used. Contributors must never commit credentials, recordings, or screenshots of real systems; GitHub secret scanning checks every push.

**Dependency vulnerabilities (SCA).** Dependabot alerts and the dependency review check run on every pull request. A pull request that adds a dependency with a known vulnerability of high or critical severity cannot be merged. A known vulnerability in a dependency already in use is fixed (by updating, replacing, or removing it) before the next release when it is high or critical, and within 90 days otherwise, unless it does not affect the app; then a VEX statement is published as described above.

**Code scanning (SAST).** GitHub CodeQL scans the Python code and the workflows on every pull request. Findings of high or critical severity, and every security finding of error level, block the merge and must be fixed before the next release. Lower findings are fixed or dismissed with a written reason within 90 days. A finding is only dismissed as a false positive or as not exploitable, with the reason recorded in the alert.
