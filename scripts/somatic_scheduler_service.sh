#!/usr/bin/env bash
# Generic autonomic somatic scheduler.
#
# Configuration lives in config/somatic_scheduler.yaml by default. Override with
# PRACTICE_AUTONOMIC_CONFIG=/path/to/config.yaml. The runner reads provider,
# model, target somatic practice, cadence, prompt, and log path from that file.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

export PRACTICE_AUTONOMIC_CONFIG="${PRACTICE_AUTONOMIC_CONFIG:-config/somatic_scheduler.yaml}"

# Escalation push (LINE): resolve the two bot creds into the runtime config
# layer from the shared, gitignored per-project .env — the short-term secret
# path in apprenticeship-cognabot/docs/jit-services-and-secrets.md. Only the two
# LINE vars are lifted (not the whole file), and never via an LLM-facing tool.
# Override the source with PRACTICE_LINE_ENV_FILE; unset → recorded, not pushed.
LINE_ENV_FILE="${PRACTICE_LINE_ENV_FILE:-$REPO_ROOT/../apprenticeship-cognabot/config/stonemonkey/.env}"
if [ -f "$LINE_ENV_FILE" ]; then
  for _k in LINE_CHANNEL_ACCESS_TOKEN LINE_DEFAULT_USER_ID; do
    _v="$(grep -E "^${_k}=" "$LINE_ENV_FILE" | head -1 | cut -d= -f2- | sed -e 's/^["'"'"']//' -e 's/["'"'"']$//')"
    [ -n "$_v" ] && export "${_k}=${_v}"
  done
  unset _k _v
fi

exec uv run python -m practice_theory_implementation.autonomic_runner
