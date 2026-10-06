HANDOFF.md v1.7.0 (Last Rev: 2026-10-06)

# Handoff

Tasks that the cloud coding session cannot finish alone, because they need the repository owner, an organization admin, or a local machine with full push rights. Hand this file to whoever (person or agent) has that access. Work through the open items in order, then update this file: mark the item done with the date in the **Done** table, and add anything new.

## Context

### The Project

- **Repository:** `ILikeHostingServices/Screencap-Documentation-Tool` (public), MIT License, default branch `main`. GitHub Actions: `Tests` (every push and pull request, Windows and Linux), `Installers` (installer changes, weekly, on demand), `Windows build` (builds and tests the packaged Windows app and its installer on every pull request, and attaches them to releases), `Publish releases` (manual).
- **What it is:** a Python tool (GUI and command line) that takes a screenshot of every step in a screen recording, using FFmpeg scene detection. Windows 11 is the main target; Linux and macOS work too. See `README.md`.
- **Current release:** v1.16.0 (Windows installer) is published as Latest, with the unsigned installer (`...-windows-x64-setup.exe`), the portable zip (`...-windows-x64-portable.zip`), and `SHA256SUMS.txt` attached.
- **Packaged app layout:** PyInstaller one-folder build (`packaging/screencap.spec`): `Screencap Documentation Tool.exe` (GUI), `screencap.exe` (command line), and a shared `_internal` folder. The installer is built with Inno Setup (`packaging/installer.iss`). Never change the installer's `AppId` GUID: Windows uses it to recognize upgrades.

### Accounts And Identity

- **`ILHS-Owner`** is the organization's working owner account: use it for all merges, settings, pushes, releases, and (if code signing is taken up) signing approvals. Two-factor authentication is on.
- **The original owner account** stays an owner of the organization as a backup only. Do not merge, commit, push, or edit files with it: github.com records those under the account that does them, and the history would need another rewrite.
- **Git identity for every commit and tag:** `ILHS-Owner <337515992+ILHS-Owner@users.noreply.github.com>`. This is the account's private GitHub address; never put the account's real email address in a commit, and never write it into a repository file.
- **Do not write the earlier account names into any repository file.** The history has been rewritten so they appear nowhere; keep it that way. If `maintenance/rewrite-history.sh` ever has to run again (for example after a commit under an earlier name), a literal earlier name in a file makes its final check fail. Refer to "the original owner account" instead.

### Conventions

- **Windows taskbar ID (AppUserModelID)** for every app from this organization: `ILHS.<AppName>.<Component>`. This app uses `ILHS.ScreencapDocumentationTool.GUI` (in `screencap_gui.pyw`, `install.ps1`, and `.github/workflows/installers.yml`).
- **Versions** are Major.Minor.Patch only (`v1.14.1`, never `v1.14` or pre-release suffixes). Every file has a header with its own version and last edit date (YYYY-MM-DD); bump it on every functional change. No em or en dashes in any file.
- **Releases** are created by `.github/workflows/release.yml` from `.github/releases/manifest.txt` (one `vX.Y.Z <full commit ID>` line per release) and `.github/releases/vX.Y.Z.md` (the notes, also copied into `CHANGELOG.md`). `version.py` `RELEASE` must equal the newest `CHANGELOG.md` entry (a test checks it). The workflow only creates tags and releases that do not exist yet; it never deletes or changes existing ones. GitHub only lets the workflow create a tag on a commit whose `.github/workflows/` files are identical to the newest commit's.
- **Merging pull requests:** always **Create a merge commit** (never squash or rebase), as `ILHS-Owner`, because the release manifest names exact commit IDs.
- **Standing permission (from the owner, 2026-10-04):** a cloud session may merge its own pull requests once every check is green, as a merge commit, through its GitHub connection, but only while that connection is `ILHS-Owner` (check who opened the pull request first). It still asks the owner before history rewrites, publishing releases, deleting branches or tags, and any repository, organization, or account setting.
- **Local agents** (on the owner's machine) should also make changes through a pull request, not by pushing to `main`, so the tests run first.

### What The Cloud Session Can And Cannot Do

It can push only to its own working branch (`claude/...`), open and (see above) merge pull requests, start workflows, and read public GitHub data. It cannot push to `main`, force-push, create or delete tags, change repository, organization, or account settings, or reach websites outside its network policy (huggingface.co was added on 2026-10-04 and works in sessions started after that).

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
