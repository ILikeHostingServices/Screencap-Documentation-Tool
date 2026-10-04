HANDOFF.md v1.5.0 (Last Rev: 2026-10-04)

# Handoff

Tasks that the cloud coding session cannot finish alone, because they need the repository owner, an organization admin, or a local machine with full push rights. Hand this file to whoever (person or agent) has that access. Work through the open items in order, then update this file: mark the item done with the date in the **Done** table, and add anything new.

## Context

### The Project

- **Repository:** `ILikeHostingServices/Screencap-Documentation-Tool` (public), MIT License, default branch `main`. GitHub Actions: `Tests` (every push and pull request, Windows and Linux), `Installers` (installer changes, weekly, on demand), `Windows build` (builds and tests the packaged Windows app and its installer on every pull request, and attaches them to releases), `Publish releases` (manual).
- **What it is:** a Python tool (GUI and command line) that takes a screenshot of every step in a screen recording, using FFmpeg scene detection. Windows 11 is the main target; Linux and macOS work too. See `README.md`.
- **Current release:** v1.16.0 (Windows installer) is published as Latest, with the unsigned installer (`...-windows-x64-setup.exe`), the portable zip (`...-windows-x64-portable.zip`), and `SHA256SUMS.txt` attached.
- **Packaged app layout:** PyInstaller one-folder build (`packaging/screencap.spec`): `Screencap Documentation Tool.exe` (GUI), `screencap.exe` (command line), and a shared `_internal` folder. The installer is built with Inno Setup (`packaging/installer.iss`). Never change the installer's `AppId` GUID: Windows uses it to recognize upgrades.

### Accounts And Identity

- **`ILHS-Owner`** is the organization's working owner account: use it for all merges, settings, pushes, releases, and (later) SignPath approvals. Two-factor authentication is on.
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

It can push only to its own working branch (`claude/...`), open and (see above) merge pull requests, start workflows, and read public GitHub data. It cannot push to `main`, force-push, create or delete tags, change repository, organization, or account settings, or reach some websites (signpath.org and huggingface.co are blocked by its network policy).

## Open Items

### 1. Optional: Ask GitHub To Drop The Old Pull Request Commits

- **Who:** owner, signed in as `ILHS-Owner`.
- **Will it go away by itself?** No. GitHub keeps pull request refs permanently; only GitHub Support can remove them.
- **Why:** after the history rewrite, GitHub still keeps read-only copies of the original commits of pull requests #1, #2, and #3 (`refs/pull/N/head`), which only GitHub can delete. Those pull requests keep listing commits under the earlier names, and old commits stay viewable by their old ID. Nothing else refers to them.
- **How:** open a ticket at https://support.github.com:

  > Please remove the cached pull request refs for pull requests #1, #2, and #3 in ILikeHostingServices/Screencap-Documentation-Tool and run garbage collection on the repository. We rewrote the history to change the commit author name and force-pushed main and all tags; the old commits are still reachable through those pull request refs.

- **Afterward:** the backup bundle of the old history on the owner's machine can be deleted once the owner is happy with the result.

### 2. Allow The Cloud Session To Reach SignPath

- **Who:** owner (Claude Code cloud environment settings: environment menu in the session title bar > Edit > Network access).
- **What:** add `signpath.org`, `*.signpath.io` (code signing documentation and API) to Allowed domains. Changes apply to new sessions. (Hugging Face is already allowed, see **Done**.)
- **Why:** lets the cloud session read SignPath's documentation directly. GitHub's own test machines already have access, so this is a convenience, not a blocker.

### 3. Code Signing Through SignPath Foundation (Roadmap #12)

Goal: a signed Windows app and installer, signed for free by SignPath Foundation (publisher shown: SignPath Foundation). Steps marked **Cloud session** can be done by Claude in a normal session; the rest need the owner, as `ILHS-Owner`. Steps 3.1, 3.2, and 3.4 are done (see **Done**); next is 3.3, then the owner tries the unsigned installer before applying in 3.5. Signing must cover all three programs: both `.exe` files inside the app (before they are packed) and the setup `.exe`.

| Step | Who | What |
| --- | --- | --- |
| 3.1 | Owner | **Done.** Require two-factor authentication for the organization: **Organization settings > Authentication security > Require two-factor authentication**. Both owner accounts already use it; this enforces it for anyone added later. SignPath requires it for everyone with write access. |
| 3.2 | Cloud session | **Done** (v1.15.0 portable zip, v1.16.0 installer, `.github/workflows/build-windows.yml`). Add a GitHub Actions workflow that builds an unsigned single-file `.exe` with PyInstaller (Python and Tkinter bundled; FFmpeg, Tesseract, Pandoc, and VLC stay separate installs because of their licenses) and attaches it to each release. Test it on Windows in CI. |
| 3.3 | Cloud session | Add `CODE_SIGNING_POLICY.md` and link it from `README.md`: "Free code signing provided by SignPath.io, certificate by SignPath Foundation"; Committers and reviewers: repository members; Approvers: `ILHS-Owner`; Privacy: "This program will not transfer any information to other networked systems unless specifically requested by the user or the person installing or operating it." |
| 3.4 | Owner | **Done** (v1.16.0). Publish a release that includes the unsigned `.exe` (SignPath requires the project to already be released in the form it will sign). |
| 3.5 | Owner | Apply at https://signpath.org/open-source with the repository URL, the MIT License, a short description, the Releases page as the download page, and the link to `CODE_SIGNING_POLICY.md`. Expect a review that can take weeks. Confirm the exact form fields there; the cloud session could not open signpath.org. |
| 3.6 | Owner | After approval, in the SignPath dashboard: set GitHub as the trusted build system for this repository, limited to the build workflow file and to `main` and `v*` tags; create an artifact configuration that signs `.exe` files; use a release signing policy that `ILHS-Owner` approves manually. |
| 3.7 | Owner | Add repository secrets **Settings > Secrets and variables > Actions**: `SIGNPATH_API_TOKEN` and `SIGNPATH_ORG_ID`. Only the owner handles the token. |
| 3.8 | Cloud session | Add `signpath/github-action-submit-signing-request` to `.github/workflows/build-windows.yml` so each release's programs are submitted for signing, approved by the owner, and the signed file is attached to the release. |

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
