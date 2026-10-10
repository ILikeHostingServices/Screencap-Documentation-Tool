README.md v1.0.0 (Last Rev: 2026-10-10)

# ILikeHostingServices Homebrew Tap

Homebrew formulas for apps from [ILikeHostingServices](https://github.com/ILikeHostingServices).

## Screencap Documentation Tool

Turns screen recordings into step-by-step screenshot documentation. See the [project page](https://github.com/ILikeHostingServices/Screencap-Documentation-Tool).

```bash
brew install ilikehostingservices/tap/screencap-documentation-tool
```

Then start the GUI with `screencap-gui`, or add the app to Launchpad, Spotlight, and the Dock:

```bash
ln -sf "$(brew --prefix)/opt/screencap-documentation-tool/Screencap Documentation Tool.app" ~/Applications/
```

Optional extras: `brew install tesseract` (blur sensitive text automatically) and `brew install pandoc` (Word export).

Update with `brew update && brew upgrade screencap-documentation-tool`. Remove with `brew uninstall screencap-documentation-tool` (your recordings and output in `~/Documents/Screencap Documentation Tool` are kept).

No Apple Developer account or notarization is involved: Homebrew builds the app on your Mac from the published source code, so macOS does not quarantine it.

## How This Tap Is Updated

`.github/workflows/update.yml` checks the project's latest release every day (and can be run by hand). When there is a new version, it writes the formula with the project's own generator (`packaging/homebrew/make_formula.py` at that release), installs and tests it on a real Mac (`packaging/homebrew/test_formula.sh`), and only then commits it here.
