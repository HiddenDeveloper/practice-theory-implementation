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
# By default this is a long-lived PM2 service. Set
# AUTONOMIC_JANITOR_ONESHOT=1 to run exactly one snapshot pass and exit.
#
# Review:  git diff main..autonomic/substrate -- substrate/
# Accept:  git merge autonomic/substrate   (after review, on main)
set -euo pipefail

cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

BRANCH="${AUTONOMIC_QUARANTINE_BRANCH:-autonomic/substrate}"
BASE="${AUTONOMIC_QUARANTINE_BASE:-main}"
INTERVAL_SECONDS="${AUTONOMIC_JANITOR_INTERVAL_SECONDS:-900}"

snapshot_once() {
  # Nothing to do if substrate/ has no uncommitted changes (tracked or new).
  if git diff --quiet -- substrate/ \
     && [ -z "$(git ls-files --others --exclude-standard -- substrate/)" ]; then
    echo "janitor: no substrate changes to snapshot"
    return 0
  fi

  local base_commit
  base_commit=$(git rev-parse "$BASE")

  # Build the snapshot tree in a throwaway index: main's tree, with substrate/
  # overlaid from the working tree. The real index and HEAD are untouched.
  local tmpindex tree parent ts msg commit status  # cspell:ignore tmpindex
  tmpindex=$(mktemp)
  status=0
  (
    export GIT_INDEX_FILE="$tmpindex"
    git read-tree "$base_commit"
    git add -A -- substrate/
    tree=$(git write-tree)

    if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
      parent=$(git rev-parse "$BRANCH")
      if [ "$(git rev-parse "$BRANCH^{tree}")" = "$tree" ]; then
        echo "janitor: no change since last snapshot"
        return 0
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
  ) || status=$?
  rm -f "$tmpindex"
  return "$status"
}

# Auto-ratify mode (AUTONOMIC_JANITOR_AUTORATIFY=1): instead of staging to the
# quarantine branch for a human to merge, commit the loop's substrate/ edits
# directly onto the live branch — no human in the loop. The loop's edits are
# already in force the moment they are written (git is only the durable record),
# so this removes a bookkeeping-only human step, not a runtime gate. Oversight
# stays in the in-loop gates + the Judge re-examining authoring + git revert.
#
# Scoped to substrate/ (never -A), authored as autonomic-loop, as discrete
# revertible commits. PRECONDITION: the working tree's uncommitted substrate/
# must be genuine loop output — a clean human/loop baseline must already be
# committed, or human WIP would be mislabelled as the loop's.
autoratify_once() {
  if git diff --quiet -- substrate/ \
     && [ -z "$(git ls-files --others --exclude-standard -- substrate/)" ]; then
    echo "janitor: no substrate changes to ratify"
    return 0
  fi
  local branch
  branch=$(git symbolic-ref --short -q HEAD || true)
  if [ -z "$branch" ]; then
    echo "janitor: HEAD is detached; refusing to auto-ratify"
    return 0
  fi
  git add -- substrate/
  if git diff --cached --quiet -- substrate/; then
    echo "janitor: nothing staged after add; skipping"
    return 0
  fi
  local ts msg
  ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  msg="autonomic: substrate self-amendment $ts"
  GIT_AUTHOR_NAME="autonomic-loop" GIT_AUTHOR_EMAIL="autonomic@localhost" \
  GIT_COMMITTER_NAME="autonomic-janitor" GIT_COMMITTER_EMAIL="autonomic@localhost" \
    git commit -q -m "$msg" -- substrate/
  echo "janitor: auto-ratified substrate -> $branch ($(git rev-parse --short HEAD))"
}

pass_once() {
  if [ "${AUTONOMIC_JANITOR_AUTORATIFY:-0}" = "1" ]; then
    autoratify_once
  else
    snapshot_once
  fi
}

if [ "${AUTONOMIC_JANITOR_ONESHOT:-0}" = "1" ]; then
  pass_once
  exit 0
fi

mode="quarantine"; [ "${AUTONOMIC_JANITOR_AUTORATIFY:-0}" = "1" ] && mode="auto-ratify"
echo "janitor: starting substrate $mode loop every ${INTERVAL_SECONDS}s"
while true; do
  pass_once
  sleep "$INTERVAL_SECONDS"
done
