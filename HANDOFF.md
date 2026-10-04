HANDOFF.md v1.3.0 (Last Rev: 2026-10-04)

# Handoff

Tasks that the cloud coding session cannot finish alone, because they need the repository owner, an organization admin, or a local machine with full push rights. Hand this file to whoever (person or agent) has that access. Work through the open items in order, then update this file: mark the item done with the date in the **Done** table, and add anything new.

## Context

### The Project

- **Repository:** `ILikeHostingServices/Screencap-Documentation-Tool` (public), MIT License, default branch `main`. GitHub Actions: `Tests` (every push and pull request, Windows and Linux), `Installers` (installer changes, weekly, on demand), `Publish releases` (manual).
- **What it is:** a Python tool (GUI and command line) that takes a screenshot of every step in a screen recording, using FFmpeg scene detection. Windows 11 is the main target; Linux and macOS work too. See `README.md`.
- **Current release:** v1.14.0 is published as Latest. v1.14.1 (ILHS taskbar ID, `ILHS-Owner` identity) is merged into `main` and listed in the release manifest but not yet published (item 2).

### Accounts And Identity

- **`ILHS-Owner`** is the organization's working owner account: use it for all merges, settings, pushes, releases, and (later) SignPath approvals. Two-factor authentication is on.
- **The original owner account** stays an owner of the organization as a backup only. Do not merge, commit, push, or edit files with it: github.com records those under the account that does them, and the history would need another rewrite.
- **Git identity for every commit and tag:** `ILHS-Owner <337515992+ILHS-Owner@users.noreply.github.com>`. This is the account's private GitHub address; never put the account's real email address in a commit, and never write it into a repository file.
- **Do not write the earlier account names into any repository file.** The rewrite in item 1 replaces them everywhere and then checks that the newest files did not change; a literal earlier name in a file makes that check fail. Refer to "the original owner account" instead.

### Conventions

- **Windows taskbar ID (AppUserModelID)** for every app from this organization: `ILHS.<AppName>.<Component>`. This app uses `ILHS.ScreencapDocumentationTool.GUI` (in `screencap_gui.pyw`, `install.ps1`, and `.github/workflows/installers.yml`).
- **Versions** are Major.Minor.Patch only (`v1.14.1`, never `v1.14` or pre-release suffixes). Every file has a header with its own version and last edit date (YYYY-MM-DD); bump it on every functional change. No em or en dashes in any file.
- **Releases** are created by `.github/workflows/release.yml` from `.github/releases/manifest.txt` (one `vX.Y.Z <full commit ID>` line per release) and `.github/releases/vX.Y.Z.md` (the notes, also copied into `CHANGELOG.md`). `version.py` `RELEASE` must equal the newest `CHANGELOG.md` entry (a test checks it). The workflow only creates tags and releases that do not exist yet; it never deletes or changes existing ones. GitHub only lets the workflow create a tag on a commit whose `.github/workflows/` files are identical to the newest commit's.
- **Merging pull requests:** always **Create a merge commit** (never squash or rebase), signed in as `ILHS-Owner`, because the release manifest names exact commit IDs.

### What The Cloud Session Can And Cannot Do

It can push only to its own working branch (`claude/...`), open pull requests, start workflows, and read public GitHub data. It cannot push to `main`, force-push, create or delete tags, change repository, organization, or account settings, or reach some websites (signpath.org and huggingface.co are blocked by its network policy).

## Open Items

### 1. Rewrite The History To The Current Names

- **Who:** `ILHS-Owner`, or an agent on a local machine signed in to GitHub as `ILHS-Owner`.
- **Why:** the history uses two earlier author names: 32 commits and 17 release tags under the original owner account name (31 commits from before 2026-10-03, plus the github.com merge of pull request #1, which used a work email address), and 15 later commits and 2 tags under an interim name. One commit message mentions an earlier name, and older versions of a few files contain old taskbar IDs and test text. This is for consistency, not privacy.
- **What it changes:** author, committer, and tagger names and emails under either earlier name become `ILHS-Owner <337515992+ILHS-Owner@users.noreply.github.com>` (matched by name, so any email address is replaced too). The earlier names and emails, old taskbar IDs, and old test text are replaced in every file version and commit message. Dates and all other content stay the same. Every commit ID changes, so the script adds one commit that updates `.github/releases/manifest.txt` to the new IDs. GitHub Releases are attached to tag names and stay in place.
- **Already verified:** rehearsed on 2026-10-04 by the cloud session against a full copy of the real repository with pull request #2 merged as `ILHS-Owner`: all 51 resulting commits on `main` and all 19 tags became `ILHS-Owner` with the private address, every check passed, the push step worked against the copy, and the release workflow can still create the v1.14.1 tag afterward. It has not been run against GitHub yet.

#### Before You Start

1. **Use Linux, macOS, or WSL (Ubuntu on Windows).** These are recommended because the script needs `bash` 4+, `git` 2.36+, and `python3`. Git Bash on Windows also works if `python3` runs there; if it does not, create a shim first:

   ```bash
   mkdir -p ~/bin && printf '#!/bin/sh\nexec python "$@"\n' > ~/bin/python3 && chmod +x ~/bin/python3 && export PATH="$HOME/bin:$PATH"
   ```

2. **Install git-filter-repo** and check that git finds it:

   ```bash
   python3 -m pip install --user git-filter-repo
   git filter-repo --version
   ```

   If `git filter-repo` is not found, add pip's user scripts folder to `PATH` (Linux and WSL: `export PATH="$HOME/.local/bin:$PATH"`; Windows: the `Scripts` folder under `%APPDATA%\Python\Python3xx`).
3. **Sign in to GitHub as `ILHS-Owner` for git pushes.** The push rewrites commits that change `.github/workflows/` files, which GitHub only accepts from a credential allowed to change workflows:
   - **GitHub CLI** (simplest): `gh auth login` as `ILHS-Owner`, then `gh auth refresh -s workflow`, then `gh auth setup-git`.
   - **Personal access token** (classic): scopes `repo` and `workflow`. Use it as the password when git asks.
   - Git Credential Manager (Git for Windows) normally has these rights already after a browser sign-in as `ILHS-Owner`.

   `main` has no branch protection, so the force-push is allowed. If a rule is added later, allow force pushes for `ILHS-Owner` during this step.
4. **Make sure nothing is merged or pushed to `main` while this runs.**

#### Run It

```bash
git clone https://github.com/ILikeHostingServices/Screencap-Documentation-Tool.git
cd Screencap-Documentation-Tool

# 1. Rehearsal: backs up, rewrites a fresh clone, verifies. Pushes nothing.
bash maintenance/rewrite-history.sh

# 2. Review the result
git -C rewrite-work/repo log --all --format='%h %an <%ae> %s' | head -20
git -C rewrite-work/repo tag -n1
git -C rewrite-work/repo log --all --format='%an <%ae>' | sort | uniq -c   # expect only ILHS-Owner

# 3. The real run: same steps, then force-pushes main and all tags,
#    and deletes the stale branch claude/gifted-ride-nqrkb1
PUSH=1 WORK=./rewrite-work-2 bash maintenance/rewrite-history.sh
```

The rehearsal must print `OK: no old names anywhere, 19 tags, release manifest updated`. If it prints any `FAIL` line, stop: nothing has been pushed. Report the output to the repository owner or a cloud session.

#### Check It Worked

```bash
git clone https://github.com/ILikeHostingServices/Screencap-Documentation-Tool.git check && cd check
git fetch --tags
git log --format='%an <%ae>' | sort | uniq -c                                   # only ILHS-Owner (merge commits show GitHub as committer, which is expected)
git for-each-ref refs/tags --format='%(taggername) %(taggeremail)' | sort | uniq -c   # 19 tags, all ILHS-Owner
git ls-remote --heads origin                                                     # only main
```

Keep `rewrite-work/backup.bundle` until item 2 is done. To undo everything: `git clone rewrite-work/backup.bundle restored && cd restored && git push --force --mirror https://github.com/ILikeHostingServices/Screencap-Documentation-Tool.git`.

#### Afterward

- Every existing clone is out of date: re-clone, or run `git fetch origin && git reset --hard origin/main`. Start a new cloud session for further work; the old session's branch is deleted.
- **Known limit:** GitHub keeps a read-only copy of every pull request's commits (`refs/pull/1/head`, `refs/pull/2/head`) that only GitHub can delete. Pull requests #1 and #2 keep listing their original commits under the earlier names, and old commits stay viewable by their old ID. Optional cleanup: open a ticket at https://support.github.com while signed in as `ILHS-Owner`:

  > Please remove the cached pull request refs for pull requests #1 and #2 in ILikeHostingServices/Screencap-Documentation-Tool and run garbage collection on the repository. We rewrote the history to change the commit author name and force-pushed main and all tags; the old commits are still reachable through those pull request refs.

- **Done when:** the checks above show only `ILHS-Owner`. The Contributors list on the repository page can take a while to refresh.

### 2. Publish v1.14.1

- **Who:** `ILHS-Owner`, an agent signed in as `ILHS-Owner`, or the cloud session (it can start workflows).
- **When:** after item 1, so the tag is created on the rewritten history.
- **How:** **Actions > Publish releases > Run workflow**, branch `main`. Or with the GitHub CLI: `gh workflow run release.yml --repo ILikeHostingServices/Screencap-Documentation-Tool --ref main`.
- **Check:** the run succeeds; **Releases** shows v1.14.1 as **Latest**; `git ls-remote --tags origin v1.14.1` shows the tag; the tag's tagger is `ILHS-Owner`.

### 3. Update This File In The Repository

- **Who:** whoever finished items 1 and 2, or a new cloud session.
- **What:** move items 1 and 2 to the **Done** table with the date, renumber the rest, and commit as `ILHS-Owner` (through a pull request merged with **Create a merge commit**). Do not write the earlier account names into the file.

### 4. Allow The Cloud Session To Reach Hugging Face And SignPath

- **Who:** owner (Claude Code cloud environment settings: environment menu in the session title bar > Edit > Network access).
- **What:** add `huggingface.co`, `*.huggingface.co`, `*.hf.co` (speech model downloads), and `signpath.org`, `*.signpath.io` (code signing documentation and API) to Allowed domains. Changes apply to new sessions.
- **Why:** lets the cloud session test speech recognition with a real model and read SignPath's documentation directly. GitHub's own test machines already have access, so this is a convenience, not a blocker.

### 5. Code Signing Through SignPath Foundation (Roadmap #12)

Goal: a signed single-file `.exe` for Windows, signed for free by SignPath Foundation (publisher shown: SignPath Foundation). Steps marked **Cloud session** can be done by Claude in a normal session; the rest need the owner, as `ILHS-Owner`. The owner wants some back and forth on the `.exe` before involving SignPath.

| Step | Who | What |
| --- | --- | --- |
| 5.1 | Owner | Require two-factor authentication for the organization: **Organization settings > Authentication security > Require two-factor authentication**. Both owner accounts already use it; this enforces it for anyone added later. SignPath requires it for everyone with write access. |
| 5.2 | Cloud session | Add a GitHub Actions workflow that builds an unsigned single-file `.exe` with PyInstaller (Python and Tkinter bundled; FFmpeg, Tesseract, Pandoc, and VLC stay separate installs because of their licenses) and attaches it to each release. Test it on Windows in CI. |
| 5.3 | Cloud session | Add `CODE_SIGNING_POLICY.md` and link it from `README.md`: "Free code signing provided by SignPath.io, certificate by SignPath Foundation"; Committers and reviewers: repository members; Approvers: `ILHS-Owner`; Privacy: "This program will not transfer any information to other networked systems unless specifically requested by the user or the person installing or operating it." |
| 5.4 | Owner | Publish a release that includes the unsigned `.exe` (SignPath requires the project to already be released in the form it will sign). |
| 5.5 | Owner | Apply at https://signpath.org/open-source with the repository URL, the MIT License, a short description, the Releases page as the download page, and the link to `CODE_SIGNING_POLICY.md`. Expect a review that can take weeks. Confirm the exact form fields there; the cloud session could not open signpath.org. |
| 5.6 | Owner | After approval, in the SignPath dashboard: set GitHub as the trusted build system for this repository, limited to the build workflow file and to `main` and `v*` tags; create an artifact configuration that signs `.exe` files; use a release signing policy that `ILHS-Owner` approves manually. |
| 5.7 | Owner | Add repository secrets **Settings > Secrets and variables > Actions**: `SIGNPATH_API_TOKEN` and `SIGNPATH_ORG_ID`. Only the owner handles the token. |
| 5.8 | Cloud session | Add `signpath/github-action-submit-signing-request` to the build workflow so each release's `.exe` is submitted for signing, approved by the owner, and the signed file is attached to the release. |

## Done

| Date | Item |
| --- | --- |
| 2026-10-03 | Default branch renamed to `main` (owner). |
| 2026-10-03 | Private vulnerability reporting enabled (owner). |
| 2026-10-03 | Pull request #1 (ILHS taskbar ID, this file, the rewrite script) merged with a merge commit (owner). |
| 2026-10-04 | `ILHS-Owner` account created with two-factor authentication, private email (`337515992+ILHS-Owner@users.noreply.github.com`) and command line email protection on, made an organization owner, and connected to Claude (GitHub app installed for the account and the organization). The original owner account kept as a backup owner (owner). |
| 2026-10-04 | Email notifications turned off for `ILHS-Owner` (it keeps notifications on github.com; the original owner account still gets the emails) (owner). |
| 2026-10-04 | Pull request #2 (rewrite script v1.2.0 for `ILHS-Owner`, this file, release tagger) merged as `ILHS-Owner` with a merge commit; the merge commit is authored by `ILHS-Owner` with the private address (owner). |
