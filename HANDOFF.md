HANDOFF.md v1.2.0 (Last Rev: 2026-10-04)

# Handoff

Tasks that the cloud coding session cannot finish alone, because they need the repository owner, an organization admin, or a local machine with full push rights. Hand this file to whoever (person or agent) has that access. Work through the open items in order, then update this file: mark the item done with the date, and add anything new.

## Context

- **Repository:** `ILikeHostingServices/Screencap-Documentation-Tool`, MIT License, default branch `main`.
- **Accounts:** `ILHS-Owner` is the organization's working owner account: use it for all merges, settings, releases, and (later) SignPath approvals. The original owner account stays an owner as a backup only; do not merge, commit, or edit files with it, because github.com records those under the account that clicks the button.
- **Git identity for all commits and tags:** `ILHS-Owner <337515992+ILHS-Owner@users.noreply.github.com>` (the account's private GitHub address; never use the account's real email address in commits).
- **Windows taskbar ID (AppUserModelID) convention** for every app from this organization: `ILHS.<AppName>.<Component>`. This app uses `ILHS.ScreencapDocumentationTool.GUI` (in `screencap_gui.pyw`, `install.ps1`, and the installer test).
- **Versions** are Major.Minor.Patch only. Releases are created by `.github/workflows/release.yml` from `.github/releases/manifest.txt` (one `vX.Y.Z <full commit ID>` line per release) and `.github/releases/vX.Y.Z.md` (the notes). See "Releases And Versions" in `README.md`.
- **What the cloud session can and cannot do:** it can push only to its own working branch, open pull requests, and start workflows. It cannot push to `main`, force-push, create or delete tags, change repository, organization, or account settings, or reach some websites (signpath.org and huggingface.co are blocked by its network policy).

## Open Items

### 1. Stop Duplicate Email Notifications For ILHS-Owner

- **Who:** the owner, signed in as `ILHS-Owner`.
- **Why:** both owner accounts receive the same organization and repository emails. The original owner account keeps receiving them; `ILHS-Owner` keeps notifications on github.com only.
- **How:** **Settings > Notifications** (github.com/settings/notifications):
  1. **Automatically watch repositories:** off.
  2. **Subscriptions > Watching** and **Participating, @mentions and custom:** untick **Email**, keep **On GitHub**.
  3. **System > Actions:** untick **Email** (workflow run results).
  4. **Dependabot alerts** and any other **Email** boxes on the page: untick.
  5. On the repository page, **Watch > Participating and @mentions** (or **Ignore**) for each repository it already watches.
- **Done when:** a workflow run or pull request event emails only the original owner account. Account security emails (sign-ins, 2FA) still go to `ILHS-Owner`; GitHub does not allow turning those off, and they are wanted.

### 2. Merge Pull Request #2 As ILHS-Owner

- **Who:** owner, signed in as `ILHS-Owner`.
- **What:** pull request #2 (rewrite script v1.2.0 for the `ILHS-Owner` identity, this file, release tagger, release notes wording).
- **How:** on the pull request page choose **Create a merge commit**. Not squash or rebase: the release manifest names the exact commit for v1.14.1.
- **Done when:** `main` contains this version of `HANDOFF.md`, and the merge commit shows `ILHS-Owner` as its author.

### 3. Rewrite The History To The Current Names

- **Who:** `ILHS-Owner` (or anyone with push rights to `main` and to tags, force-push allowed), on a local machine with git, Python 3, and `git-filter-repo` (`python3 -m pip install --user git-filter-repo`).
- **When:** after item 2. If anything is merged or committed under another name afterward, run it again.
- **Why:** the history uses two earlier author names: 31 commits and 17 release tags from before 2026-10-03 (one of them with a work email address, from a merge on github.com), and later commits and 2 tags under an interim name. One commit message mentions an earlier name, and older versions of a few files contain old taskbar IDs and test text. This is for consistency, not privacy.
- **What changes:** author, committer, and tagger names and emails under either earlier name become `ILHS-Owner <337515992+ILHS-Owner@users.noreply.github.com>` (matched by name, so any email address is replaced too); the earlier names and emails, the old taskbar IDs, and the old test text are replaced in every file version and commit message. Dates and all other content stay the same. Every commit ID changes, so the script also updates `.github/releases/manifest.txt` to the new IDs. GitHub Releases are attached to tag names and stay in place.
- **How:**
  1. Rehearse (pushes nothing): `bash maintenance/rewrite-history.sh`. It makes a full backup (`rewrite-work/backup.bundle`), rewrites a fresh clone, and verifies that no earlier name remains, every `ILHS-Owner` commit uses the private address, all tags still exist, and each tag still points at its release.
  2. Look over `rewrite-work/repo` (`git log --all --format='%h %an <%ae> %s'`, `git tag -n1`).
  3. Run for real: `PUSH=1 WORK=./rewrite-work-2 bash maintenance/rewrite-history.sh`. This force-pushes `main` and all tags and deletes the stale branch `claude/gifted-ride-nqrkb1`.
- **Rehearsed:** 2026-10-04 by the cloud session on a copy of the real repository with pull request #2 merged as `ILHS-Owner`: all commits on `main` and all 19 tags rewritten to `ILHS-Owner`, all verification checks passed, and the push step was exercised against the copy. It has not been run against GitHub.
- **Afterward:** every existing clone is out of date. Re-clone, or run `git fetch origin && git reset --hard origin/main`. Start a new cloud session for further work rather than continuing an old one.
- **If something goes wrong:** restore from the backup: `git clone backup.bundle restored && cd restored && git push --force --mirror <repo URL>`.
- **Known limit:** GitHub keeps a read-only copy of every pull request's commits (`refs/pull/1/head`, `refs/pull/2/head`), which nobody but GitHub can delete. After the rewrite, pull requests #1 and #2 still list their original commits under the earlier names, and old commits stay viewable by their old ID. To remove them (optional), open a request at https://support.github.com asking them to remove the cached pull request refs for pull requests #1 and #2 and run garbage collection on `ILikeHostingServices/Screencap-Documentation-Tool`, because the history was rewritten to change the author name.
- **Done when:** the commit list on `main` and the tags show only `ILHS-Owner` (plus Claude as co-author). The Contributors list can take a while to refresh.

### 4. Publish v1.14.1

- **Who:** owner, or the cloud session (it can start workflows).
- **When:** after item 3, so the tag is created on the rewritten history.
- **How:** **Actions > Publish releases > Run workflow** on `main`. It creates the `v1.14.1` tag (tagger `ILHS-Owner`) and release from the manifest and marks it Latest.
- **Done when:** the Releases page shows v1.14.1 as Latest.

### 5. Allow The Cloud Session To Reach Hugging Face And SignPath

- **Who:** owner (Claude Code cloud environment settings: environment menu in the session title bar > Edit > Network access).
- **What:** add `huggingface.co`, `*.huggingface.co`, `*.hf.co` (speech model downloads), and `signpath.org`, `*.signpath.io` (code signing documentation and API) to Allowed domains. Changes apply to new sessions.
- **Why:** lets the cloud session test speech recognition with a real model and read SignPath's documentation directly. GitHub's own test machines already have access, so this is a convenience, not a blocker.

### 6. Code Signing Through SignPath Foundation (Roadmap #12)

Goal: a signed single-file `.exe` for Windows, signed for free by SignPath Foundation (publisher shown: SignPath Foundation). Steps marked **Cloud session** can be done by Claude in a normal session; the rest need the owner, as `ILHS-Owner`.

| Step | Who | What |
| --- | --- | --- |
| 6.1 | Owner | Require two-factor authentication for the organization: **Organization settings > Authentication security > Require two-factor authentication**. Both owner accounts already use it; this enforces it for anyone added later. SignPath requires it for everyone with write access. |
| 6.2 | Cloud session | Add a GitHub Actions workflow that builds an unsigned single-file `.exe` with PyInstaller (Python and Tkinter bundled; FFmpeg, Tesseract, Pandoc, and VLC stay separate installs because of their licenses) and attaches it to each release. Test it on Windows in CI. |
| 6.3 | Cloud session | Add `CODE_SIGNING_POLICY.md` and link it from `README.md`: "Free code signing provided by SignPath.io, certificate by SignPath Foundation"; Committers and reviewers: repository members; Approvers: `ILHS-Owner`; Privacy: "This program will not transfer any information to other networked systems unless specifically requested by the user or the person installing or operating it." |
| 6.4 | Owner | Publish a release that includes the unsigned `.exe` (SignPath requires the project to already be released in the form it will sign). |
| 6.5 | Owner | Apply at https://signpath.org/open-source with the repository URL, the MIT License, a short description, the Releases page as the download page, and the link to `CODE_SIGNING_POLICY.md`. Expect a review that can take weeks. Confirm the exact form fields there; the cloud session could not open signpath.org. |
| 6.6 | Owner | After approval, in the SignPath dashboard: set GitHub as the trusted build system for this repository, limited to the build workflow file and to `main` and `v*` tags; create an artifact configuration that signs `.exe` files; use a release signing policy that `ILHS-Owner` approves manually. |
| 6.7 | Owner | Add repository secrets **Settings > Secrets and variables > Actions**: `SIGNPATH_API_TOKEN` and `SIGNPATH_ORG_ID`. Only the owner handles the token. |
| 6.8 | Cloud session | Add `signpath/github-action-submit-signing-request` to the build workflow so each release's `.exe` is submitted for signing, approved by the owner, and the signed file is attached to the release. |

## Done

| Date | Item |
| --- | --- |
| 2026-10-03 | Default branch renamed to `main` (owner). |
| 2026-10-03 | Private vulnerability reporting enabled (owner). |
| 2026-10-03 | Pull request #1 (ILHS taskbar ID, this file, the rewrite script) merged with a merge commit (owner). |
| 2026-10-04 | `ILHS-Owner` account created with two-factor authentication, private email (`337515992+ILHS-Owner@users.noreply.github.com`) and command line email protection on, made an organization owner, and connected to Claude (GitHub app installed for the account and the organization). The original owner account kept as a backup owner (owner). |
