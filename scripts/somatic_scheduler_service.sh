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

# Escalation push (LINE): the bot creds now resolve from the shared `setec`
# secrets store on the tailnet — the secret_provider does env-first then setec,
# so simply pointing at the store lets the runner fetch LINE_CHANNEL_ACCESS_TOKEN
# / LINE_DEFAULT_USER_ID at startup. No per-project .env is lifted any more, and
# resolution never goes through an LLM-facing tool. Unset PRACTICE_SETEC_URL (and
# no env LINE vars) → recorded, not pushed. See docs/plans/setec-secrets-setup.md.
export PRACTICE_SETEC_URL="${PRACTICE_SETEC_URL:-https://setec.tail82f84.ts.net}"

exec uv run python -m practice_theory_implementation.autonomic_runner
