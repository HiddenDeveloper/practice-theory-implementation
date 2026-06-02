#!/usr/bin/env bash
# Long-lived somatic practice MCP server over streamable HTTP.
# Per-session state (server.py) makes concurrent sessions safe. Default port
# 7180. Service credentials (Neo4j/Qdrant) are loaded from .codex/config.toml
# via practice_service_env so the engagement projection can reach the graph.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# Export the same service env the adapters use (no secrets embedded here).
eval "$(uv run python -c "
from pathlib import Path
import shlex
from practice_theory_implementation.autonomic_adapters import practice_service_env
for k, v in practice_service_env(Path.cwd()).items():
    print(f'export {k}={shlex.quote(v)}')
")"

export PRACTICE_SERVER_MODE=somatic
export PRACTICE_TRANSPORT=http
export PRACTICE_HTTP_HOST="${PRACTICE_HTTP_HOST:-127.0.0.1}"
export PRACTICE_HTTP_PORT="${PRACTICE_SOMATIC_HTTP_PORT:-7180}"
# The dispatcher stays ON (the somatic server ran it under stdio too): when a
# somatic enactment closes it is routed to judge_inbox for the Judge to pick up,
# and emitted Friction to smoother_inbox. Routing is idempotent (INSERT OR
# IGNORE over the shared trail), so if the autonomic server also runs a
# dispatcher the overlap is harmless.

exec uv run python -m practice_theory_implementation.server
