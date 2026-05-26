"""Runner for the real autonomic adapters — Anthropic SDK, Claude CLI, or Codex exec.

Long-running counterpart to the verify's bounded `drain`. Picks the adapter
by env var or CLI flag, opens it, runs `run_role_loop` for both Judge and
Smoother concurrently against the trail's inboxes, and exits on SIGINT/SIGTERM
or when `/tmp/practice-autonomic-quit` appears.

Usage (Anthropic SDK, stdio default):
    PRACTICE_AUTONOMIC_PROVIDER=anthropic \
        uv run --extra anthropic python -m practice_theory_implementation.autonomic_runner

Usage (Anthropic SDK, HTTP — gated on per-session lifespan state):
    PRACTICE_AUTONOMIC_PROVIDER=anthropic \
        PRACTICE_AUTONOMIC_MCP_URL=http://127.0.0.1:7181/mcp/ \
        uv run --extra anthropic python -m practice_theory_implementation.autonomic_runner

Usage (Claude CLI):
    PRACTICE_AUTONOMIC_PROVIDER=anthropic_cli \
        uv run python -m practice_theory_implementation.autonomic_runner

Usage (Codex):
    PRACTICE_AUTONOMIC_PROVIDER=codex \
        uv run python -m practice_theory_implementation.autonomic_runner

PRACTICE_AUTONOMIC_MCP_URL is optional. Unset, each adapter instance spawns
its own stdio MCP server subprocess (Anthropic SDK) or invokes the autonomic
MCP server inline (Claude CLI via `--mcp-config`, Codex via inline
`-c mcp_servers.…`). Set, the adapter connects to a long-lived HTTP MCP
server instead.

All three real adapters drive the same `run_role_loop` against the same
trail inboxes. The choice of adapter is the only difference; everything else
— bundle content, policies, brief composition, consumption marking — is
shared.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import os
import signal
import sys
from pathlib import Path

from practice_theory_implementation.autonomic_adapters import (
    AdapterConfig,
    AutonomicAdapter,
    RolePolicy,
    compose_brief,
    run_role_loop,
)
from practice_theory_implementation.autonomic_dispatcher import dispatcher_task
from practice_theory_implementation.bundles import BUNDLES
from practice_theory_implementation.pools import substrate
from practice_theory_implementation.trail import EnactmentStore

logger = logging.getLogger(__name__)

QUIT_SENTINEL = Path("/tmp/practice-autonomic-quit")  # noqa: S108


def _build_adapter(provider: str, role: str) -> AutonomicAdapter:
    bundle = BUNDLES[role]
    brief = compose_brief(bundle, substrate)
    mcp_url = os.environ.get("PRACTICE_AUTONOMIC_MCP_URL")

    if provider == "anthropic":
        from practice_theory_implementation.autonomic_adapters import (
            AnthropicSDKAdapter,
        )

        # mcp_url is optional. Without it, the adapter spawns a stdio MCP
        # server subprocess per adapter instance — which avoids the shared
        # module-level state under HTTP. With it (and once per-session
        # state lands), HTTP gives one long-lived server many workers
        # connect to concurrently.
        return AnthropicSDKAdapter(
            AdapterConfig(role=role, bundle_id=role, brief=brief, mcp_url=mcp_url),
            model=os.environ.get("PRACTICE_ANTHROPIC_MODEL", "claude-sonnet-4-6"),
            max_turns=int(os.environ.get("PRACTICE_ANTHROPIC_MAX_TURNS", "60")),
        )
    if provider == "anthropic_cli":
        from practice_theory_implementation.autonomic_adapters import (
            ClaudeCliAdapter,
        )

        budget_raw = os.environ.get("PRACTICE_CLAUDE_MAX_BUDGET_USD", "").strip()
        return ClaudeCliAdapter(
            AdapterConfig(role=role, bundle_id=role, brief=brief, mcp_url=mcp_url),
            model=os.environ.get("PRACTICE_CLAUDE_MODEL"),
            max_budget_usd=float(budget_raw) if budget_raw else None,
            effort=os.environ.get("PRACTICE_CLAUDE_EFFORT"),
        )
    if provider == "codex":
        from practice_theory_implementation.autonomic_adapters import (
            CodexExecAdapter,
        )

        return CodexExecAdapter(
            AdapterConfig(role=role, bundle_id=role, brief=brief, mcp_url=mcp_url),
            model=os.environ.get("PRACTICE_CODEX_MODEL"),
            reasoning_effort=os.environ.get("PRACTICE_CODEX_REASONING_EFFORT"),
        )
    raise ValueError(f"unknown PRACTICE_AUTONOMIC_PROVIDER={provider!r}")


async def _watch_sentinel(stop: asyncio.Event) -> None:
    while not stop.is_set():
        if await asyncio.to_thread(QUIT_SENTINEL.exists):
            logger.info("quit sentinel %s observed", QUIT_SENTINEL)
            stop.set()
            return
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(stop.wait(), timeout=1.0)


async def main_async() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    provider = os.environ.get("PRACTICE_AUTONOMIC_PROVIDER", "").strip()
    if provider not in ("anthropic", "anthropic_cli", "codex"):
        raise RuntimeError(
            "Set PRACTICE_AUTONOMIC_PROVIDER to one of: "
            "anthropic, anthropic_cli, codex"
        )

    store = EnactmentStore()
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)

    judge = _build_adapter(provider, "judge")
    smoother = _build_adapter(provider, "smoother")

    try:
        # The dispatcher routes closed enactments → judge_inbox and emitted
        # Friction → smoother_inbox while the role loops run. Workers (the
        # adapters' subprocesses) have PRACTICE_DISABLE_DISPATCHER=1 so they
        # don't double-route; routing is owned by this runner's process.
        await asyncio.gather(
            dispatcher_task(stop, store=store),
            run_role_loop(
                judge,
                RolePolicy(role="judge"),
                store,
                stop=stop,
                worker_id=f"{provider}-judge",
            ),
            run_role_loop(
                smoother,
                RolePolicy(role="smoother"),
                store,
                stop=stop,
                worker_id=f"{provider}-smoother",
            ),
            _watch_sentinel(stop),
        )
    finally:
        store.close()


def main() -> None:
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        sys.exit(130)


if __name__ == "__main__":
    main()
