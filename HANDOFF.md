HANDOFF.md v1.0.0 (Last Rev: 2026-10-03)

# Handoff

Tasks that the cloud coding session cannot finish alone, because they need the repository owner, an organization admin, or a local machine with full push rights. Hand this file to whoever (person or agent) has that access. Work through the open items in order, then update this file: mark the item done with the date, and add anything new.

## Context

- **Repository:** `ILikeHostingServices/Screencap-Documentation-Tool`, MIT License, default branch `main`.
- **Git identity for all commits and tags:** `HostingServices-Owner <HostingServices-Owner@users.noreply.github.com>`.
- **Windows taskbar ID (AppUserModelID) convention** for every app from this organization: `ILHS.<AppName>.<Component>`. This app uses `ILHS.ScreencapDocumentationTool.GUI` (in `screencap_gui.pyw`, `install.ps1`, and the installer test).
- **Versions** are Major.Minor.Patch only. Releases are created by `.github/workflows/release.yml` from `.github/releases/manifest.txt` (one `vX.Y.Z <full commit ID>` line per release) and `.github/releases/vX.Y.Z.md` (the notes). See "Releases And Versions" in `README.md`.
- **What the cloud session can and cannot do:** it can push only to its own working branch, open pull requests, and start workflows. It cannot push to `main`, force-push, create or delete tags, change repository or organization settings, or reach some websites (signpath.org and huggingface.co are blocked by its network policy).

## Open Items

### 1. Merge The Pending Pull Request

- **Who:** repository owner.
- **What:** merge the open pull request from `claude/gifted-ride-nqrkb1` into `main` (v1.14.1: ILHS taskbar ID, this file, and the history rewrite script).
- **How:** on the pull request page choose **Create a merge commit**. Do not use squash or rebase: the release manifest names the exact commit to tag, and squash or rebase would give it a new ID.
- **Done when:** `main` contains `HANDOFF.md` and the checks on the merge commit are green.

### 2. Rewrite The History To The Current Names

- **Who:** anyone with push rights to `main` and to tags (force-push allowed), on a local machine with git, Python 3, and `git-filter-repo` (`python3 -m pip install --user git-filter-repo`).
- **Why:** 31 commits and 17 release tags from before 2026-10-03 are recorded under the previous owner account name, one commit message mentions that name, and older versions of a few files contain the old taskbar ID and test text. This is for consistency, not privacy.
- **What changes:** author, committer, and tagger names and emails become `HostingServices-Owner`; the old name, the old taskbar IDs, and the old test text are replaced in every file version and commit message. Dates and all other content stay the same. Every commit ID changes, so the script also updates `.github/releases/manifest.txt` to the new IDs. GitHub Releases are attached to tag names and stay in place.
- **How:**
  1. Rehearse (pushes nothing): `bash maintenance/rewrite-history.sh`. It makes a full backup (`rewrite-work/backup.bundle`), rewrites a fresh clone, and verifies that no old name remains, all tags still exist, and each tag still points at its release.
  2. Look over `rewrite-work/repo` (`git log --all --format='%h %an %s'`, `git tag -n1`).
  3. Run for real: `PUSH=1 WORK=./rewrite-work-2 bash maintenance/rewrite-history.sh`. This force-pushes `main` and all tags and deletes the stale branch `claude/gifted-ride-nqrkb1`.
- **Rehearsed:** 2026-10-03 by the cloud session on a full copy of the repository with this pull request merged: 45 commits and 19 tags rewritten, all verification checks passed, and the push step was exercised against the copy. It has not been run against GitHub.
- **Afterward:** every existing clone is out of date. Re-clone, or run `git fetch origin && git reset --hard origin/main`. Start a new cloud session for further work rather than continuing an old one.
- **If something goes wrong:** restore from the backup: `git clone backup.bundle restored && cd restored && git push --force --mirror <repo URL>`.
- **Optional:** old commits stay viewable on GitHub by their old ID until GitHub cleans up. To remove them sooner, ask GitHub Support to run garbage collection on the repository.
- **Done when:** the Contributors list on the repository page shows only HostingServices-Owner and Claude (GitHub can take a while to refresh it).

### 3. Publish v1.14.1

- **Who:** repository owner, or the cloud session (it can start workflows).
- **When:** after item 2, so the tag is created on the rewritten history.
- **How:** **Actions > Publish releases > Run workflow** on `main`. It creates the `v1.14.1` tag and release from the manifest and marks it Latest.
- **Done when:** the Releases page shows v1.14.1 as Latest.

### 4. Allow The Cloud Session To Reach Hugging Face And SignPath

- **Who:** repository owner (Claude Code cloud environment settings: environment menu in the session title bar > Edit > Network access).
- **What:** add `huggingface.co`, `*.huggingface.co`, `*.hf.co` (speech model downloads), and `signpath.org`, `*.signpath.io` (code signing documentation and API) to Allowed domains. Changes apply to new sessions.
- **Why:** lets the cloud session test speech recognition with a real model and read SignPath's documentation directly. GitHub's own test machines already have access, so this is a convenience, not a blocker.

### 5. Code Signing Through SignPath Foundation (Roadmap #12)

Goal: a signed single-file `.exe` for Windows, signed for free by SignPath Foundation (publisher shown: SignPath Foundation). Steps marked **Cloud session** can be done by Claude in a normal session; the rest need the owner.

| Step | Who | What |
| --- | --- | --- |
| 5.1 | Owner | Require two-factor authentication for the organization: **Organization settings > Authentication security > Require two-factor authentication**. SignPath requires it for everyone with write access. |
| 5.2 | Cloud session | Add a GitHub Actions workflow that builds an unsigned single-file `.exe` with PyInstaller (Python and Tkinter bundled; FFmpeg, Tesseract, Pandoc, and VLC stay separate installs because of their licenses) and attaches it to each release. Test it on Windows in CI. |
| 5.3 | Cloud session | Add `CODE_SIGNING_POLICY.md` and link it from `README.md`: "Free code signing provided by SignPath.io, certificate by SignPath Foundation"; Committers and reviewers: repository members; Approvers: the owner; Privacy: "This program will not transfer any information to other networked systems unless specifically requested by the user or the person installing or operating it." |
| 5.4 | Owner | Publish a release that includes the unsigned `.exe` (SignPath requires the project to already be released in the form it will sign). |
| 5.5 | Owner | Apply at https://signpath.org/open-source with the repository URL, the MIT License, a short description, the Releases page as the download page, and the link to `CODE_SIGNING_POLICY.md`. Expect a review that can take weeks. Confirm the exact form fields there; the cloud session could not open signpath.org. |
| 5.6 | Owner | After approval, in the SignPath dashboard: set GitHub as the trusted build system for this repository, limited to the build workflow file and to `main` and `v*` tags; create an artifact configuration that signs `.exe` files; use a release signing policy that the owner approves manually. |
| 5.7 | Owner | Add repository secrets **Settings > Secrets and variables > Actions**: `SIGNPATH_API_TOKEN` and `SIGNPATH_ORG_ID`. Only the owner handles the token. |
| 5.8 | Cloud session | Add `signpath/github-action-submit-signing-request` to the build workflow so each release's `.exe` is submitted for signing, approved by the owner, and the signed file is attached to the release. |

## Done

| Date | Item |
| --- | --- |
| 2026-10-03 | Default branch renamed to `main` (owner). |
| 2026-10-03 | Private vulnerability reporting enabled (owner). |
