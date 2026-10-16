CONTRIBUTING.md v1.0.0 (Last Rev: 2026-10-16)

# Contributing

Thank you for helping with ScreenCap Docs. Bug reports, ideas, and pull requests are all welcome.

## Reporting Bugs And Ideas

- Use **Help > Report a Problem...** or **Suggest an Idea...** in the app, or [open an issue](https://github.com/ILikeHostingServices/Screencap-Documentation-Tool/issues/new/choose). Include the details from **Help > About > Copy Details**.
- Never attach real recordings or screenshots: they can show passwords, license keys, and internal names. A synthetic example is enough.
- Report security problems privately, as described in [SECURITY.md](SECURITY.md), never in a public issue.

## Proposing A Change

1. For anything larger than a small fix, open an issue first so the approach can be agreed before you spend time on it.
2. Fork the repository, make a branch, and keep each pull request to one change.
3. Run the checks below, then open a pull request that says what changed and why.

Every pull request is tested on Windows and Linux by GitHub Actions, and the packages are built and installed on several systems. A pull request is merged only when all of that passes.

## What A Change Must Include

- **Tests.** New features and bug fixes come with tests in `tests/` that fail without the change and pass with it. Changes to the installers or packages come with a check in the matching workflow under `.github/workflows/`.
- **Documentation.** Update `README.md` for anything a person using the app or an administrator would notice.
- **Headers.** Each file starts with its name, date, and version. Bump the file's own version when you change it (patch for fixes, minor for features).
- **Writing rules.** Follow [docs/BRANDING.md](docs/BRANDING.md): the name is "ScreenCap Docs", plain US English, sentence case, dates as YYYY-MM-DD, versions with three parts, and no em or en dashes.
- **No secrets or personal data.** No keys, tokens, real email addresses, recordings, or screenshots of real systems in commits.

The maintainer writes the release notes and `CHANGELOG.md` entry when a release is cut.

## Running The Checks

```bash
python -m pip install pyflakes
python -m pyflakes *.py *.pyw tests/*.py assets/*.py
python -m unittest discover -s tests -v
```

FFmpeg must be on the PATH for the processing tests. On Linux, run the tests under `xvfb-run -a` so the GUI tests have a display. `shellcheck install.sh` checks the shell installer.

## License

By contributing, you agree that your work is released under the project's [MIT License](LICENSE).
