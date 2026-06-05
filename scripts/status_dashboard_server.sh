#!/usr/bin/env bash
# Self-refreshing HTTP status dashboard for the autonomic loop: Judge inbox,
# Smoother inbox, open enactments (with age), and unaddressed Frictions. Reads
# the live trail read-only on every request and serves a self-contained HTML
# page that auto-reloads. Open the URL once and leave it up.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

export PRACTICE_DASHBOARD_HOST="${PRACTICE_DASHBOARD_HOST:-127.0.0.1}"
export PRACTICE_DASHBOARD_PORT="${PRACTICE_DASHBOARD_PORT:-7182}"
export PRACTICE_DASHBOARD_REFRESH_SECONDS="${PRACTICE_DASHBOARD_REFRESH_SECONDS:-10}"

exec uv run python -m practice_theory_implementation.status_dashboard_server
