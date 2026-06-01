"""Runner for the real autonomic adapters — Anthropic SDK, Claude CLI, or Codex exec.

Long-running counterpart to the verify's bounded `drain`. Picks the adapter
by env var or CLI flag, opens it, runs `run_role_loop` for both Judge and
Smoother concurrently against the trail's inboxes, optionally runs RemSleep's
memory recall/consolidation pipeline on a schedule, and exits on SIGINT/SIGTERM or when
`/tmp/practice-autonomic-quit` appears.

Usage (Anthropic SDK, stdio default):
    PRACTICE_AUTONOMIC_PROVIDER=anthropic \
        uv run --extra anthropic python -m practice_theory_implementation.autonomic_runner

Usage (Anthropic SDK, experimental HTTP — one client per server process):
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
server instead. The HTTP server itself requires PRACTICE_EXPERIMENTAL_HTTP=1
until active practice state is scoped per session.

All three real adapters drive the same role machinery. Judge and Smoother are
inbox-driven; RemSleep Recall is wall-clock-driven; RemSleep Consolidation is
memory-signal-driven. The choice of adapter is the only difference; everything
else — bundle content, policies, brief composition, and MCP surface — is shared.
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
REMSLEEP_ENABLED_ENV = "PRACTICE_REMSLEEP_ENABLED"
REMSLEEP_INTERVAL_ENV = "PRACTICE_REMSLEEP_INTERVAL_SECONDS"
REMSLEEP_SIGNAL_POLL_ENV = "PRACTICE_REMSLEEP_SIGNAL_POLL_SECONDS"
DEFAULT_REMSLEEP_INTERVAL_SECONDS = 6 * 60 * 60
DEFAULT_REMSLEEP_SIGNAL_POLL_SECONDS = 60


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


def _env_flag(name: str, *, default: bool = False) -> bool:
    raw = os.environ.get(name, "").strip().lower()
    if not raw:
        return default
    return raw in ("1", "true", "yes", "on")


def _remsleep_interval_seconds() -> float:
    raw = os.environ.get(REMSLEEP_INTERVAL_ENV, "").strip()
    if not raw:
        return float(DEFAULT_REMSLEEP_INTERVAL_SECONDS)
    try:
        return max(60.0, float(raw))
    except ValueError:
        logger.warning(
            "invalid %s=%r, falling back to %s",
            REMSLEEP_INTERVAL_ENV,
            raw,
            DEFAULT_REMSLEEP_INTERVAL_SECONDS,
        )
        return float(DEFAULT_REMSLEEP_INTERVAL_SECONDS)


def _remsleep_signal_poll_seconds() -> float:
    raw = os.environ.get(REMSLEEP_SIGNAL_POLL_ENV, "").strip()
    if not raw:
        return float(DEFAULT_REMSLEEP_SIGNAL_POLL_SECONDS)
    try:
        return max(10.0, float(raw))
    except ValueError:
        logger.warning(
            "invalid %s=%r, falling back to %s",
            REMSLEEP_SIGNAL_POLL_ENV,
            raw,
            DEFAULT_REMSLEEP_SIGNAL_POLL_SECONDS,
        )
        return float(DEFAULT_REMSLEEP_SIGNAL_POLL_SECONDS)


async def _run_memory_recall_loop(
    adapter: AutonomicAdapter,
    *,
    stop: asyncio.Event,
    interval_seconds: float,
) -> None:
    """Run Memory Recall on a wall-clock schedule."""
    from datetime import UTC, datetime

    from practice_theory_implementation.autonomic_adapters import WorkItem

    await adapter.open()
    try:
        while not stop.is_set():
            logger.info("[memory_recall] scheduled RemSleep recall dispatch")
            try:
                await adapter.dispatch(
                    WorkItem(
                        primary_id=datetime.now(UTC).isoformat(timespec="seconds"),
                        role="memory_recall",
                        dispatch_message=(
                            "Run one RemSleep memory-recall pass. Switch to "
                            "`memory_recall`. Read the RemSleep "
                            "checkpoint, read the current canonical/user context, "
                            "recall unreviewed episodes after the checkpoint, and "
                            "read non-canonical graph nodes updated after the graph "
                            "watermark. Summarize the recalled evidence into "
                            "source-backed candidates, then dispatch a "
                            "memory_signal for each relevant durable change or "
                            "explicit no-op summary. Do not write canonical "
                            "memory and do not record the checkpoint. "
                            "Stop after one recall pass."
                        ),
                    )
                )
            except Exception:
                logger.exception("[memory_recall] RemSleep dispatch failed")
            with contextlib.suppress(TimeoutError):
                await asyncio.wait_for(stop.wait(), timeout=interval_seconds)
    finally:
        await adapter.close()


async def _run_memory_consolidation_signal_loop(
    adapter: AutonomicAdapter,
    *,
    stop: asyncio.Event,
    poll_seconds: float,
) -> None:
    """Dispatch Memory Consolidation work when Memory Recall emits signals."""
    import json

    from practice_theory_implementation.autonomic_adapters import WorkItem
    from practice_theory_implementation.materials import remsleep

    await adapter.open()
    try:
        while not stop.is_set():
            signals = await asyncio.to_thread(
                remsleep.remsleep_read_memory_signals,
                limit=1,
            )
            pending = signals.get("signals", []) if isinstance(signals, dict) else []
            signal = pending[0] if pending else None
            if isinstance(signal, dict) and isinstance(signal.get("id"), str):
                signal_id = signal["id"]
                logger.info("[memory_consolidation] dispatching signal %s", signal_id)
                try:
                    await adapter.dispatch(
                        WorkItem(
                            primary_id=signal_id,
                            role="memory_consolidation",
                            dispatch_message=(
                                "Run one RemSleep memory-consolidation pass. "
                                "Switch to `memory_consolidation`. Consume the "
                                "following memory_signal by reading any cited "
                                "evidence, comparing it with canonicals, and then "
                                "either writing additive non-episodic memory, "
                                "staging an ambiguous/high-impact candidate, or "
                                "recording why no canonical change is warranted. "
                                "Only after the signal has been handled should you "
                                "mark it handled and record the checkpoint if the "
                                "review range is complete. Stop after this signal.\n\n"
                                f"memory_signal:\n{json.dumps(signal, sort_keys=True)}"
                            ),
                        )
                    )
                except Exception:
                    logger.exception(
                        "[memory_consolidation] signal dispatch failed for %s",
                        signal_id,
                    )
                continue
            with contextlib.suppress(TimeoutError):
                await asyncio.wait_for(stop.wait(), timeout=poll_seconds)
    finally:
        await adapter.close()


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
    memory_recall: AutonomicAdapter | None = None
    memory_consolidation: AutonomicAdapter | None = None
    remsleep_interval = _remsleep_interval_seconds()
    signal_poll = _remsleep_signal_poll_seconds()
    if _env_flag(REMSLEEP_ENABLED_ENV):
        missing = [
            bundle_id
            for bundle_id in ("memory_recall", "memory_consolidation")
            if bundle_id not in BUNDLES
        ]
        if missing:
            raise RuntimeError(
                "PRACTICE_REMSLEEP_ENABLED=1 but RemSleep bundle(s) "
                f"{', '.join(missing)!r} are not loaded"
            )
        memory_recall = _build_adapter(provider, "memory_recall")
        memory_consolidation = _build_adapter(provider, "memory_consolidation")

    try:
        # The dispatcher routes closed enactments → judge_inbox and emitted
        # Friction → smoother_inbox while the role loops run. Workers (the
        # adapters' subprocesses) have PRACTICE_DISABLE_DISPATCHER=1 so they
        # don't double-route; routing is owned by this runner's process.
        tasks = [
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
        ]
        if memory_recall is not None and memory_consolidation is not None:
            tasks.append(
                _run_memory_recall_loop(
                    memory_recall,
                    stop=stop,
                    interval_seconds=remsleep_interval,
                )
            )
            tasks.append(
                _run_memory_consolidation_signal_loop(
                    memory_consolidation,
                    stop=stop,
                    poll_seconds=signal_poll,
                )
            )
        await asyncio.gather(*tasks)
    finally:
        store.close()


def main() -> None:
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        sys.exit(130)


if __name__ == "__main__":
    main()
