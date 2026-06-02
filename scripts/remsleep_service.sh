#!/usr/bin/env bash
# RemSleep as a dedicated unattended keeper: Memory Recall + Memory
# Consolidation only (no Judge/Smoother, no dispatcher). The practitioner
# applies source-backed canonical updates directly and stages contentious or
# identity-sensitive changes for review (per rule_memory_consolidation_stage_
# ambiguity). Preview is intentionally OFF so the loop actually writes.
#
# Neo4j/Qdrant credentials are read from .codex/config.toml by the adapters
# (practice_service_env), so this launcher embeds no secrets.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

export PRACTICE_AUTONOMIC_PROVIDER="${PRACTICE_AUTONOMIC_PROVIDER:-anthropic_cli}"
export PRACTICE_REMSLEEP_ONLY=1
export PRACTICE_REMSLEEP_INTERVAL_SECONDS="${PRACTICE_REMSLEEP_INTERVAL_SECONDS:-21600}"
# Autonomous keeper applies for real — capture-only preview must be off.
unset PRACTICE_REMSLEEP_PREVIEW || true

exec uv run python -m practice_theory_implementation.autonomic_runner
