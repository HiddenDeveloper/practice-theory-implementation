#!/usr/bin/env bash
# The full autonomic loop in one keeper process: the reactive dispatcher +
# reflective loop route closed enactments to the Judge, the Judge and Smoother
# drain their inboxes, and RemSleep runs Memory Recall + Consolidation on its
# schedule. Every closed enactment is worked — somatic ones reactively, all
# autonomic ones (judge, smoother, memory_recall, memory_consolidation)
# reflectively. The practitioner applies source-backed canonical updates
# directly and stages contentious or identity-sensitive changes for review
# (per rule_memory_consolidation_stage_ambiguity). Preview is OFF so the loop
# actually writes.
#
# Neo4j/Qdrant credentials are read from .codex/config.toml by the adapters
# (practice_service_env), so this launcher embeds no secrets.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

export PRACTICE_AUTONOMIC_PROVIDER="${PRACTICE_AUTONOMIC_PROVIDER:-anthropic_cli}"
# Run the full autonomic loop: Judge + Smoother (inbox roles, with the reactive
# dispatcher and the reflective autonomic-history loop) AND RemSleep memory.
# (REMSLEEP_ENABLED keeps the memory loops; dropping REMSLEEP_ONLY turns the
# Judge/Smoother/dispatcher/reflective roles back on — see _selected_roles.)
export PRACTICE_REMSLEEP_ENABLED=1
export PRACTICE_REMSLEEP_INTERVAL_SECONDS="${PRACTICE_REMSLEEP_INTERVAL_SECONDS:-21600}"
# Connect each recall/consolidation dispatch to the long-lived autonomic HTTP
# MCP server (start it with `make autonomic-http-up`) instead of spawning a
# fresh stdio server per dispatch. Set to empty to fall back to stdio.
export PRACTICE_AUTONOMIC_MCP_URL="${PRACTICE_AUTONOMIC_MCP_URL-http://127.0.0.1:7181/mcp}"
# Autonomous keeper applies for real — capture-only preview must be off.
unset PRACTICE_REMSLEEP_PREVIEW || true

exec uv run python -m practice_theory_implementation.autonomic_runner
