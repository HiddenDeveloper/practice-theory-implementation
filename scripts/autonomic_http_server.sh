#!/usr/bin/env bash
# Long-lived autonomic practice MCP server over streamable HTTP.
# Per-session state (server.py) makes the concurrent role sessions (judge,
# smoother, memory_recall, memory_consolidation) safe on one process. Default
# port 7181. It owns the dispatcher (routing closed enactments -> judge inbox,
# Friction -> smoother inbox); workers that connect must NOT also dispatch.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

eval "$(uv run python -c "
from pathlib import Path
import shlex
from practice_theory_implementation.autonomic_adapters import practice_service_env
for k, v in practice_service_env(Path.cwd()).items():
    print(f'export {k}={shlex.quote(v)}')
")"

export PRACTICE_SERVER_MODE=autonomic
export PRACTICE_TRANSPORT=http
export PRACTICE_HTTP_HOST="${PRACTICE_HTTP_HOST:-127.0.0.1}"
export PRACTICE_HTTP_PORT="${PRACTICE_AUTONOMIC_HTTP_PORT:-7181}"

exec uv run python -m practice_theory_implementation.server
