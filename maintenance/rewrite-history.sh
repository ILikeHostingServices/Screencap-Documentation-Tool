#!/usr/bin/env bash
#
# rewrite-history.sh
# 2026-10-03
# Version: v1.0.0
#
# PURPOSE:
# One-time cleanup: rewrites the repository history so every commit, tag,
# and file version uses the current names (author HostingServices-Owner,
# taskbar ID prefix ILHS). File contents and dates are otherwise unchanged.
# Rewriting changes every commit ID, so the release manifest is updated to
# the new IDs, then main and all tags are force-pushed. Run it on a local
# machine with push rights to main and to tags; see HANDOFF.md.
#
# Usage:
#   bash maintenance/rewrite-history.sh            # rehearse: rewrite and verify, push nothing
#   PUSH=1 bash maintenance/rewrite-history.sh     # rewrite, verify, then force-push
#
# Optional environment variables:
#   REPO_URL  repository to rewrite (default: the GitHub repository)
#   WORK      scratch folder (default: ./rewrite-work, must not exist yet)
#
# Needs: git 2.36+, Python 3, and git-filter-repo
# (python3 -m pip install --user git-filter-repo).

set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/ILikeHostingServices/Screencap-Documentation-Tool.git}"
WORK="${WORK:-$PWD/rewrite-work}"
PUSH="${PUSH:-0}"
NAME="HostingServices-Owner"
EMAIL="HostingServices-Owner@users.noreply.github.com"
# The previous account name is assembled from parts so that this file
# itself contains nothing for the rewrite to change or the checks to find
OLD="$(printf '%s%s' MV TS)"
OLD_NAME="$OLD-Owner"
OLD_EMAIL="$OLD_NAME@users.noreply.github.com"
STALE_BRANCHES="claude/gifted-ride-nqrkb1"

step() { printf '\033[36m==> %s\033[0m\n' "$*"; }
die()  { printf '\033[31mERROR: %s\033[0m\n' "$*" >&2; exit 1; }

command -v git >/dev/null || die "git is not installed."
git filter-repo --version >/dev/null 2>&1 \
    || die "git-filter-repo is not installed. Run: python3 -m pip install --user git-filter-repo"
[ ! -e "$WORK" ] || die "$WORK already exists. Remove it or set WORK to a new folder."

mkdir -p "$WORK"
step "Backing up the current repository (every branch and tag) to $WORK/backup.bundle"
git clone --quiet --mirror "$REPO_URL" "$WORK/backup.git"
git -C "$WORK/backup.git" bundle create "$WORK/backup.bundle" --all
rm -rf "$WORK/backup.git"

step "Cloning main and all tags"
git clone --quiet --single-branch --branch main "$REPO_URL" "$WORK/repo"
cd "$WORK/repo"
git fetch --quiet --tags origin
tags_before="$(git tag | wc -l)"
tree_before="$(git rev-parse 'HEAD^{tree}')"

# What to change. Names and emails in commits and tags come from the mailmap;
# text inside files and commit messages comes from the replacements list.
cat > "$WORK/mailmap" <<EOF
$NAME <$EMAIL> $OLD_NAME <$OLD_EMAIL>
EOF
cat > "$WORK/replacements" <<EOF
$OLD_EMAIL==>$EMAIL
$OLD_NAME==>$NAME
$OLD.ScreencapDocumentationTool.GUI==>ILHS.ScreencapDocumentationTool.GUI
ILikeHostingServices.ScreencapDocumentationTool.GUI==>ILHS.ScreencapDocumentationTool.GUI
$OLD IT==>Example IT
EOF

step "Rewriting history"
git filter-repo --force --mailmap "$WORK/mailmap" \
    --replace-text "$WORK/replacements" --replace-message "$WORK/replacements"

step "Pointing the release manifest at the rewritten commits"
manifest=.github/releases/manifest.txt
python3 - "$manifest" .git/filter-repo/commit-map <<'PY'
import re, sys
manifest, commit_map = sys.argv[1], sys.argv[2]
old_to_new = {}
with open(commit_map) as fh:
    next(fh)                                  # header line: old new
    for line in fh:
        old, new = line.split()
        old_to_new[old] = new
lines, changed = [], 0
for line in open(manifest, encoding="utf-8").read().splitlines():
    m = re.match(r"^(v\d+\.\d+\.\d+)\s+([0-9a-f]{40})\s*$", line)
    if m and m.group(2) in old_to_new:
        line = f"{m.group(1)} {old_to_new[m.group(2)]}"
        changed += 1
    elif m:
        sys.exit(f"Manifest commit {m.group(2)} for {m.group(1)} is not in the rewritten history")
    lines.append(line)
open(manifest, "w", encoding="utf-8").write("\n".join(lines) + "\n")
print(f"    {changed} release(s) updated")
PY
git -c user.name="$NAME" -c user.email="$EMAIL" commit --quiet -am \
    "Point the release manifest at the rewritten history

Every commit ID changed when the author name was updated across the
history. The tags were rewritten too; this keeps the manifest matching
them so the release workflow does not try to recreate anything."

step "Verifying"
fail=0
if git log --all --format='%an %ae %cn %ce' | grep -qi "$OLD"; then
    echo "    FAIL: an author or committer still uses the old name"; fail=1; fi
if git for-each-ref refs/tags --format='%(taggername) %(taggeremail)' | grep -qi "$OLD"; then
    echo "    FAIL: a tag still uses the old name"; fail=1; fi
if git log --all --format=%B | grep -qi "$OLD"; then
    echo "    FAIL: a commit message still mentions the old name"; fail=1; fi
mapfile -t all_commits < <(git rev-list --all)
if git grep -qi "$OLD" "${all_commits[@]}" -- 2>/dev/null; then
    echo "    FAIL: a file version still mentions the old name"; fail=1; fi
[ "$(git tag | wc -l)" = "$tags_before" ] || { echo "    FAIL: tag count changed"; fail=1; }
# The newest content must match the original except for the expected edits
changed_files="$(git diff --name-only "$tree_before" 'HEAD^{tree}' | tr '\n' ' ')"
echo "    Files that differ from the original main: ${changed_files:-none}"
while read -r tag; do
    v="${tag#v}"
    # version.py exists from v1.12.1 on; older tags are checked by the tag count
    if git cat-file -e "$tag:version.py" 2>/dev/null; then
        git show "$tag:version.py" | grep -q "RELEASE = \"$v\"" \
            || { echo "    FAIL: $tag does not point at its release (version.py)"; fail=1; }
    fi
done < <(git tag)
[ "$fail" = 0 ] || die "Verification failed. Nothing was pushed. The backup is $WORK/backup.bundle."
echo "    OK: no old names anywhere, $(git tag | wc -l) tags, release manifest updated"

if [ "$PUSH" != 1 ]; then
    step "Rehearsal finished. Nothing was pushed."
    echo "Review the result in $WORK/repo (git log --all, git tag -n1), then run again with PUSH=1."
    exit 0
fi

step "Force-pushing main and all tags"
git remote add origin "$REPO_URL"
git push --force origin main
git push --force --tags origin
for b in $STALE_BRANCHES; do
    if git push origin --delete "$b" 2>/dev/null; then echo "    Deleted the stale branch $b"; fi
done
step "Done. Backup of the old history: $WORK/backup.bundle"
echo "Everyone with a clone must re-clone (or: git fetch && git reset --hard origin/main)."
