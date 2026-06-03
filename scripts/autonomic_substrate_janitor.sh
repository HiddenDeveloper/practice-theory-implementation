#!/usr/bin/env bash
# Autonomic substrate janitor.
#
# The autonomic loop (Smoother/PM) writes its self-amendments to substrate/ in
# the working tree. This snapshots those uncommitted edits onto a QUARANTINE
# branch for human review — never onto main, never pushed. The division of
# labour: the loop *proposes* (writes files), this janitor *preserves* (commits
# to quarantine), a human *ratifies* (reviews + merges to main).
#
# It uses git plumbing (a temp index + commit-tree + update-ref) so it does NOT
# touch HEAD or the working tree — the keeper keeps running on main, oblivious.
# Safe to run while the keeper is live: the substrate write path is atomic, so
# git never reads a half-written file.
#
# Review:  git diff main..autonomic/substrate -- substrate/
# Accept:  git merge autonomic/substrate   (after review, on main)
set -euo pipefail

cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

BRANCH="${AUTONOMIC_QUARANTINE_BRANCH:-autonomic/substrate}"
BASE="${AUTONOMIC_QUARANTINE_BASE:-main}"

# Nothing to do if substrate/ has no uncommitted changes (tracked or new).
if git diff --quiet -- substrate/ \
   && [ -z "$(git ls-files --others --exclude-standard -- substrate/)" ]; then
  echo "janitor: no substrate changes to snapshot"
  exit 0
fi

base_commit=$(git rev-parse "$BASE")

# Build the snapshot tree in a throwaway index: main's tree, with substrate/
# overlaid from the working tree. The real index and HEAD are untouched.
tmpindex=$(mktemp)
trap 'rm -f "$tmpindex"' EXIT
export GIT_INDEX_FILE="$tmpindex"
git read-tree "$base_commit"
git add -A -- substrate/
tree=$(git write-tree)

if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
  parent=$(git rev-parse "$BRANCH")
  if [ "$(git rev-parse "$BRANCH^{tree}")" = "$tree" ]; then
    echo "janitor: no change since last snapshot"
    exit 0
  fi
else
  parent="$base_commit"
fi

ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
msg="autonomic: substrate amendments snapshot $ts (base $(git rev-parse --short "$base_commit"))"
commit=$(printf '%s\n' "$msg" \
  | GIT_AUTHOR_NAME="autonomic-loop" GIT_AUTHOR_EMAIL="autonomic@localhost" \
    GIT_COMMITTER_NAME="autonomic-janitor" GIT_COMMITTER_EMAIL="autonomic@localhost" \
    git commit-tree "$tree" -p "$parent")
git update-ref "refs/heads/$BRANCH" "$commit"
echo "janitor: snapshotted substrate -> $BRANCH (${commit:0:12})"
