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

exec uv run python -m practice_theory_implementation.autonomic_runner
