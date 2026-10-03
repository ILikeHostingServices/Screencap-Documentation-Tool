SECURITY.md v1.0.0 (Last Rev: 2026-10-03)

# Security Policy

## Supported Versions

Only the latest release (the one marked **Latest** on the Releases page) gets security fixes. Update by pasting the Quick Start command from `README.md` again.

## Reporting A Vulnerability

Please report security problems privately, not in a public issue:

1. Open the repository's **Security** tab and click **Report a vulnerability**.
2. Describe the problem, the version (shown in the GUI footer or by `screencap.py --version`), and how to reproduce it.

Do not attach real recordings or screenshots: they can contain passwords, license keys, and internal hostnames. A synthetic example that shows the problem is enough.

This is a small, volunteer-maintained project. Reports are handled on a best-effort basis, usually within a few days, with no guaranteed response time.

## Scope

In scope: the tool's own code, its installers (`install.ps1`, `Install-Prerequisites.ps1`, `install.sh`), and its GitHub workflows. Examples: the installer downloading something it should not, blurred text being recoverable from an exported document, or sensitive files ending up somewhere other than the output folder.

Out of scope: vulnerabilities in FFmpeg, Python, Tesseract, Pandoc, VLC, or a browser. Report those to their own projects; the tool picks up their fixes when you update them.
