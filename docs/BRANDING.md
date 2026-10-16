BRANDING.md v1.0.0 (Last Rev: 2026-10-16)

# Branding

The core brand rules for ScreenCap Docs, so the app, installer, README, release notes, website, and store listings stay consistent. The maintainers keep a fuller visual guide (components, tokens, artwork drafts) privately; this file holds everything needed to work in this repository.

## The name

- Write **ScreenCap Docs**: capital S, C, and D, one space. Never "Screencap Docs", "ScreenCapDocs", "SCD", or "the tool" in headings.
- "Formerly Screencap Documentation Tool" only where someone may search for the old name: store descriptions, the About window, migration notes.
- The publisher is **ILHS** in running text and **ILikeHostingServices** for the GitHub organization.
- Identifiers that must never change (they keep upgrades working): the Windows AppId `{39ABD99E-CAC0-48C0-B602-EF8172627F70}` and the taskbar app ID `ILHS.ScreencapDocumentationTool.GUI`. The `screencap` and `screencap-gui` commands stay as they are.

## Positioning

- **One line:** A free Steps Recorder replacement for Windows, Linux, and macOS.
- **Tagline:** Record a task once. Get the how-to guide.
- **Summary (under 80 characters):** Free Steps Recorder replacement: record a task, get a step-by-step guide
- **One sentence:** Record a task and get a step-by-step guide: screenshots with click rings, draft captions, auto-blurred secrets, and HTML, Word, PDF, or PowerPoint export.

## Voice

- Plain and direct, active voice, second person ("you"). US English, sentence case for headings and buttons.
- Use the app's own words: step, step editor, click ring, caption, Recording window, Record, Stop, Discard, Export. Quote UI labels: click "Next".
- No em or en dashes, no emoji, no exclamation marks, no hype words.
- Dates YYYY-MM-DD. Versions always have three parts (1.35.0).
- Buttons say what happens ("Download for Windows (x64)", "Save changes"). Errors say what went wrong, why, and what to do next; never just "An error occurred".

## Color

| Name | Light | Dark | Use |
|---|---|---|---|
| brand-blue | `#2563eb` | `#6ea8fe` | The brand: primary buttons, links, export accent, the icon |
| click-red | `#e53935` | `#ff6b66` | Only what the product draws: click rings, change boxes, arrows, markers, the recording dot |
| red-text | `#c62828` | `#ff8a85` | Warning and error text (click-red is too light for text) |
| capture-amber | `#f59e0b` | `#f5a524` | Icon accent; fills and marks only, never text on a light background |
| screen-navy | `#0f1e3d` | `#22355f` | The icon's screen; dark brand fields |
| ink | `#17202b` | `#e8edf3` | Body text |
| muted | `#566273` | `#9aa7b8` | Secondary text, timestamps |
| paper | `#f6f7f9` | `#10151c` | Page background |
| sheet | `#ffffff` | `#18202a` | Raised surfaces: frames, tables, command lines |
| rule | `#d9dee6` | `#2a3542` | Hairline borders |

Every text color above meets 4.5:1 contrast on paper and sheet in both themes. Status always has a word, never color alone.

**Being retired** (replace as each file is next changed): the app accent `#0f6cbd` / `#4ca0e0` in `theme.py` (use brand-blue) and the HTML export warning text `#8e1b17` in `export.py` (use red-text).

## Type

- **Website and marketing:** Familjen Grotesk 700 for headings, Source Sans 3 for text, JetBrains Mono for commands, versions, and labels (Google Fonts, with system fallbacks).
- **The app:** the system font (Segoe UI on Windows). No web fonts in the app.
- **Exports:** Segoe UI, then Arial and Helvetica.

## Icon

- The icon is built by `assets/make_icon.py`, which writes `assets/icon.ico` and `assets/icon.png`. Change the artwork there, never by hand.
- Never recolor, outline, rotate, or redraw it. Clear space: a quarter of its width on every side. Minimum 16 px.
- There is no separate wordmark: set "ScreenCap Docs" in the heading font beside the icon.

## Screenshots

- Screenshots in `docs/screenshots/` are made by `packaging/screenshots/make_screenshots.sh` for every feature release.
- Marketing screenshots (website, stores) come from a clean Windows 11 VM at 1920 x 1080 and 100% scaling, light theme, a plain wallpaper, the real current release, and a real open-source app as the example task. No real names, emails, or keys: use `alex.morgan@example.com` and "Northwind Traders".

## Release notes

- `.github/releases/vX.Y.Z.md`: first line is the title (what matters most, no version, no period), then bold section lines with bullets: the headline feature, **New**, **Improved**, **Fixed**, **Removed** (leave out empty ones).
- Bullets describe what the person can now do or what no longer goes wrong. Start with the thing, not "Added" or "We".

## Exported guides

Guides people export belong to them: their title, logo, and template come first. ScreenCap Docs appears at most as one small "Created with ScreenCap Docs" line and in the document's Application property.

## Brand check before each release

1. The name is "ScreenCap Docs" in all new text (notes, app strings, installer, store text).
2. Release notes follow the format above.
3. New UI text follows the voice rules.
4. New screenshots follow the screenshot rules.
5. Store descriptions still match the positioning above.
