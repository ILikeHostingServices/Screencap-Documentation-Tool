HANDOFF.md v1.13.0 (Last Rev: 2026-10-10)

# Handoff

Tasks that the cloud coding session cannot finish alone, because they need the repository owner, an organization admin, or a local machine with full push rights. Hand this file to whoever (person or agent) has that access. Work through the open items in order, then update this file: mark the item done with the date in the **Done** table, and add anything new.

## Context

### The Project

- **Repository:** `ILikeHostingServices/Screencap-Documentation-Tool` (public), MIT License, default branch `main`. GitHub Actions: `Tests` (every push and pull request, Windows and Linux), `Installers` (installer changes, weekly, on demand), `Windows build` (builds and tests the packaged Windows app and its installer on every pull request, and attaches them to releases), `Publish releases` (manual; also submits the newest release to winget), `Publish to winget` (`winget.yml`; manual for an existing release).
- **What it is:** a Python tool (GUI and command line) that takes a screenshot of every step in a screen recording, using FFmpeg scene detection. Windows 11 is the main target; Linux and macOS work too. See `README.md`.
- **Current release:** v1.20.0 (new look, light and dark themes) is published as Latest, with the unsigned installer (`...-windows-x64-setup.exe`), the portable zip (`...-windows-x64-portable.zip`), and `SHA256SUMS.txt` attached. v1.19.0 (install folder `Program Files\ILHS\...`) also has them; v1.17.0 and v1.18.0 are notes-only releases (their Windows build would fail the newer install-folder test, and v1.20.0 contains them).
- **Packaged app layout:** PyInstaller one-folder build (`packaging/screencap.spec`): `Screencap Documentation Tool.exe` (GUI), `screencap.exe` (command line), and a shared `_internal` folder. The installer is built with Inno Setup (`packaging/installer.iss`). Never change the installer's `AppId` GUID: Windows uses it to recognize upgrades.

### Accounts And Identity

- **`ILHS-Owner`** is the organization's working owner account: use it for all merges, settings, pushes, releases, and (if code signing is taken up) signing approvals. Two-factor authentication is on.
- **The original owner account** stays an owner of the organization as a backup only. Do not merge, commit, push, or edit files with it: github.com records those under the account that does them, and the history would need another rewrite.
- **Git identity for every commit and tag:** `ILHS-Owner <337515992+ILHS-Owner@users.noreply.github.com>`. This is the account's private GitHub address; never put the account's real email address in a commit, and never write it into a repository file.
- **Do not write the earlier account names into any repository file.** The history has been rewritten so they appear nowhere; keep it that way. If `maintenance/rewrite-history.sh` ever has to run again (for example after a commit under an earlier name), a literal earlier name in a file makes its final check fail. Refer to "the original owner account" instead.

### Conventions

- **Windows install folder** for every app from this organization: `C:\Program Files\ILHS\<App-Name>` for all users, or `%LOCALAPPDATA%\Programs\ILHS\<App-Name>` per user (this app: `Screencap-Documentation-Tool`, from v1.19.0; the installer moves older copies).
- **Windows taskbar ID (AppUserModelID)** for every app from this organization: `ILHS.<AppName>.<Component>`. This app uses `ILHS.ScreencapDocumentationTool.GUI` (in `screencap_gui.pyw`, `install.ps1`, and `.github/workflows/installers.yml`).
- **Versions** are Major.Minor.Patch only (`v1.14.1`, never `v1.14` or pre-release suffixes). Every file has a header with its own version and last edit date (YYYY-MM-DD); bump it on every functional change. No em or en dashes in any file.
- **Releases** are created by `.github/workflows/release.yml` from `.github/releases/manifest.txt` (one `vX.Y.Z <full commit ID>` line per release) and `.github/releases/vX.Y.Z.md` (the notes, also copied into `CHANGELOG.md`). `version.py` `RELEASE` must equal the newest `CHANGELOG.md` entry (a test checks it). The workflow only creates tags and releases that do not exist yet; it never deletes or changes existing ones. GitHub only lets the workflow create a tag on a commit whose `.github/workflows/` files are identical to the newest commit's. **Publish right after each release merges**, before the next change to `.github/workflows/`: GitHub refuses a tag made by the workflow on a commit whose workflow files differ from `main`'s ("refusing to allow a GitHub App to create or update workflow"). If that happens, point the version at a commit with the same app and current workflow files (as done for v1.17.0 and v1.18.0 in pull request #14); `release.yml` reports such tags and still creates the others.
- **Merging pull requests:** always **Create a merge commit** (never squash or rebase), as `ILHS-Owner`, because the release manifest names exact commit IDs.
- **Standing permission (from the owner, 2026-10-04):** a cloud session may merge its own pull requests once every check is green, as a merge commit, through its GitHub connection, but only while that connection is `ILHS-Owner` (check who opened the pull request first). It still asks the owner before history rewrites, publishing releases, deleting branches or tags, and any repository, organization, or account setting.
- **Local agents** (on the owner's machine) should also make changes through a pull request, not by pushing to `main`, so the tests run first.

### What The Cloud Session Can And Cannot Do

It can push only to its own working branch (`claude/...`), open and (see above) merge pull requests, start workflows, and read public GitHub data. It cannot push to `main`, force-push, create or delete tags, change repository, organization, or account settings, or reach websites outside its network policy (huggingface.co was added on 2026-10-04 and works in sessions started after that).

## Owner To-Do List

Everything that needs the owner (an account, a key, an approval, or a setting), in one place. Details for each are in the numbered items below. Tell the cloud session when a step is done; it runs the publishing and checks the result.

| # | Platform | What to do | Why | Where |
| --- | --- | --- | --- | --- |
| A1 | Windows (winget) | Accept Microsoft's contributor license agreement (CLA) on the open winget pull request, signed in as `ILHS-Owner`. Post one comment: `@microsoft-github-policy-service agree company="ILikeHostingServices"` (the code is copyrighted to the organization, so use the company form). It is signed once per GitHub account and covers every later pull request | Microsoft does not review or merge until the submitter accepts (the `Needs-CLA` label and the queued `license/cla` check) | https://github.com/microsoft/winget-pkgs/pull/450166 |
| A2 | Windows (winget) | Answer moderator questions on that pull request, if any (the cloud session can draft the replies) | New packages are reviewed by hand | Same pull request |
| A3 | Windows (winget) | Renew the `WINGET_TOKEN` secret before it expires (created 2026-10-10, one year): new classic token, `public_repo` scope only, then replace the secret | Without it, releases stop reaching winget (they still publish) | https://github.com/settings/tokens, repository **Settings > Secrets and variables > Actions** |
| B1 | Linux (AUR) | **Blocked (2026-10-10):** AUR registration is paused by the Arch team (wave of automated sign-ups). Try again when it reopens; watch the Arch news feed or the aur-general list. Nothing breaks meanwhile: the Arch package is attached to every release | Arch users install from the AUR | https://aur.archlinux.org/register, https://archlinux.org/news/ |
| B2 | Linux (AUR) | After B1: make an SSH key just for publishing (item 4), add the public half to the AUR account, the private half as the `AUR_SSH_PRIVATE_KEY` secret, then delete both files | Lets the release workflow push the PKGBUILD | AUR **My Account**; repository secrets |
| B3 | Linux (Snap Store) | ~~Create an Ubuntu One account and register the name~~ Done 2026-10-10: account `ilhs-owner2026`, name `screencap-documentation-tool` registered | | |
| B4 | Linux (Snap Store) | In WSL Ubuntu: install snapcraft and export a login token (exact commands in item 4), then add it as the `SNAPCRAFT_STORE_CREDENTIALS` secret; renew before it expires (2027-10-10) | Lets the release workflow upload snaps | Repository secrets |
| C1 | macOS (Homebrew) | ~~Create the public repository `ILikeHostingServices/homebrew-tap`~~ Done 2026-10-10 (created as `Homebrew-Tap`; GitHub names ignore case, so `brew tap ilikehostingservices/tap` finds it) | | |
| C2 | macOS (Homebrew) | ~~Workflow permissions: Read and write~~ Done 2026-10-10: the tap workflow committed the v1.22.0 formula | | |
| C3 | macOS (Homebrew) | ~~Give the Claude GitHub app access to it~~ Done 2026-10-10; the cloud session pushed the tap files the same day | | |
| C4 | macOS (Apple) | **Shelved (2026-10-10, cost):** no Apple Developer Program membership for now. Homebrew needs none. Revisit later: see item 6 | | |
| D1 | GitHub | Optional: ask GitHub Support to drop the old pull request refs (item 1) | Old commit names stay visible there until then | https://support.github.com |
| D2 | All | When a secret is added or renewed, tell the cloud session; it runs the publish (Linux build or tap update with the newest release) and checks the result | | |

**Secrets and tokens kept for publishing** (all in this repository's **Settings > Secrets and variables > Actions**; none are ever written into files):

| Secret | Holds | Scope | Expires | If it leaks |
| --- | --- | --- | --- | --- |
| `WINGET_TOKEN` | Classic personal access token of `ILHS-Owner` | `public_repo` only | 2027-10-10 | Revoke it at https://github.com/settings/tokens and make a new one |
| `AUR_SSH_PRIVATE_KEY` | SSH private key used only for the AUR | Push to this AUR package | Never (rotate yearly) | Remove the public key from the AUR account, make a new pair |
| `SNAPCRAFT_STORE_CREDENTIALS` | Snapcraft login export | Upload and release this snap only | The date given to `--expires` | Revoke it in the Snapcraft dashboard, export a new one |

## Open Items

### 1. Optional: Ask GitHub To Drop The Old Pull Request Commits

- **Who:** owner, signed in as `ILHS-Owner`.
- **Will it go away by itself?** No. GitHub keeps pull request refs permanently; only GitHub Support can remove them.
- **Why:** after the history rewrite, GitHub still keeps read-only copies of the original commits of pull requests #1, #2, and #3 (`refs/pull/N/head`), which only GitHub can delete. Those pull requests keep listing commits under the earlier names, and old commits stay viewable by their old ID. Nothing else refers to them.
- **How:** open a ticket at https://support.github.com:

  > Please remove the cached pull request refs for pull requests #1, #2, and #3 in ILikeHostingServices/Screencap-Documentation-Tool and run garbage collection on the repository. We rewrote the history to change the commit author name and force-pushed main and all tags; the old commits are still reachable through those pull request refs.

- **Afterward:** the backup bundle of the old history on the owner's machine can be deleted once the owner is happy with the result.

### 2. Code Signing (Roadmap #12): On Hold

**Status (2026-10-06):** on hold by the owner's decision. Releases stay unsigned, with `SHA256SUMS.txt` checksums and the instructions in `CODE_SIGNING_POLICY.md`. Nothing here needs doing until the owner picks an option.

**What happened:** the owner applied to the free SignPath Foundation program. SignPath declined for now: the program is for projects that already show public trust and visibility (GitHub stars, forks, contributors, outside articles or discussions such as Reddit, Stack Overflow, or YouTube, institutional backing, sustained activity). They invited a new application once the project has broader recognition, and pointed to their paid subscription.

**Already in place, whichever option is chosen:** organization-wide two-factor authentication; the app and installer built and tested only by GitHub Actions (`.github/workflows/build-windows.yml`); published releases with checksums; `CODE_SIGNING_POLICY.md` (to reapply to SignPath Foundation, restore its v1.0.0 wording from git history, which has the attribution line SignPath requires on the policy and download pages). Signing must cover all three programs: both `.exe` files inside the app, before they are packed into the zip and installer, and the setup `.exe`.

**Options** (check current prices and rules before deciding; they change):

| Option | Cost | Notes |
| --- | --- | --- |
| SignPath Foundation | Free | Reapply once the project has public visibility (share it in the sysadmin community first). Publisher shown: SignPath Foundation. |
| SignPath paid subscription | Paid, see https://docs.signpath.io/change-subscription | Same GitHub Actions integration that was planned, so the old steps apply as they were: the owner sets up the SignPath project and adds the `SIGNPATH_API_TOKEN` and `SIGNPATH_ORG_ID` repository secrets, then a cloud session adds `signpath/github-action-submit-signing-request` to the build workflow. Publisher shown: the owner's own validated name. |
| Azure Artifact Signing (formerly Trusted Signing) | Monthly fee (the basic tier has been around 10 US dollars a month) | Microsoft's managed signing service, with a GitHub Action. Needs identity validation by Microsoft, and eligibility has been limited by country and organization history; check before paying. Publisher shown: the validated name. |
| Certificate from a certificate authority (for example Certum, SSL.com, Sectigo, DigiCert) | Yearly fee | Since 2023 the private key must live on a hardware token or a cloud signing service, so for GitHub Actions use the authority's cloud signing service. Certum sells a lower priced certificate for individual open source developers. |
| Publish to winget (Windows Package Manager) | Free | Not signing, but installs through winget do not show the SmartScreen prompt, and Microsoft scans each submitted version. Needs a manifest pull request to `microsoft/winget-pkgs` per release (can be automated). Also helps visibility for a later SignPath application. |
| Microsoft Store (MSIX package) | Free for individual developers | Microsoft signs Store packages. Needs MSIX packaging and Store certification; a plain `.exe` installer submitted to the Store must already be signed, so only the MSIX route avoids a certificate. |
| Internal (Active Directory Certificate Services) code signing certificate | Free | Trusted only on PCs that trust the internal certificate authority, so not for public downloads. The owner is not interested in this for now. |

Signing does not remove SmartScreen warnings instantly: reputation builds per certificate as people download and run the signed files (since 2024 even EV certificates no longer skip this).

### 3. winget (Windows Package Manager) Listing

- **Goal:** `winget install ILikeHostingServices.ScreencapDocumentationTool` works for anyone. winget installs FFmpeg with it (a dependency in the manifest).
- **How it works:** `.github/workflows/winget.yml` downloads the release's installer, writes the manifest from `packaging/winget/` (`packaging/make_winget_manifests.py`), validates it, tests installing and uninstalling through winget, then opens a pull request on `microsoft/winget-pkgs` with Microsoft's `wingetcreate` tool. `release.yml` runs it after each new release; it can also be run by hand for an existing release.
- **Credential:** the `WINGET_TOKEN` repository secret, a classic personal access token of `ILHS-Owner` with only the `public_repo` scope (created 2026-10-10 with a one-year expiry). The submission uses a fork of `microsoft/winget-pkgs` under the `ILHS-Owner` account. Least-privilege alternative for later: a separate bot account outside the organization. When the token expires, create a new one the same way and replace the secret; without it, releases still publish and only the winget submission is skipped (with a warning).
- **Owner, once:** on the first pull request on `microsoft/winget-pkgs`, the Microsoft contributor license agreement bot asks the submitting account (`ILHS-Owner`) to accept the agreement by replying in a comment. Moderators review a new package by hand, which can take days; later versions are usually merged after the automatic checks.
- **After it is listed:** add the winget command to the README's Windows install section (cloud session).

### 4. Linux Package Stores

Every release gets `.deb`, `.rpm`, Arch, and snap packages attached automatically (`.github/workflows/build-linux.yml`, run by `release.yml`). Two stores need an account first; until their secrets exist, the workflow skips them with a warning.

**AUR (Arch Linux User Repository):**
1. Create an account at https://aur.archlinux.org/register (use `ILHS-Owner`'s address or a dedicated one).
2. On any PC, make a key just for this: `ssh-keygen -t ed25519 -f aur_ilhs -C "ILHS AUR publishing" -N ""`.
3. AUR **My Account > SSH Public Key**: paste the contents of `aur_ilhs.pub`.
4. GitHub repository **Settings > Secrets and variables > Actions > New repository secret**: name `AUR_SSH_PRIVATE_KEY`, value the whole contents of `aur_ilhs` (the private key). Then delete both files from the PC.
5. Ask the cloud session to run **Actions > Linux build > Run workflow** with the newest release tag (or wait for the next release): the package `screencap-documentation-tool` is created on the first push.

**Snap Store:**
1. Create an Ubuntu One account at https://snapcraft.io (Sign in), and accept the developer agreement.
2. Register the name: https://snapcraft.io/register-snap with `screencap-documentation-tool`.
3. In WSL Ubuntu (or any Linux PC). snapcraft is only published as a snap, not an apt package, and `export-login` is a snapcraft command, not a `snap` one:
   ```bash
   sudo snap install snapcraft --classic
   snapcraft export-login --snaps=screencap-documentation-tool \
     --acls=package_access,package_push,package_update,package_release \
     --expires=2027-10-10 ~/snap-creds.txt
   ```
   It asks for the Ubuntu One email, password, and two-factor code of the account that owns the name (`ilhs-owner2026`). The token can only upload and release this one snap.
4. Copy it to the Windows clipboard with `clip.exe < ~/snap-creds.txt`, add it as the repository secret `SNAPCRAFT_STORE_CREDENTIALS` (**Settings > Secrets and variables > Actions > New repository secret**, paste, save), then delete the file: `shred -u ~/snap-creds.txt`. It expires on the date given; renew it the same way.
   - `sudo` in WSL asks for the Linux user's password (set when the distribution was first started), not the Windows one. If it is forgotten, reset it from PowerShell: `wsl -u root passwd <linux user name>`.
5. As with the AUR, the next release (or a manual run of the Linux build with a release tag) publishes to the `stable` channel. The snap uses strict confinement with the `home`, `removable-media`, and `network` interfaces, which the store approves automatically.

**Flathub (later):** not started. Flathub's runtimes have no Tkinter, so the Flatpak would have to build Tcl/Tk (and Tesseract) itself; Flathub also asks submitters to disclose AI-generated code (this project's code was largely written with Claude) and has at times refused such apps, so check its current policy first. The desktop entry and AppStream file (`packaging/linux/`) already use the Flathub-style ID `io.github.ILikeHostingServices.ScreencapDocumentationTool`.

**Official distribution repositories (Debian, Ubuntu, Fedora):** need a volunteer maintainer inside each distribution (a sponsor for Debian, a packager for Fedora); not practical to automate. The packages here are the usual route for independent tools.

### 5. Homebrew Tap (macOS)

- **Goal:** `brew install ilikehostingservices/tap/screencap-documentation-tool` (from v1.22.0, the first version that knows about Homebrew installs). No Apple Developer account: Homebrew builds the app on the Mac from the release source, so it is not quarantined.
- **How it works:** the formula is written by `packaging/homebrew/make_formula.py` (Homebrew's `python@3.13`, `python-tk@3.13`, `ffmpeg`; `screencap` and `screencap-gui` commands; a small `Screencap Documentation Tool.app` the user can link into `~/Applications`). `build-macos.yml` installs and tests it on a Mac for every pull request (`packaging/homebrew/test_formula.sh`).
- **The tap repository** `ILikeHostingServices/homebrew-tap` holds the files in `packaging/homebrew/tap/` (README, LICENSE, `Formula/`, and `.github/workflows/update.yml`). Its workflow checks the latest release every day, writes and tests the new formula on a Mac, and commits it with the tap's own token. Owner steps C1 to C3 above set it up.
- **Status (2026-10-10):** live. The tap workflow published v1.22.0 and runs daily for new releases.
- **One tap for the whole organization:** a tap is a repository of formulas, and its name (`ilikehostingservices/tap`) is not tied to this project. Any other ILHS app can be added as another file in `Formula/` (or `Casks/` for a ready-made, signed `.app`), installed as `brew install ilikehostingservices/tap/<name>`. Each app needs its own formula generator and a line in the tap's update workflow; the current workflow updates only this project's formula.

### 6. Apple Developer Program (macOS Signing): Shelved

**Status (2026-10-10):** shelved by the owner because of the cost (the Apple Developer Program is a yearly paid membership, about 99 US dollars; check the current price). Nothing needs doing now: the Homebrew tap (item 5) builds the app on each Mac from source, so macOS Gatekeeper does not block it and no signature is needed.

**What a membership would add, when revisited:**
- A **Developer ID** certificate to sign the app and Apple **notarization** (an automated malware scan), so a downloadable `.dmg` or `.zip` opens without the "cannot be opened because the developer cannot be verified" warning. That suits people who do not use Homebrew.
- A Homebrew **cask** (a ready-made app instead of a build on the Mac), and optionally the Mac App Store (needs sandboxing work).

**Revisit when:** people ask for a plain download for Mac, the project earns money or sponsorship to cover the fee, or a client requires signed software. **Then:** the owner joins the program (organization enrollment needs a D-U-N-S number; individual enrollment does not), creates a Developer ID Application certificate and an app-specific password or App Store Connect API key, and stores them as repository secrets; a cloud session adds a macOS build job (PyInstaller app, `codesign`, `notarytool`, a `.dmg`) and a cask to the tap.

## Done

| Date | Item |
| --- | --- |
| 2026-10-03 | Default branch renamed to `main` (owner). |
| 2026-10-03 | Private vulnerability reporting enabled (owner). |
| 2026-10-03 | Pull request #1 (ILHS taskbar ID, this file, the rewrite script) merged with a merge commit (owner). |
| 2026-10-04 | `ILHS-Owner` account created with two-factor authentication, private email (`337515992+ILHS-Owner@users.noreply.github.com`) and command line email protection on, made an organization owner, and connected to Claude (GitHub app installed for the account and the organization). The original owner account kept as a backup owner (owner). |
| 2026-10-04 | Email notifications turned off for `ILHS-Owner` (it keeps notifications on github.com; the original owner account still gets the emails) (owner). |
| 2026-10-04 | Pull request #2 (rewrite script v1.2.0 for `ILHS-Owner`, this file, release tagger) merged as `ILHS-Owner` with a merge commit; the merge commit is authored by `ILHS-Owner` with the private address (owner). |
| 2026-10-04 | Pull request #3 (this file v1.3.0) merged as `ILHS-Owner` (owner). |
| 2026-10-04 | History rewritten and force-pushed as `ILHS-Owner` from the owner's machine (local agent): 53 commits on `main` and all 19 tags now use `ILHS-Owner <337515992+ILHS-Owner@users.noreply.github.com>` (the 3 github.com merges have `GitHub` as committer, as expected); the stale branch was deleted; no earlier name remains in any commit, message, tag, or file version (checked by the cloud session). |
| 2026-10-04 | v1.14.1 published (cloud session): tag by `ILHS-Owner`, Latest. |
| 2026-10-04 | Local agent review addressed (cloud session): `Run-Screencap.bat` renormalized (GitHub's download zip still delivers it with CRLF line endings), the GUI focus test hardened for the Windows foreground lock, and `version.py`'s header now always equals the release version (checked by a test). |
| 2026-10-04 | Two-factor authentication required for the whole organization (owner; SignPath step 3.1). |
| 2026-10-04 | Hugging Face allowed in the cloud environment's network access (owner); takes effect in new sessions. |
| 2026-10-04 | v1.15.0 published (cloud session): unsigned packaged Windows app (portable zip) built and tested in GitHub Actions and attached with `SHA256SUMS.txt` (SignPath step 3.2). |
| 2026-10-04 | v1.16.0 published (cloud session): unsigned Windows installer (Inno Setup; one user or all users; silent install) built, install and uninstall tested for both scopes in GitHub Actions, and attached with the portable zip and `SHA256SUMS.txt` (SignPath step 3.4). Pull requests #4, #5, and #6 merged by the cloud session under the standing permission. |
| 2026-10-04 | `CODE_SIGNING_POLICY.md` added and linked from `README.md`, including next to the Windows app downloads (SignPath requires the download page to mention it) (cloud session; SignPath step 3.3). The owner tested the v1.16.0 installer successfully. |
| 2026-10-06 | Applied to the SignPath Foundation program (owner). Declined for now for lack of public visibility, with an invitation to reapply later; code signing put on hold by the owner. |
| 2026-10-06 | `CODE_SIGNING_POLICY.md` v2.0.0 and `README.md` updated to say the programs are not signed (no SignPath wording until signing is taken up again); `ROADMAP.md` #12 and this file record the options (cloud session). The open item to allow SignPath in the cloud environment's network access was dropped as no longer needed. |
| 2026-10-10 | `WINGET_TOKEN` repository secret added (owner): classic token of `ILHS-Owner`, `public_repo` scope only. winget publishing workflow added (cloud session). |
| 2026-10-10 | v1.17.0 (more presets), v1.18.0 (Help menu, About, update check, issue forms), v1.19.0 (install folder `C:\Program Files\ILHS\Screencap-Documentation-Tool`, older copies moved), and v1.20.0 (redesigned GUI, light/dark/system themes) published by the cloud session; pull requests #11 to #14 merged under the standing permission. |
| 2026-10-10 | First winget test run (v1.16.0) stalled inside winget on the test machine and was cancelled; the install test is now time-boxed and best effort (`winget.yml` v1.2.0). |
| 2026-10-10 | v1.21.0 Linux packages (cloud session): `.deb`, `.rpm`, Arch, and snap, each installed and tested on its distributions in GitHub Actions and attached to releases; AUR and Snap Store publishing ready, waiting on the accounts in item 4. |
| 2026-10-10 | Homebrew formula, macOS CI test, and tap repository files prepared (cloud session); waiting on owner steps C1 to C3. The cloud session could not create the tap repository (GitHub: "Resource not accessible by integration"). |
