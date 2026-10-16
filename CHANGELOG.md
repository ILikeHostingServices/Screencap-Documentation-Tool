CHANGELOG.md v1.40.0 (Last Rev: 2026-10-16)

# Changelog

Every release of ScreenCap Docs (called Screencap Documentation Tool until v1.35.0), newest first. Each version is a git tag (Major.Minor.Patch), and the same notes appear on the GitHub Releases page.

## v1.35.0 - New name: ScreenCap Docs (2026-10-16)

**New name: ScreenCap Docs**
- The app is now called **ScreenCap Docs** (formerly Screencap Documentation Tool): in the window title, the About window, the Start Menu and desktop shortcuts, Apps & Features, the installer, the Linux application menu and software centers, the Snap Store, the Homebrew app, and exported documents.
- Only the shown name changed. The repository, the winget package `ILHS.ScreencapDocumentationTool`, the Linux and Homebrew package names, the Windows install folder, the program file `Screencap Documentation Tool.exe`, and the `screencap` and `screencap-gui` commands keep their names, so updates, scripts, taskbar pins, and application allow-lists keep working.
- Updating replaces the old Start Menu and desktop shortcuts with ones under the new name. Settings, presets, and chosen folders are kept.
- New installs keep recordings and output in `Documents\ScreenCap Docs`. A `Documents\Screencap Documentation Tool` folder from an earlier version keeps being used.
- Homebrew: the app is now `ScreenCap Docs.app`. Run the `ln -sf` command from the README again, and remove the old link with `rm ~/Applications/"Screencap Documentation Tool.app"`.

**Fixed**
- The README no longer says the Arch package is on the AUR yet: it is published there as soon as the AUR reopens new account sign-ups. Until then, install the `.pkg.tar.zst` from the release with `sudo pacman -U`.

## v1.34.1 - Installer keeps the install mode (2026-10-15)

**Fixed**
- The Windows installer no longer asks "Install for all users or for me only?" when the tool is already installed: it updates the installed copy the same way (for everyone, or for you only). To switch, run the installer with `/ALLUSERS` or `/CURRENTUSER`.
- A silent update without a scope (for example from a deployment tool) now updates a copy installed for one user in place, instead of installing a second copy for everyone.

## v1.34.0 - Update Now (2026-10-15)

**New**
- **Update Now:** on a copy installed with the Windows installer, the update window has an **Update Now** button. It downloads the new installer for your PC (x64 or ARM64), checks it against the release's `SHA256SUMS.txt`, closes the app, installs the update silently for the same scope (just you, or everyone on the PC), and opens the app again. Settings, presets, folders, and recordings are kept.
- A download that does not match the checksum list is deleted and never run, and only this project's own GitHub release files are downloaded. A copy installed for everyone still needs administrator rights, so Windows shows its permission prompt.
- The update window shows the release notes, with **Remind Me Later** and **Skip This Version**. For other installs it shows the command to copy (Homebrew, apt, dnf, the AUR, snap) or opens the download (the portable zip).
- `SCREENCAP_NO_UPDATE_CHECK=1` turns Update Now off along with the update check, for PCs where updates are deployed centrally.

**Testing**
- On real Windows machines (x64 and ARM64), for one user and for everyone: v1.33.0 is installed, the new updater downloads this release from a local test server, checks it, installs it silently, and the updated app opens again with the folders kept.

## v1.33.0 - Faster processing and fixes (2026-10-14)

**Faster**
- Processing is about three times faster on a 4-core PC: a 3-minute, 1080p recording with 40 steps now takes 27 seconds instead of 81, and a recording made with the built-in recorder 4 seconds instead of 11. The results are the same, screenshot for screenshot.
- Saving the screenshots, reading the clicked words for captions, scanning for sensitive text, and rendering now run on all CPU cores (up to 8 at once) instead of one screenshot at a time. **Save Changes** in the step editor is faster for the same reason.
- An unblurred copy of a screenshot with nothing to blur is now copied instead of being rendered a second time, and screenshots are compared row by row, skipping the rows that did not change.
- `SCREENCAP_WORKERS` (an environment variable) sets how many cores to use; `SCREENCAP_WORKERS=1` does everything one at a time.

**Fixed**
- Tesseract OCR could stall for minutes on a busy PC: its own threads compete for the CPU with each other. It now runs one thread per scan, which is also faster on its own.
- A change made in the step editor while **Save Changes** was still running was marked as saved even though it was not in the saved files, so it could be lost on closing. It now stays marked as unsaved, and the status bar says to save again.
- If FFmpeg could not be started for a recording, the tool kept reading clicks and keys in the background until it was closed.
- A Word or PDF export that hangs now ends with a clear message ("did not finish within 3 minutes") instead of an internal error.
- `screencap.py --help` mentions `--record`.

## v1.32.0 - PowerPoint export (2026-10-14)

**New**
- **Export to PowerPoint:** **PowerPoint** in the Export box (command line: `--export pptx`) saves the steps as a widescreen presentation for training sessions and handovers: a title slide with the title, version, date, author, and logo, then one slide per step with "Step N", the screenshot as large as fits, and the caption under it.
- What was said during a step (Captions From Narration) goes in that slide's speaker notes, so the presenter has the script; screenshots keep their alt text; a step with an animated clip gets one more slide where the clip plays.
- The logo (PNG, JPG, or GIF) is on every slide. The Unblurred copy option works as for the other exports and puts the warning on the title slide.
- No other program is needed: the presentation is written by the tool itself (`pptxwriter.py`, Python standard library only) and opens in PowerPoint, Keynote, LibreOffice Impress, and Google Slides.

**Testing**
- Every exported presentation in the tests is checked with Microsoft's Open XML SDK (the rules Office itself uses, for Office 2007, 2016, and Microsoft 365) and read back with python-pptx, on Windows and Linux.

**Changed**
- The screenshots in the README and the software center listing show the PowerPoint button, and a new one shows an exported presentation. From now on, every feature release updates the screenshots.

## v1.31.2 - Better click captions, and screenshots in the store listings (2026-10-13)

**Fixed**
- First-draft captions name the clicked button even when the mouse pointer covers part of its words: the same place is read a moment before the click too, and the fuller reading is used when it holds the shorter one (so `Click "Ne".` is now `Click "Next".`).
- A checkbox or option button clicked on its box gets its label from the words to the right of it (`Click "Create a desktop shortcut".`), instead of "the marked spot".
- Text box borders and the text cursor, which OCR reads as `|` or `I`, no longer hide the label of an empty text box (`Click next to "Product key"`), and the border between two buttons no longer joins their words (`Click "Back | Next"`).

**New**
- Screenshots of the app in the README and in the Linux software center listing (GNOME Software, KDE Discover), plus a Snap Store button and download and Homebrew badges at the top of the README.
- `packaging/screenshots/make_screenshots.sh` makes the screenshots again after interface changes: it records a made-up setup wizard with the built-in recorder on a virtual display, so the click rings, blurring, and captions in the pictures are the tool's own.

## v1.31.1 - Snap Store fix (2026-10-13)

**Fixed**
- The snap of v1.31.0 was held for manual review by the Snap Store, which asks for the audio-playback permission together with the microphone (audio-record) permission the recorder added. The snap now has both, so it is published to the Snap Store again. Nothing else changed; the other downloads are the same as v1.31.0.

## v1.31.0 - Built-in screen recorder (2026-10-13)

**New**
- **Record:** a built-in screen recorder, like Windows Steps Recorder but as a video. Click **Record** above the list of recordings (or **File > Record Screen...**, Ctrl+R), choose a microphone if you want to narrate, and click **Start Recording**. The main window minimizes and a small **Recording** window shows a timer, **Stop**, and **Discard**. When you click **Stop**, the recording is saved in the Recordings folder and the screenshots are made straight away.
- **Clicks and keys are noted while recording:** where and when you click (double-clicks, right-clicks, and drags too) and keys such as Enter, Tab, Esc, arrows, function keys, and shortcuts like Ctrl+S. **Typed text is never saved:** letters and digits only count as "type the text". They are kept next to the recording in `<name>.events.json`.
- **Click rings:** each click gets a red ring on its step's screenshot, and a drag gets an arrow. They are ordinary annotations, so **Annotate > Edit or Remove** takes one off.
- **First-draft captions:** empty captions are filled from the clicks and keys, for example `Click "Next".` or `Click next to "User name", type the text, then press Tab.` The words of the clicked button are read from the recording at the moment of the click with Tesseract OCR; words that look sensitive (the same patterns that are blurred) are left out. Captions you type are never changed, and Captions From Narration replaces a draft you have not edited.
- Command line: `--record` (stop with Enter, or after `--record-seconds N`), `--microphone NAME` and `--list-microphones`, `--no-key-log`, `--ignore-clicks`, and `--no-click-marks`.

**By system**
- Windows: all monitors are recorded, and the Recording window is left out of the video.
- macOS: the main display is recorded. Allow the app (or Terminal) under System Settings > Privacy & Security > Screen Recording, and Input Monitoring for keys.
- Linux: X11 sessions. Wayland desktops do not let other programs record the screen; the app explains this and suggests the desktop's own recorder. In the snap, connect the microphone once with `sudo snap connect screencap-documentation-tool:audio-record`.

**Changed**
- The Linux packages recommend libXtst, which lets the recorder see every click, even very short ones. The snap includes it.

## v1.30.0 - Animated clips of single steps (2026-10-12)

**New**
- **Animated GIF clips:** for steps a still picture cannot show well (dragging, a menu that opens on hover, a slider), tick **Highlight > Animated Clip of This Step (GIF)** in the Steps tab and save. The clip runs from just before the screen changes until the next screen has settled (at most 6 seconds) and appears under the step's screenshot in `steps.md` and in HTML and Word exports. **Open > Open Animated Clip** opens it.
- Clips are made from the original recording, cropped like the screenshot and blurred with the blur boxes of the step and the next one. They are only made again when something they depend on changes, so reordering steps does not redo them.

**Changed**
- The README, the Snap Store and winget descriptions, and the Linux software center listing now describe the tool as a free replacement for Windows Steps Recorder (`psr.exe`), which Microsoft deprecated in 2023, with a comparison table under "Coming From Steps Recorder" in the README.

**Fixed**
- The Steps tab could stop with "int() argument must be a string..." when the window was resized on Linux systems whose Tk returns option values as objects (seen on Debian 12 and Raspberry Pi OS). This affected the toolbars that wrap onto more rows, added in v1.26.0.

**Notes**
- PDF exports show a clip's first frame. Before sharing, play the clip of any screen with sensitive information: it also shows the moments between the two screenshots.

## v1.29.0 - Alt text on every screenshot (2026-10-12)

**New**
- Every screenshot now has **alt text** in `steps.md` and in HTML, PDF, and Word exports: the step number, its caption, and the text of any labels drawn on it (for example "Step 3: Click Next. Labels on the screenshot: "Next""). Screen readers read it aloud, and it is shown when a picture cannot be. This helps documents meet accessibility requirements such as Section 508 and WCAG.
- Steps without a caption get "Screenshot of step N", so no picture is left without a description.

**Notes**
- In Word, the alt text is stored as the picture's description (right-click the picture > **View Alt Text**) and is not printed a second time as a caption.

## v1.28.0 - Company logo and Word template for exports (2026-10-12)

**New**
- **Logo and Template...** in the Steps tab's Export box: choose a **company logo** (PNG, JPG, GIF, or SVG) that goes at the top of HTML, PDF, and Word exports, and a **Word template** whose styles (fonts, colors, spacing), margins, and page header and footer are used for Word exports. Both are remembered for every export until cleared.
- **Create Starter Template...** saves the standard Word template to edit in Word: change its styles, put your logo or a confidentiality note in the page header or footer, save it, and choose it.
- Command line: `--logo`, `--word-template`, and `--create-word-template FILE`.

**Notes**
- With a logo, the title block of a Word export is written with Word's Title, Subtitle, Author, and Date styles below the logo, so a template's styling of those applies too.

## v1.27.0 - Zoomed inset of small changes (2026-10-12)

**New**
- **Zoomed inset:** a magnified copy (up to 2.5 times) of a small change, such as a ticked checkbox or a short field, in the corner of the screenshot farthest from it. It stays readable when a document shows the screenshot small. Switch it on for the whole recording with **Zoomed inset** (top right of the Steps tab), for one step in the new **Highlight** menu, or with `--zoom` on the command line. Steps where the change is already big enough to read get no inset.
- The inset is made from the blurred screenshot, so it never shows anything that is blurred, and it stays inside the crop. Annotations are drawn on top of it.

**Changed**
- Steps tab: **Highlight this step** is now **Highlight > Red Box on This Step**, next to the new **Zoomed Inset on This Step**, and **Captions From Narration** moved next to **Caption**. With the shorter "removed" note above the step list, this leaves more room for the picture, which matters most on laptops with display scaling.

## v1.26.0 - Annotations: arrows, numbered markers, and text labels (2026-10-12)

**New**
- **Annotate** menu in the Steps tab: draw **arrows**, **numbered markers** (1, 2, 3, ...), and **text labels** on any screenshot, so readers see exactly which button to click or which field to fill in. Drag to draw an arrow; click to place a number or a label. **Edit or Remove** changes a label's text or a marker's number, or removes it, and **Clear Annotations on This Step** removes them all.
- Annotations are red with a thin white edge, so they stand out on light and dark screens, and their size follows the recording's resolution.
- They are drawn on top of everything else, including blurred areas, so they never uncover what is blurred, and they follow the crop. The original frames are never changed: annotations can be edited or removed at any time.
- Exports (HTML, Word, PDF) and `steps.md` show the annotated screenshots.

**Notes**
- Label text and marker numbers use a bold font already on your system (Segoe UI on Windows, Arial on macOS, DejaVu Sans or another sans-serif font on Linux). Set `SCREENCAP_FONT` to a `.ttf` file to use another one.
- The Linux .deb now recommends `fonts-dejavu-core`, and the snap includes DejaVu Sans.

**Fixed**
- In the Steps tab, the toolbar above the picture and the buttons below it no longer cut off **Highlight this step** and **Discard** when the window is not wide enough; they wrap onto a second row.

## v1.25.1 - Accurate update summary in the Windows installer (2026-10-11)

**Fixed**
- When updating, the installer's **Ready to Update** page listed "Additional tasks: Create a desktop shortcut" and "Also install Tesseract OCR and Pandoc with winget", because it re-applies the choices made at the last install. It now says what is kept from the current installation (Start Menu and desktop shortcuts, settings and saved presets) and lists only what will really be installed.
- The "Also install Tesseract OCR and Pandoc with winget" option is now offered, and run, only while one of them is missing, like the FFmpeg option. An update no longer runs winget again for programs that are already installed.
- The Ready page now also shows the recordings and output folders that will be used.

## v1.25.0 - ARM support: Raspberry Pi and Windows on ARM (2026-10-11)

**New**
- **Windows on ARM:** native ARM64 builds, `Screencap-Documentation-Tool-vX.Y.Z-windows-arm64-setup.exe` and `...-windows-arm64-portable.zip`, for Snapdragon and other ARM laptops and tablets. They are built and tested on a real Windows 11 on ARM machine. The x64 files keep working on Windows 11 on ARM through Windows' x64 emulation, and that is tested too. winget (once listed) and **Help > Check for Updates** choose the ARM64 download on ARM PCs, also when the x64 copy is the one installed. Either installer updates a copy installed by the other.
- **Raspberry Pi and other ARM boards:**
  - The **snap** is now built for 64-bit ARM as well (`_arm64.snap`), so `sudo snap install screencap-documentation-tool` works on 64-bit Raspberry Pi OS and other arm64 Linux.
  - The **.deb** works on both 64-bit and 32-bit Raspberry Pi OS (it is not tied to a processor type), and is now tested on Debian 12 and 13 and Ubuntu 24.04 for arm64, and on Debian 12 and 13 for 32-bit ARM (armhf).

**Notes**
- On Windows on ARM, FFmpeg and Tesseract OCR installed with winget are x64 programs that run under emulation; everything works, a little slower. Captions From Narration is not available there.
- There is no 32-bit ARM snap: GitHub has no 32-bit ARM machines to test it on, and an untested build is not published. 32-bit Raspberry Pi OS uses the `.deb`.

**Changed**
- `SHA256SUMS.txt` now lists all Windows files (x64 and arm64).

## v1.24.1 - Cleaner installer pages (2026-10-11)

**Fixed**
- **Recordings and Output Folders** page in the Windows installer: the two choices are now short ("Use the default folders (recommended)" and "Choose my own folders"), and the default folders are listed underneath on lines of their own, instead of long paths wrapping in the middle of the first choice.
- Clearer wording on the installer's folder pages, the options page ("required, and not found on this PC"), and the error shown when an older copy cannot be removed.
- Running setup over the same version now says **Ready to Reinstall** with a **Reinstall** button, instead of "update"; the last page ends with "Click Finish to close Setup."
- The text on the **Ready to Update** page was cut off after two lines; it is shorter now and fits.
- The Windows build now drives the real installer and saves a screenshot of every page, and checks that every text on every page fits its space, so layout problems are caught on each change.

## v1.24.0 - Choose the recordings and output folders in the Windows installer (2026-10-11)

**New**
- The Windows installer has a **Recordings and Output Folders** page: keep the defaults, `source` and `output` inside the install folder (`C:\Program Files\ILHS\Screencap-Documentation-Tool\source` and `...\output` for an all-users install, which setup makes writable for every user), or choose your own folders. The app uses them from its next start, replacing the folders it had remembered; changing them later in the app works as before.
- Updating keeps the folders chosen before, so the page is skipped; updating from v1.23.2 or earlier asks once. Silent installs take `/SOURCEDIR="..."` and `/OUTPUTDIR="..."`; a silent update (for example through winget) never changes the folders the app uses.
- Uninstalling removes the default folders only when they are empty, and never removes folders you chose or any files in them.
- The command line program (`screencap.exe`) uses the installer's folders as its default `--source` and `--output`.

**Changed**
- The maintainer notes (owner to-do list and release runbook) moved out of the public repository.
- Snap Store publishing is set up: from this release the snap is also uploaded to the Snap Store, as well as attached to the release.

## v1.23.2 - New winget package ID (2026-10-10)

**Changed**
- The winget package ID is now `ILHS.ScreencapDocumentationTool`, matching the organization's naming for its apps (the same ILHS prefix as the install folder and the Windows taskbar ID). Once Microsoft approves the listing, install with `winget install ILHS.ScreencapDocumentationTool`. The first submission under the old ID was never listed, so nobody needs to change anything.
- **Help > Check for Updates** suggests the new winget ID for winget installs.

## v1.23.1 - Windows installer updates in place (2026-10-10)

**Improved**
- **Windows installer recognizes an installed copy.** Running a newer installer over an existing installation now updates it: setup goes straight to **Ready to Update** ("Setup is ready to update Screencap Documentation Tool from v1.23.0 to v1.23.1"), with an **Update** button, and skips the license, folder, and options pages (the options page still appears if FFmpeg is missing, so it can be installed). The desktop shortcut choice from last time is kept.
- The **Folder Exists** question ("The folder ... already exists. Would you like to install to that folder anyway?") no longer appears.
- The Windows build now also tests running setup over an installed copy, for one user and for all users, and that the update is detected when upgrading from v1.16.0.

## v1.23.0 - Cleaner About, Advanced Settings, and menu bar (2026-10-10)

**Improved**
- **Menu bar follows the theme.** On Windows the File, View, and Help menus were on a white bar even in the dark theme, because the native Windows menu bar cannot change color. The menu bar is now part of the window and matches the light or dark theme. Alt+F, Alt+V, and Alt+H open the menus. (macOS keeps its system menu bar at the top of the screen.)
- **About window:** laid out in sections. **System** lists the version, install type (in words, for example "Windows installer"), operating system, Python, and Tk, one per line. **Programs** lists each helper program on its own line with a green check mark when it is installed or a red cross when it is not, and what it is used for. The links (Project on GitHub, Release Notes, License, Privacy) are evenly spaced. **Copy Details** copies the same information, one program per line.
- **Update status in the status bar:** the right end of the status bar shows the version and whether it is the latest: **Up to date** (green), **Update available** (orange; click to see it and download), or **Check for updates** (click to check). The update result no longer replaces the status message on the left.
- **Advanced Settings window:** grouped into **Timing**, **Detection**, **Output**, and **Run**, with clearer labels, the unit after each box (seconds, percent, pixels), and all the boxes lined up. **Reset Defaults** is now **Reset to Defaults**.
- **Preset names in title case:** Installer Wizard, General Desktop Use, Web Console, Terminal / Command Line, Remote Desktop / VM Console, Forms and Spreadsheets, Slideshow / Presentation, Video Meeting / Screen Share, and Fast Clicking. Saved settings and scripts that use the old names keep working: preset names are not case-sensitive (`--preset "web console"` still works).
- **Help window:** topic titles in title case (Getting Started, Editing Steps, Blurring Sensitive Information, Keyboard Shortcuts), with more room between topics in the list.
- Buttons and links use title case throughout: **Advanced Settings...**, **Save as Preset...**, **Delete Preset**.

## v1.22.0 - Homebrew for macOS (2026-10-10)

**New**
- macOS: install with Homebrew, `brew install ilikehostingservices/tap/screencap-documentation-tool`, once the tap repository is live. It installs the tool with Homebrew's own Python, Tkinter, and FFmpeg, adds the `screencap-gui` and `screencap` commands, and builds a `Screencap Documentation Tool.app` you can link into `~/Applications` for Launchpad, Spotlight, and the Dock.
- No Apple Developer account or notarization is needed: Homebrew builds the app on your Mac from the published source, so macOS does not block it.
- Installed with Homebrew, the default folders are in `~/Documents/Screencap Documentation Tool`, and **Help > Check for Updates** suggests `brew upgrade`.
- Every change is now also installed and tested with Homebrew on a real Mac: the command line program, the default folders, the app bundle, the GUI window, and uninstalling.

**Fixed**
- The Linux package tests now really fail if uninstalling leaves files behind (the check could not fail before).

## v1.21.0 - Linux packages for Debian, Ubuntu, Fedora, openSUSE, Arch, and snap (2026-10-10)

**New**
- Packages for the common Linux distributions are attached to this release. Your package manager installs FFmpeg, Python, and Tkinter with them, and the app appears in the application menu:
  - `screencap-documentation-tool_1.21.0-1_all.deb` for Ubuntu, Debian, Linux Mint, and Pop!_OS: `sudo apt install ./screencap-documentation-tool_1.21.0-1_all.deb`
  - `screencap-documentation-tool-1.21.0-1.noarch.rpm` for Fedora, RHEL and its rebuilds (Rocky, Alma; FFmpeg from RPM Fusion), and openSUSE: `sudo dnf install ./...rpm` or `sudo zypper install --allow-unsigned-rpm ./...rpm`
  - `screencap-documentation-tool-1.21.0-1-any.pkg.tar.zst` for Arch Linux (`sudo pacman -U ./...`); the same recipe goes to the AUR as `screencap-documentation-tool`
  - `screencap-documentation-tool_1.21.0_amd64.snap` for any distribution with snapd: it brings its own FFmpeg, Tesseract OCR, and Pandoc
- `SHA256SUMS-linux.txt` lists the checksums of the Linux packages.
- Installed from a package, the default `source` and `output` folders are in `~/Documents/Screencap Documentation Tool` (any folder can still be chosen), and **Help > Check for Updates** opens the right package for your distribution.
- Every change is now tested by installing each package in a clean Ubuntu 24.04, Ubuntu 22.04, Debian 12, Fedora, Rocky Linux 9, openSUSE Tumbleweed, and Arch Linux system, processing a recording, opening the GUI, and uninstalling; the snap is installed and tested with snapd.

**Coming**
- The AUR and Snap Store listings go live once their accounts are set up; releases then update them automatically.

The install command (`install.sh`) still works as before.

## v1.20.0 - New look, with light and dark themes (2026-10-10)

**New**
- **Light and dark themes.** **View > System Theme** (the default) follows the app theme of Windows (Settings > Personalization > Colors), macOS, or the Linux desktop, and switches by itself when that setting changes. **View > Light Theme** and **View > Dark Theme** pick one for good. On Windows the title bar turns dark too. The choice is remembered.
- A cleaner main window: the folders sit in a slim bar at the top, the **Recordings** list and **Settings** are cards on the left, the step editor and log are on the right, and a status bar at the bottom shows progress and the version. Drag the divider to give either side more room.
- **Settings** shows only what you change most: the preset (with a line saying what it is for), sensitivity, when the screenshot is taken, and the highlight, blur, duplicate, and narration switches. Everything else moved to **Advanced settings...**, a separate window (also in the **View** menu).
- **Save as preset...** and **Delete preset** sit next to **Advanced settings...**.
- The Steps tab is reorganized: **Crop** and **Blur** are menus above the picture, **Highlight this step** is next to them, and the rarely used **Open** buttons (image, steps.md, folders) are one menu.
- **Document title** now has a full-width box with larger text, with **Version** and **Author** beside it, in their own row together with **Export**.
- New check boxes and radio buttons that look the same everywhere, primary buttons (**Process All**, **Save Changes**) in the accent color, and Segoe UI on Windows.
- Ctrl+1 and Ctrl+2 switch between the Steps and Log tabs.

**Changed**
- The window opens at 1400 x 860 and still fits down to 1180 x 720.

Your settings, presets, and recordings carry over unchanged.

## v1.19.0 - New install folder for the Windows installer (2026-10-10)

**Changed**
- The Windows installer now installs in `C:\Program Files\ILHS\Screencap-Documentation-Tool` for all users by default (Windows asks for admin rights). Every app from this organization will use an `ILHS` folder like this.
- Without admin rights, choose **Install for me only** on the first page: the app goes to `%LOCALAPPDATA%\Programs\ILHS\Screencap-Documentation-Tool`.
- Upgrading from v1.16.0 or earlier moves the app: the copy in the old folder (`...\Screencap Documentation Tool`) is uninstalled first, so there is only one copy and one entry in **Settings > Apps**. Settings, presets, recordings, and screenshots are kept.
- Silent installs (`/VERYSILENT /SUPPRESSMSGBOXES /NORESTART`) now install for all users unless `/CURRENTUSER` is added. `/DIR="..."` still chooses another folder.
- Uninstalling also removes the `ILHS` folder when no other app is left in it.
- The winget listing offers the all-users install first, matching the installer.

**Tested**
- Every pull request installs and uninstalls the new installer for one user and for all users, and upgrades from the real v1.16.0 installer in both modes, checking that the old folder is gone and only one Apps & Features entry remains.

## v1.18.0 - Help menu, About, and update check (2026-10-10)

**New**
- A menu bar with **File** (choose and open the source and output folders) and **Help**.
- **Help > Help** (or F1): built-in guides to getting started, presets, editing steps, blurring, exporting, keyboard shortcuts, and troubleshooting. **Online Documentation** opens the README.
- **Help > Report a Problem...** and **Suggest an Idea...** open new GitHub issue forms that ask for the version, install type, and steps, and remind you to remove anything sensitive. **Project on GitHub** and **Release Notes** open the repository and its releases.
- **Help > About** shows the version, license, and links, and **Copy Details** copies the version, operating system, and which helper programs were found (without folder paths) for a problem report.
- **Help > Check for Updates...** asks GitHub whether a newer release is out and, if so, shows what changed and opens the right download: the installer, the portable zip, or the Releases page for the Python install.
- **Check for Updates Automatically**: the GUI asks once whether to turn it on; when on, it checks at most once a day in the background. Cancel on the update message skips that version.
- Administrators can turn update checks off on a PC with the environment variable `SCREENCAP_NO_UPDATE_CHECK=1` (Group Policy, Intune, or a login script).

**Privacy**
- The update check only asks GitHub for the public list of releases; nothing about the PC or its files is sent. The privacy statement in `CODE_SIGNING_POLICY.md` now describes it.

## v1.17.0 - More built-in presets (2026-10-10)

**New**
- **General desktop use** preset: for moving around the operating system, such as opening apps, browsing files in File Explorer, and flipping through menus. It catches quick menu changes and saves the screenshots exactly as captured, with **no blurring and no red boxes**.
- **Remote desktop / VM console** preset: RDP, VNC, Hyper-V, VMware, and other remote or virtual machine consoles. Ignores compression noise and waits for a slow screen to finish drawing.
- **Forms and spreadsheets** preset: filling in forms, tickets, and spreadsheets. Catches small field changes and merges a whole entry being typed into one step.
- **Slideshow / presentation** preset: one screenshot per slide, no forced shots on slides shown for a long time, no blurring, and no red boxes.
- **Video meeting / screen share** preset: recorded calls and shared screens. Ignores webcam and video movement, keeps blurring on for names and email addresses, and draws no red boxes.
- All presets work in the GUI (**Preset** list) and on the command line (`--preset "General desktop use"`, `--list-presets`). The README's Presets section explains what each one changes.

**Changed**
- The preset list in the GUI is wider, so the longer names fit.

## v1.16.0 - Windows installer (2026-10-04)

**New**
- A Windows installer is attached to this release: `Screencap-Documentation-Tool-v1.16.0-windows-x64-setup.exe`. It installs the packaged app (Python built in), adds a Start Menu shortcut, an optional desktop shortcut, and an entry in **Settings > Apps** to uninstall it.
- By default it installs for your account only, with no admin rights needed (in `%LOCALAPPDATA%\Programs`). Choose **Install for all users** at the start to install in `Program Files` instead (needs admin rights).
- If FFmpeg is not found, the installer offers to install it with winget. Tesseract OCR (automatic blurring) and Pandoc (Word export) can be installed the same way by ticking one box.
- Installing a newer version over an older one upgrades it in place. Uninstalling never touches your recordings, output, or settings.
- Silent installs for deployment: `setup.exe /VERYSILENT /SUPPRESSMSGBOXES /NORESTART` (add `/ALLUSERS` for all users, `/TASKS=desktopicon` for a desktop shortcut).
- The portable zip is still attached for PCs where you prefer not to install anything. `SHA256SUMS.txt` now lists both files.
- Every pull request now also builds the installer and tests installing, starting, and uninstalling it, both for one user and for all users.

**Known limitations**
- The installer and app are not code signed yet, so Windows SmartScreen may show **Windows protected your PC**. After checking the checksum, choose **More info > Run anyway**. Code signing through SignPath Foundation is planned.
- Captions From Narration still needs the Python install.

## v1.15.0 - Windows app without Python (portable zip) (2026-10-04)

**New**
- A packaged Windows app is attached to this release: `Screencap-Documentation-Tool-v1.15.0-windows-x64-portable.zip`. It holds `Screencap Documentation Tool.exe` (the GUI) and `screencap.exe` (the command line), with Python built in, so a PC does not need Python installed. Extract it anywhere and start the GUI.
- `SHA256SUMS.txt` is attached too. Check the download with `(Get-FileHash .\Screencap-Documentation-Tool-v1.15.0-windows-x64-portable.zip).Hash` in PowerShell before running it.
- The packaged app keeps its default `source` and `output` folders in `Documents\Screencap Documentation Tool`, so it works from any folder, including read-only ones. Any folder can still be chosen in the GUI.
- FFmpeg is still needed (`winget install --id Gyan.FFmpeg -e`), as are the optional Tesseract OCR and Pandoc; their licenses keep them separate. Captions From Narration needs the Python install.
- Every pull request now builds the packaged app on a real Windows machine and tests it: version and file details, processing and exporting a recording, the Documents folders, and that the GUI opens. Each release gets the tested files attached automatically.

**Known limitations**
- The app is not code signed yet, so Windows SmartScreen may show **Windows protected your PC** the first time. After checking the checksum, choose **More info > Run anyway**. Code signing through SignPath Foundation is planned.
- The Python install (Quick Start command) is unchanged and remains the main way to install the tool.

## v1.14.1 - New taskbar identity (2026-10-04)

**Changed**
- The app's Windows taskbar identity is now `ILHS.ScreencapDocumentationTool.GUI` (ILHS, short for ILikeHostingServices, the prefix every app from this organization uses; it was named after the previous owner account). It keeps the running window, its icon, and pinned shortcuts together as one taskbar button.
- Re-running the installer updates the Start Menu and Desktop shortcuts and any taskbar pin of this tool to the new identity. If you still see two taskbar buttons after updating, unpin the old one and pin the app again from the Start Menu.
- Commits and release tags are now made by `ILHS-Owner`, the organization's own owner account, using its private GitHub email address.
- The repository's default branch is now `main`. The Quick Start commands are unchanged and install from it automatically.

## v1.14.0 - Captions From Narration (2026-10-03)

**New**
- If you talk while you record, the tool can turn what you said into the first-draft caption of each step. Each sentence goes to the step whose screen was showing while it was said.
- Speech recognition runs offline on your PC with faster-whisper (an open source version of OpenAI's Whisper). The audio never leaves the machine, and no graphics card is needed.
- It is optional and off by default. Install it by adding `-WithWhisper` to the Windows Quick Start command, or `SCREENCAP_WITH_WHISPER=1` on Linux and macOS (about 450 MB, kept in a separate `whisper-env` folder so it never changes your system Python). The speech model downloads on first use.
- GUI: tick **Captions from narration** in Detection Settings and pick a **Model**, or click **Captions From Narration** in the Steps tab for a recording that is already processed.
- Command line: `--transcribe`, `--whisper-model`, and `--whisper-python`.
- Only empty captions are filled, so captions you typed are never replaced. The full transcript with timestamps is saved as `transcript.txt`.
- Tested on Windows and Linux with a real speech sample, including both installers.

## v1.13.1 - Open source under the MIT License (2026-10-03)

**Changed**
- The project is now open source under the MIT License (`LICENSE`): free to use, change, and share, including at work, as long as the copyright notice stays with it. It comes with no warranty.
- New `SECURITY.md` explains how to report a security problem privately.
- README has a new **License And Support** section: support is best effort, and bug reports should include the version and log lines, never real recordings.
- Commits and release tags are now made under the organization's own owner account.

## v1.13.0 - Automated testing on real Windows, Linux, and macOS (2026-10-02)

**New**
- Every push and pull request runs the full test suite on real Windows 11-class (windows-latest) and Linux machines through GitHub Actions: screenshot detection, duplicate removal, highlight boxes, cropping, blurring with Tesseract, HTML/Word/PDF export, presets, launching VLC, and the GUI itself (processing a recording, step navigation with the arrow keys, reordering, saving captions). A run fails if any test was skipped, so a missing tool cannot hide a problem.
- The one-step installers are tested on clean machines whenever an installer changes, every Monday, and on demand (**Actions > Installers > Run workflow**): Windows both per-user and system-wide, Linux, and macOS. Each run checks the installed files and version, the Start Menu shortcut's icon and taskbar identity, that the Users group can write to a system-wide install, that the installed tool processes and exports a recording, and that re-running the installer (an update) keeps your recordings and output.
- Both workflows use a read-only token and no secrets. GitHub Actions is free for public repositories.
- README has a new **Automated Testing** section, and roadmap item #11 is done.

**Fixed**
- GUI: **Process All** and **Process Selected** did nothing except say "The source folder changed. Click Refresh" when the source folder was typed as a Windows short name (such as `C:\Users\RUNNER~1\...`), through a junction, or through a symbolic link. Found by the first Windows test run.
- Steps tab: clicking the picture now takes the keyboard, so **Up** and **Down** page through the steps afterwards. Before, the keys could keep moving through the Videos list instead.
- PDF export works when the tool runs as root or in a locked-down Linux container (set `SCREENCAP_NO_SANDBOX=1` if Chrome refuses to start).

## v1.12.1 - Clearer step navigation and the release version in the footer (2026-10-02)

**Fixed**
- Steps tab: the arrow keys now always continue from the step being shown. Before, after using a button or **< Prev / Next >**, pressing Up or Down in the step list could jump to a different step than expected.
- **Up** and **Down** page through the steps from anywhere in the Steps tab (for example after clicking a button or the picture), not only when the step list has focus. They still behave normally while typing a caption or title.
- The reorder buttons are now named **Move Step Up** and **Move Step Down**, and the status bar says where the step moved. The moved step stays selected, which is why the picture does not change when reordering. **Ctrl+Up** and **Ctrl+Down** in the step list also reorder.

**Changed**
- The window title and footer show the release version (this release: v1.12.1) instead of the GUI file's own version. `screencap.py --version` shows it too, and the Log tab lists each component's version at startup.
- The release workflow can no longer delete tags or releases. That ability was only needed for the one-time renumbering in v1.4.0; it now only creates tags and releases.

## v1.12.0 - Saved presets (2026-10-02)

**New**
- **Preset** dropdown above Detection Settings fills in every setting at once for the kind of recording:
  - **Installer wizard:** the recommended defaults.
  - **Web console:** ignores spinners and slow-loading pages.
  - **Terminal / command line:** catches small text changes and merges bursts of typing.
  - **Fast clicking:** for recordings with short pauses between actions.
- **Save As...** saves the current settings, including **Also blur** patterns, as your own preset. **Delete** removes one. Built-in presets cannot be overwritten or deleted.
- Saved presets live in your profile (`presets.json` next to the GUI settings) and are shared with the command line.
- Command line: `--preset NAME` (not case-sensitive; options you add override the preset) and `--list-presets`.
- The last preset you used is remembered.

## v1.11.0 - Play a step in VLC (2026-10-02)

**New**
- **Play in VLC** in the Steps tab opens the original recording in VLC media player 3 seconds before the selected step's screen appeared, so you can watch the click or keystroke that led to it.
- VLC is found on the PATH or in its standard install folders (Windows `Program Files\VideoLAN\VLC`, macOS `/Applications/VLC.app`).
- Each new VLC window starts at the right moment even if VLC is set to allow only one instance.
- Processed recordings now remember where the source video is, so this keeps working when the recording is not selected in the Videos list.

## v1.10.0 - Export to HTML, Word, and PDF (2026-10-02)

**New**
- One-click export from the Steps tab to a finished document in the recording's `export/` folder:
  - **HTML:** a single self-contained file with the screenshots embedded, easy to email or put on a file share.
  - **Word (.docx):** made with Pandoc, with proper Title, Subtitle, Author, and Date styles.
  - **PDF:** printed by Microsoft Edge (included with Windows 11), Google Chrome, or Chromium, with no window shown.
- Every export starts with a header block: title, version, date (YYYY-MM-DD), and author. Set these in the Steps tab; the title defaults to the recording's name and the version to `v1.0.0`.
- Captions appear under each screenshot.
- Exports use the blurred screenshots. **Unblurred copy** exports the unblurred set after a confirmation, with `-UNREDACTED` in the file name and a warning inside.
- Command line: `--export html,docx,pdf` (also re-exports recordings that were already processed), `--doc-author`, `--doc-version`, `--pandoc`, `--browser`.
- The installers now install Pandoc as an optional component (Windows: `JohnMacFarlane.Pandoc`). HTML and PDF export do not need it.

## v1.9.0 - Automatic blurring of sensitive information (2026-10-02)

**New**
- Passwords, license and product keys, API tokens, GUIDs, IP, MAC and email addresses, masked passwords, and anything after labels such as `Password:` or `Token:` are found with Tesseract OCR and blurred automatically.
- **Two copies:** `steps.md` uses the blurred screenshots, and a complete unblurred set is kept in `unredacted/` with its own `steps-unredacted.md` (marked "do not publish"), in case a blurred detail is needed.
- **Toggles:** blurring can be switched on or off for a whole recording (**Blur sensitive info**) or a single step (**Blur this step**).
- **Fix mistakes by hand:** **Add Blur Box** blurs anything else, **Un-blur / Re-blur** switches off a false positive with a click, and **Re-scan All Steps for Sensitive Text** runs detection again. The Original frame view outlines every blur box.
- **Your own patterns:** **Also blur** in the GUI or `--redact-pattern` on the command line, for example an internal domain name.
- Blurred areas are pixelated and then blurred, so the text cannot be read back. The originals are never changed.
- Command line: `--no-redact`, `--redact-pattern`, `--tesseract`.
- The installers now install Tesseract OCR as an optional component (Windows: `UB-Mannheim.TesseractOCR`, which asks for administrator permission). Without it, everything else works and hand-drawn blur boxes still apply.

**Note**
- Automatic detection is a safety net, not a guarantee. Review screenshots before publishing them.

## v1.8.0 - Adjustable cropping (2026-10-02)

**New**
- Crop screenshots by dragging a rectangle on the picture in the Steps tab: **Crop: All Steps** for the whole recording, or **This Step** for one step. Press Esc to cancel.
- **No Crop Here** leaves one step uncropped, and **Clear All Crops** removes every crop.
- On **Original frame**, dashed outlines show the crop (blue) and the "what changed" box (red) that will be applied.
- Command line: `--crop X:Y:W:H`, for example `--crop 0:0:1920:1080` to keep the left monitor of a dual-screen recording.
- The originals are never cropped, so a crop can be adjusted or removed at any time and nothing is lost.
- Crop sizes are rounded down to even numbers and kept inside the frame, so every image format can save them.

## v1.7.0 - Red box around what changed (2026-10-02)

**New**
- Each screenshot gets a red box around the area that changed since the previous step, so readers can see where to click or what appeared.
- The box hugs the change: in testing it fit a 14 pixel checkbox with a 28 pixel box. Whole-screen changes (a new window) get no box, and small far-away changes such as a moving mouse cursor are left out.
- Steps tab: **Highlight changes** turns the box on or off for the whole recording, and **Highlight this step** overrides it for one step. The preview updates immediately.
- GUI: **Highlight what changed in each step** in Detection Settings. Command line: `--no-highlight`.
- The box is drawn only on the rendered screenshot. The original frame in `originals/` is never changed, so the box can be turned off again at any time.
- Output from earlier versions gets its change areas worked out the first time it is saved in the editor.

## v1.6.0 - Duplicate screenshot removal (2026-10-02)

**New**
- Screenshots that look virtually identical to one already kept, for example when you go back to a screen you already captured, are removed automatically.
- Removed duplicates are not deleted: they are kept as deleted steps with their original frames, and **Restore Deleted** in the Steps tab brings them back. The Steps tab shows how many were removed as duplicates.
- GUI: **Remove duplicate screenshots** checkbox and **Duplicate if differs by (%)** in Detection Settings.
- Command line: `--no-dedup` and `--dedup-threshold` (default 0.01 percent).
- The default only matches near-exact copies. In testing, a moving mouse cursor counted as no change while a ticked 14 pixel checkbox did not count as a duplicate, so small but real changes are kept.
- The final screenshot of a recording is always kept, so the end result is always documented.

## v1.5.0 - Step editor (2026-10-02)

**New**
- **Steps tab (step editor)** replaces the Preview tab. For the selected recording you can delete steps, restore deleted steps, move steps up or down, and write a caption for each step. Click **Save Changes** to re-render the screenshots and regenerate `steps.md`.
- Every captured frame is now kept untouched in `originals/`, and the screenshots in `steps.md` are rendered from those originals. Edits never destroy anything, and later features (crop, highlight, redaction) build on this.
- Captions replace the `_Notes:_` placeholder in `steps.md`.
- Unsaved edits are protected: the GUI asks before switching recordings, processing, or closing.
- `ROADMAP.md` records the ideas on hold for discussion: narration to captions, watch folder, Windows test automation, and a single-file Windows app.
- Automated tests in `tests/` (run with `python -m unittest discover -s tests -v`).

**Changed**
- Reprocessing with `--force` (or "Reprocess videos that are already done") now moves the previous results, including captions, into a `previous-<date>-<time>` folder instead of deleting them.
- If `steps.md` was edited by hand, saving from the editor keeps the hand-edited copy as `steps.hand-edited-<date>-<time>.md`.
- Output from v1.4.0 and earlier is upgraded automatically when opened. The old `steps.md` is kept as a backup.

## v1.4.0 - Automatic per-user or system-wide install on Windows (2026-10-01)

**New**
- The Windows install command now chooses the scope for you:
  - Normal PowerShell window: installs for the current user only, as before. No admin needed.
  - Administrator PowerShell window: installs for everyone on the PC. Python and FFmpeg are installed system-wide, shortcuts go on the All Users Start Menu and Public Desktop, and all users can save into the default `source` and `output` folders.
- `-SystemWide` and `-UserOnly` switches override the automatic choice.
- `Install-Prerequisites.ps1` gains `-Scope user|machine`. In machine mode, copies installed only in one user's profile are not counted, because other accounts cannot use them.
- Upgrading a PC from per-user to system-wide removes your old per-user shortcuts so the app does not appear twice.
- GitHub releases are now published automatically for every version tag, and `CHANGELOG.md` lists every release.

**Documentation**
- README covers the single command, both explicit variants, switching a PC to system-wide, and uninstalling either kind of install.

## v1.3.0 - Custom application icon (2026-10-01)

**New**
- Custom icon (a monitor with amber capture brackets) for the window title bar, taskbar, Alt+Tab, Start Menu and Desktop shortcuts, and the Linux menu entry.
- On Windows the GUI has its own taskbar identity, so it shows its icon instead of grouping under the generic Python icon.
- Windows shortcuts now launch through the Python launcher (`pyw.exe`), so they can be pinned to the taskbar and keep working after Python upgrades.
- `assets/make_icon.py` rebuilds the icon from code if you want to tweak it (needs Pillow, which the tool itself does not).

**Upgrade note**
- Paste the Quick Start command again to get the new shortcuts. If you pinned the old version, unpin it and pin again from the Start Menu.

## v1.2.1 - Installer fixes and copy-and-paste Quick Start (2026-10-01)

Install everything (prerequisites and the tool) with a single copy-and-paste command. Running the same command again updates the tool and never deletes your recordings or screenshots.

**Installers**
- Windows (`install.ps1`): installs to `C:\DATA\Tools\Screencap-Documentation-Tool`, installs Python 3 and FFmpeg with winget, and adds Start Menu and Desktop shortcuts. No admin rights needed, and it works even when PowerShell's default policy blocks script files. Supports `-InstallDir`, `-NoShortcuts`, and `-SkipPrerequisites`.
- Linux (`install.sh`, run with sudo): installs FFmpeg, Python, and Tkinter with apt, dnf, or pacman, installs to `/opt/Screencap-Documentation-Tool`, and adds `screencap` and `screencap-gui` commands plus a menu entry. `source` and `output` belong to your user, so no sudo is needed afterwards.
- macOS (`install.sh`, no sudo): installs Homebrew if needed, plus FFmpeg, Python, and the matching Tkinter, installs to `~/Applications/Screencap-Documentation-Tool`, and adds `screencap` and `screencap-gui` commands and a double-clickable `Screencap GUI.command`.

**Fixed (since v1.2.0)**
- The Linux installer now picks a Python that has Tkinter, so the GUI starts.
- The Linux installer no longer reinstalls curl.

**Documentation**
- Quick Start commands for each OS, a "review the installer first" option, and update and uninstall steps.

## v1.2.0 - First one-step installers (2026-10-01)

First version of the copy-and-paste installers. Use v1.2.1 instead: in this version the Linux installer could pick a Python without Tkinter, so the GUI might not start, and it also reinstalled curl unnecessarily.

**New**
- `install.ps1` for Windows: downloads the tool, installs Python and FFmpeg with winget, and creates shortcuts.
- `install.sh` for Linux (`/opt`) and macOS (`~/Applications`).

## v1.1.1 - README reorganized for easier reading (2026-10-01)

**Documentation**
- The README now leads with what you get, then quick start, then reference material.
- GUI walkthrough in the order the window is laid out.
- Tuning advice shows the GUI setting and the command line switch side by side.
- Troubleshooting is grouped into setup, GUI, and processing problems.

No code changes.

## v1.1.0 - Desktop GUI (2026-10-01)

**New**
- `screencap_gui.pyw` desktop GUI, launched with `Run-Screencap-GUI.bat` on Windows. Uses Tkinter, which ships with Python, so there is nothing extra to install.
- Pick source and output folders, see every recording with its status and step count, and process all or selected recordings with a live progress bar and Cancel.
- Sensitivity presets (High, Normal, Low) and every command line setting, with input validation and Reset Defaults.
- Preview tab to page through captured steps, open images full size, and open `steps.md`.
- Log tab with errors highlighted.
- Settings are remembered per user (in `%APPDATA%\ScreencapDocTool` on Windows), outside the repository.

**Changed**
- `screencap.py` v1.1.0: no console windows flash up when FFmpeg runs from the GUI on Windows. Command line behavior is unchanged.

## v1.0.0 - Initial release: automatic step screenshots from screen recordings (2026-10-01)

Drop screen recordings in a folder and get a screenshot of every step, plus a ready-to-write Markdown index.

**What's included**
- `screencap.py` command line tool (Python 3.8+ standard library and FFmpeg only).
- Finds `.mp4`, `.mov`, and `.mkv` recordings in the `source` folder (optionally including subfolders).
- FFmpeg scene detection tuned for screen recordings. Bursts of changes such as typing or window animations are merged into one step.
- Each screenshot shows the finished state of a step, captured just before the next change (`--capture-point start` captures right after each change instead).
- Full resolution PNG or JPG screenshots, plus `steps.md` and `steps.json` per recording.
- Skips recordings that are already processed (`--force` to redo), `--dry-run` for tuning, and a log in `output/screencap.log`.
- Windows 11 launcher (`Run-Screencap.bat`) and prerequisite installer (`Install-Prerequisites.ps1`, uses winget).
- `.gitignore` keeps recordings, screenshots, and logs, which may contain sensitive data, out of the repository.
