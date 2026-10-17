CONTRIBUTING.md v1.1.0 (Last Rev: 2026-10-17)

# Contributing

Thank you for helping with ScreenCap Docs. Bug reports, ideas, and pull requests are all welcome.

## Reporting Bugs And Ideas

- Use **Help > Report a Problem...** or **Suggest an Idea...** in the app, or [open an issue](https://github.com/ILikeHostingServices/Screencap-Documentation-Tool/issues/new/choose). Include the details from **Help > About > Copy Details**.
- Never attach real recordings or screenshots: they can show passwords, license keys, and internal names. A synthetic example is enough.
- Report security problems privately, as described in [SECURITY.md](SECURITY.md), never in a public issue.

## Proposing A Change

1. For anything larger than a small fix, open an issue first so the approach can be agreed before you spend time on it.
2. Fork the repository, make a branch, and keep each pull request to one change.
3. Sign off every commit (see below), run the checks below, then open a pull request that says what changed and why.

Every pull request is tested on Windows and Linux by GitHub Actions, scanned by CodeQL and the dependency review, and the packages are built and installed on several systems. A pull request is merged only when all of that passes. Who decides, and who has access to what, is described in [GOVERNANCE.md](GOVERNANCE.md).

## Signing Off Your Commits

Every commit must carry a `Signed-off-by:` line with your name and email, which certifies the [Developer Certificate of Origin](https://developercertificate.org/): that you wrote the change, or otherwise have the right to submit it under the project's license. Add it with `git commit -s`. The **DCO** check fails a pull request that has a commit without it; fix that with `git commit --amend -s` (one commit) or `git rebase --signoff main` (several), then push again. Commits from bots such as Dependabot are exempt.

## What A Change Must Include

- **Tests.** Every major change, new feature, and bug fix comes with tests in `tests/` that fail without the change and pass with it. Changes to the installers or packages come with a check in the matching workflow under `.github/workflows/`.
- **Documentation.** Update `README.md` for anything a person using the app or an administrator would notice.
- **Headers.** Each file starts with its name, date, and version. Bump the file's own version when you change it (patch for fixes, minor for features).
- **Writing rules.** Follow [docs/BRANDING.md](docs/BRANDING.md): the name is "ScreenCap Docs", plain US English, sentence case, dates as YYYY-MM-DD, versions with three parts, and no em or en dashes.
- **Dependencies.** The app uses only the Python standard library, so it installs on locked-down PCs without extra packages. A new dependency (a Python package, a helper program, or a GitHub Action) needs a reason in the pull request, must be free and open source, actively maintained, and installable from the standard source (PyPI, winget, the distribution's packages, or the GitHub Marketplace). Third-party GitHub Actions are pinned to a full commit SHA and kept up to date by Dependabot. Helper programs are installed by the installers and listed in the README; the Windows build's components are listed in the SBOM attached to each release.
- **No secrets or personal data.** No keys, tokens, real email addresses, recordings, or screenshots of real systems in commits.

The maintainer writes the release notes and `CHANGELOG.md` entry when a release is cut.

## Running From Source And Building

You need Python 3.8 or newer (with Tkinter, included in the Windows and macOS installers from python.org; `python3-tk` on Debian and Ubuntu) and FFmpeg on the PATH. Tesseract OCR, Pandoc, Edge or Chrome, and VLC are optional; see the README Quick Start. No Python packages are needed to run the app.

```bash
git clone https://github.com/ILikeHostingServices/Screencap-Documentation-Tool.git
cd Screencap-Documentation-Tool
python screencap_gui.pyw          # the GUI
python screencap.py --help        # the command line tool
```

The release files are built by the workflows in `.github/workflows/`, which are the exact build instructions:

| Build | Tools | Workflow |
|---|---|---|
| Windows app and setup | PyInstaller 6 (`python -m PyInstaller packaging/screencap.spec`), then Inno Setup 6 (`ISCC packaging/installer.iss`) | `build-windows.yml` |
| .deb and .rpm | nfpm (`packaging/linux/build_packages.py`) | `build-linux.yml` |
| Arch package, snap | makepkg (`packaging/aur/`), snapcraft (`snap/snapcraft.yaml`) | `build-linux.yml` |
| Homebrew formula | `packaging/homebrew/make_formula.py` | `build-macos.yml` |

## Running The Checks

The same checks run in GitHub Actions on every push and pull request (`ci.yml`), the packages are built and installed on every pull request and release (`build-windows.yml`, `build-linux.yml`, `build-macos.yml`), and the install scripts are tested when they change and every Monday (`installers.yml`). Run them locally before opening a pull request:

```bash
python -m pip install pyflakes
python -m pyflakes *.py *.pyw tests/*.py assets/*.py
python -m unittest discover -s tests -v
```

FFmpeg must be on the PATH for the processing tests. On Linux, run the tests under `xvfb-run -a` so the GUI tests have a display. `shellcheck install.sh` checks the shell installer.

## License

By contributing, you agree that your work is released under the project's [MIT License](LICENSE).
