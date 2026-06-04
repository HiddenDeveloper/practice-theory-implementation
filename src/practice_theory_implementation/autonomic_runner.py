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
    WorkItem,
    _record_usage_and_close_consumer,
    _resolve_consumer_id,
    compose_brief,
    run_role_loop,
)
from practice_theory_implementation.autonomic_dispatcher import dispatcher_task
from practice_theory_implementation.bundles import BUNDLES
from practice_theory_implementation.harness_errors import (
    CircuitBreaker,
    observe_dispatch,
)
from practice_theory_implementation.observability import (
    annotate_dispatch_result,
    autonomic_dispatch_span,
)
from practice_theory_implementation.pools import substrate
from practice_theory_implementation.trail import EnactmentStore

logger = logging.getLogger(__name__)

QUIT_SENTINEL = Path("/tmp/practice-autonomic-quit")  # noqa: S108
REMSLEEP_ENABLED_ENV = "PRACTICE_REMSLEEP_ENABLED"
REMSLEEP_ONLY_ENV = "PRACTICE_REMSLEEP_ONLY"
REMSLEEP_INTERVAL_ENV = "PRACTICE_REMSLEEP_INTERVAL_SECONDS"
REMSLEEP_SIGNAL_POLL_ENV = "PRACTICE_REMSLEEP_SIGNAL_POLL_SECONDS"
REMSLEEP_STARTUP_DELAY_ENV = "PRACTICE_REMSLEEP_STARTUP_DELAY_SECONDS"
REMSLEEP_MAX_BACKLOG_ENV = "PRACTICE_REMSLEEP_MAX_AUTONOMIC_BACKLOG"
REMSLEEP_BACKLOG_RETRY_ENV = "PRACTICE_REMSLEEP_BACKLOG_RETRY_SECONDS"
REFLECTIVE_INTERVAL_ENV = "PRACTICE_REFLECTIVE_INTERVAL_SECONDS"
DEFAULT_REMSLEEP_INTERVAL_SECONDS = 6 * 60 * 60
DEFAULT_REMSLEEP_SIGNAL_POLL_SECONDS = 60
DEFAULT_REMSLEEP_STARTUP_DELAY_SECONDS = 5 * 60
DEFAULT_REMSLEEP_MAX_AUTONOMIC_BACKLOG = 10
DEFAULT_REMSLEEP_BACKLOG_RETRY_SECONDS = 5 * 60
# The reflective loop runs on its own (slow) timescale, distinct from the
# reactive dispatcher's seconds-scale poll. Hourly by default — see
# trail.route_autonomic_history_to_judge_inbox and the strange-loop essay.
DEFAULT_REFLECTIVE_INTERVAL_SECONDS = 60 * 60


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


def _selected_roles() -> tuple[bool, bool]:
    """Decide which loops run, from the env flags. Pure, so it is unit-testable.

    Returns ``(run_inbox_roles, run_remsleep)``. RemSleep-only
    (``PRACTICE_REMSLEEP_ONLY``) is a focused keeper: just the memory loops, no
    Judge/Smoother and no dispatcher (the dispatcher only routes the Judge/
    Smoother inboxes this process never uses). It implies RemSleep enabled.
    Otherwise Judge+Smoother always run, and RemSleep runs when
    ``PRACTICE_REMSLEEP_ENABLED`` is set.
    """
    remsleep_only = _env_flag(REMSLEEP_ONLY_ENV)
    run_inbox_roles = not remsleep_only
    run_remsleep = remsleep_only or _env_flag(REMSLEEP_ENABLED_ENV)
    return run_inbox_roles, run_remsleep


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


def _env_float(
    name: str,
    *,
    default: float,
    minimum: float = 0.0,
) -> float:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return max(minimum, float(raw))
    except ValueError:
        logger.warning("invalid %s=%r, falling back to %s", name, raw, default)
        return default


def _env_int(
    name: str,
    *,
    default: int,
    minimum: int | None = None,
) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        logger.warning("invalid %s=%r, falling back to %s", name, raw, default)
        return default
    return max(minimum, value) if minimum is not None else value


def _remsleep_startup_delay_seconds() -> float:
    return _env_float(
        REMSLEEP_STARTUP_DELAY_ENV,
        default=float(DEFAULT_REMSLEEP_STARTUP_DELAY_SECONDS),
    )


def _remsleep_backlog_retry_seconds() -> float:
    return _env_float(
        REMSLEEP_BACKLOG_RETRY_ENV,
        default=float(DEFAULT_REMSLEEP_BACKLOG_RETRY_SECONDS),
        minimum=10.0,
    )


def _remsleep_max_autonomic_backlog() -> int:
    return _env_int(
        REMSLEEP_MAX_BACKLOG_ENV,
        default=DEFAULT_REMSLEEP_MAX_AUTONOMIC_BACKLOG,
    )


def _autonomic_inbox_backlog(store: EnactmentStore) -> int:
    return store.pending_judge_inbox_count() + store.pending_smoother_inbox_count()


def _reflective_interval_seconds() -> float:
    raw = os.environ.get(REFLECTIVE_INTERVAL_ENV, "").strip()
    if not raw:
        return float(DEFAULT_REFLECTIVE_INTERVAL_SECONDS)
    try:
        return max(60.0, float(raw))
    except ValueError:
        logger.warning(
            "invalid %s=%r, falling back to %s",
            REFLECTIVE_INTERVAL_ENV,
            raw,
            DEFAULT_REFLECTIVE_INTERVAL_SECONDS,
        )
        return float(DEFAULT_REFLECTIVE_INTERVAL_SECONDS)


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


async def _run_reflective_judge_loop(
    store: EnactmentStore,
    *,
    stop: asyncio.Event,
    interval_seconds: float,
) -> None:
    """Route autonomic history into the Judge inbox on a slow schedule.

    The reflective half of the two-loop design. The reactive dispatcher routes
    only somatic completions; this loop, in its own (much slower) time, hands
    the Judge the closed autonomic enactments — its own and the Smoother's —
    to examine. Pure routing, so it needs only the store, not an adapter; the
    Judge's run_role_loop then claims and judges what this routes. See
    trail.route_autonomic_history_to_judge_inbox and the strange-loop essay.

    Watermark: the loop only examines autonomic enactments closed since a
    moving cutoff that starts at boot and advances each pass, so it never
    re-grinds pre-existing autonomic history (an already-audited, already-fixed
    backlog). In-memory by design — on restart we resume from "now", not from
    the whole backlog. Reactive somatic routing is unaffected; every somatic
    enactment is still examined. (Routing is INSERT OR IGNORE, so the watermark
    is an efficiency/scope bound, not a correctness gate.)
    """
    from datetime import UTC, datetime

    since = datetime.now(UTC).isoformat(timespec="microseconds")
    while not stop.is_set():
        pass_start = datetime.now(UTC).isoformat(timespec="microseconds")
        try:
            from practice_theory_implementation.judge_triage import triage_and_route

            summary = await asyncio.to_thread(
                triage_and_route, store, mode="autonomic", since=since
            )
            since = pass_start  # advance only on success; a failure retries the window
            if summary.examined:
                logger.info(
                    "[reflective] triaged autonomic history since watermark: "
                    "judge_inbox +%d friction +%d clean %d",
                    summary.ambiguous,
                    summary.friction,
                    summary.clean,
                )
        except Exception:
            logger.exception("[reflective] triage failed; continuing")
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(stop.wait(), timeout=interval_seconds)


async def _run_memory_recall_loop(
    adapter: AutonomicAdapter,
    store: EnactmentStore,
    *,
    stop: asyncio.Event,
    interval_seconds: float,
    startup_delay_seconds: float = 0.0,
    max_autonomic_backlog: int = -1,
    backlog_retry_seconds: float = 300.0,
    breaker: CircuitBreaker | None = None,
) -> None:
    """Run Memory Recall on a wall-clock schedule."""
    import time as _time
    from datetime import UTC, datetime

    await adapter.open()
    try:
        if startup_delay_seconds > 0:
            logger.info(
                "[memory_recall] startup delay %.1fs before first dispatch",
                startup_delay_seconds,
            )
            with contextlib.suppress(TimeoutError):
                await asyncio.wait_for(stop.wait(), timeout=startup_delay_seconds)
        while not stop.is_set():
            if max_autonomic_backlog >= 0:
                backlog = _autonomic_inbox_backlog(store)
                if backlog > max_autonomic_backlog:
                    logger.info(
                        "[memory_recall] deferring: autonomic inbox backlog %d > %d",
                        backlog,
                        max_autonomic_backlog,
                    )
                    with contextlib.suppress(TimeoutError):
                        await asyncio.wait_for(stop.wait(), timeout=backlog_retry_seconds)
                    continue
            logger.info("[memory_recall] scheduled RemSleep recall dispatch")
            dispatch_started = datetime.now(UTC).isoformat(timespec="microseconds")
            work = WorkItem(
                primary_id=datetime.now(UTC).isoformat(timespec="seconds"),
                role="memory_recall",
                dispatch_message=(
                    "Run one RemSleep memory-recall pass. Switch to "
                    "`memory_recall`, then read the checkpoint, the "
                    "current canonical/user context, the unreviewed "
                    "episodes after the checkpoint, and the non-canonical "
                    "graph nodes updated after the graph watermark. Judge "
                    "what you read and dispatch memory_signals "
                    "accordingly. Stop after one recall pass."
                ),
            )
            t0 = _time.monotonic()
            with autonomic_dispatch_span(
                role=adapter.config.role,
                bundle_id=adapter.config.bundle_id,
                primary_id=work.primary_id,
                worker_id="memory-recall-scheduler",
                metadata=work.metadata,
            ) as span:
                try:
                    await adapter.dispatch(work)
                    consumer_id = _resolve_consumer_id(
                        store, adapter.config.bundle_id, dispatch_started
                    )
                    dispatch_ms = int((_time.monotonic() - t0) * 1000)
                    if consumer_id:
                        try:
                            _record_usage_and_close_consumer(
                                store,
                                adapter,
                                consumer_id,
                                dispatch_ms=dispatch_ms,
                            )
                        except Exception:
                            logger.exception(
                                "[memory_recall] usage/finalize failed for %s",
                                consumer_id,
                            )
                        annotate_dispatch_result(
                            span,
                            status="ok",
                            consumer_id=consumer_id,
                            usage=getattr(adapter, "last_usage", None),
                            dispatch_ms=dispatch_ms,
                        )
                    else:
                        annotate_dispatch_result(
                            span,
                            status="no_consumer",
                            usage=getattr(adapter, "last_usage", None),
                            dispatch_ms=dispatch_ms,
                            error="no consumer id resolved",
                        )
                except Exception as exc:
                    annotate_dispatch_result(span, status="error", error=str(exc))
                    logger.exception("[memory_recall] RemSleep dispatch failed")
            if observe_dispatch(
                breaker, getattr(adapter, "last_error", None), on_stop_signal=stop.set
            ):
                break
            with contextlib.suppress(TimeoutError):
                await asyncio.wait_for(stop.wait(), timeout=interval_seconds)
    finally:
        await adapter.close()


async def _run_memory_consolidation_signal_loop(
    adapter: AutonomicAdapter,
    store: EnactmentStore,
    *,
    stop: asyncio.Event,
    poll_seconds: float,
    breaker: CircuitBreaker | None = None,
) -> None:
    """Dispatch Memory Consolidation work when Memory Recall emits signals."""
    import json
    import time as _time
    from datetime import UTC, datetime

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
                dispatch_started = datetime.now(UTC).isoformat(timespec="microseconds")
                work = WorkItem(
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
                    metadata={"memory_signal_id": signal_id},
                )
                t0 = _time.monotonic()
                with autonomic_dispatch_span(
                    role=adapter.config.role,
                    bundle_id=adapter.config.bundle_id,
                    primary_id=work.primary_id,
                    worker_id="memory-consolidation-signal",
                    metadata=work.metadata,
                ) as span:
                    try:
                        await adapter.dispatch(work)
                        consumer_id = _resolve_consumer_id(
                            store, adapter.config.bundle_id, dispatch_started
                        )
                        dispatch_ms = int((_time.monotonic() - t0) * 1000)
                        if consumer_id:
                            try:
                                _record_usage_and_close_consumer(
                                    store,
                                    adapter,
                                    consumer_id,
                                    dispatch_ms=dispatch_ms,
                                )
                            except Exception:
                                logger.exception(
                                    "[memory_consolidation] usage/finalize failed for %s",
                                    consumer_id,
                                )
                            annotate_dispatch_result(
                                span,
                                status="ok",
                                consumer_id=consumer_id,
                                usage=getattr(adapter, "last_usage", None),
                                dispatch_ms=dispatch_ms,
                            )
                        else:
                            annotate_dispatch_result(
                                span,
                                status="no_consumer",
                                usage=getattr(adapter, "last_usage", None),
                                dispatch_ms=dispatch_ms,
                                error="no consumer id resolved",
                            )
                    except Exception as exc:
                        annotate_dispatch_result(span, status="error", error=str(exc))
                        logger.exception(
                            "[memory_consolidation] signal dispatch failed for %s",
                            signal_id,
                        )
                if observe_dispatch(
                    breaker,
                    getattr(adapter, "last_error", None),
                    on_stop_signal=stop.set,
                ):
                    break
                continue
            with contextlib.suppress(TimeoutError):
                await asyncio.wait_for(stop.wait(), timeout=poll_seconds)
    finally:
        await adapter.close()


def _invariant_audit_poll_seconds() -> float:
    return _env_float("PRACTICE_INVARIANT_AUDIT_POLL_SECONDS", default=30.0, minimum=5.0)


def _invariant_audit_cooldown_seconds() -> float:
    return _env_float(
        "PRACTICE_INVARIANT_AUDIT_COOLDOWN_SECONDS", default=300.0, minimum=0.0
    )


def _invariant_audit_brief(firings: list[dict[str, object]]) -> str:
    """Build the audit dispatch from a batch of unaudited firings + their rules."""
    from practice_theory_implementation.substrate_loader import loaded

    invariants = loaded().substrate.invariants
    lines = []
    for f in firings:
        inv = invariants.get(str(f["invariant_id"]))
        rule = (
            f"forbid_when={inv.forbid_when!r}; status={inv.status}"
            if inv is not None
            else "(rule not found / tombstoned)"
        )
        lines.append(
            f"- invariant `{f['invariant_id']}` fired on enactment "
            f"`{f['enactment_id']}`, raising friction `{f['friction_kind']}` "
            f"(id {f['friction_id']}). Rule: {rule}"
        )
    body = "\n".join(lines)
    return (
        "# Invariant audit\n\n"
        "The loop is idle. Review whether these governed deterministic invariants "
        "are still firing correctly. Each one already detected AND auto-resolved its "
        "friction with no LLM; your task is oversight of the rules themselves, not of "
        "the underlying enactments.\n\n"
        "For each firing, judge whether the rule is sound, or whether it is a false "
        "positive, stale, or too blunt. If a rule looks wrong, emit_friction naming "
        "the invariant_id in observation_data with the reason, so the Smoother can "
        "amend_invariant or tombstone_invariant it. If the rules are firing correctly, "
        "record a no-finding. Do not re-judge the underlying enactments.\n\n"
        f"Firings under review:\n{body}\n"
    )


async def _run_invariant_audit_loop(
    adapter: AutonomicAdapter,
    store: EnactmentStore,
    *,
    stop: asyncio.Event,
    poll_seconds: float,
    cooldown_seconds: float,
    batch_limit: int = 20,
    breaker: CircuitBreaker | None = None,
) -> None:
    """Idle-triggered audit of the governed invariants (judgement over the rules).

    Runs only when both inboxes are empty (the loop has cleared its reactive
    work) AND there are unaudited firings — so the audit never competes with
    real-time Judge/Smoother dispatches, and there is always something to review.
    A cooldown batches firings instead of auditing one at a time. The single LLM
    in the determinable path, by design.
    """
    import time as _time
    from datetime import UTC, datetime

    await adapter.open()
    last_audit = 0.0
    try:
        while not stop.is_set():
            backlog = _autonomic_inbox_backlog(store)
            cooling = (_time.monotonic() - last_audit) < cooldown_seconds
            firings = (
                store.unaudited_invariant_firings(limit=batch_limit)
                if backlog == 0 and not cooling
                else []
            )
            if not firings:
                with contextlib.suppress(TimeoutError):
                    await asyncio.wait_for(stop.wait(), timeout=poll_seconds)
                continue
            logger.info(
                "[invariant_audit] idle (inboxes empty); reviewing %d firing(s)",
                len(firings),
            )
            dispatch_started = datetime.now(UTC).isoformat(timespec="microseconds")
            work = WorkItem(
                primary_id=dispatch_started,
                role="invariant_audit",
                dispatch_message=_invariant_audit_brief(firings),
            )
            t0 = _time.monotonic()
            with autonomic_dispatch_span(
                role=adapter.config.role,
                bundle_id=adapter.config.bundle_id,
                primary_id=work.primary_id,
                worker_id="invariant-audit",
                metadata={"firings": len(firings)},
            ) as span:
                try:
                    await adapter.dispatch(work)
                    consumer_id = _resolve_consumer_id(
                        store, adapter.config.bundle_id, dispatch_started
                    )
                    dispatch_ms = int((_time.monotonic() - t0) * 1000)
                    if consumer_id:
                        # Only mark reviewed once a real audit enactment landed.
                        for f in firings:
                            store.mark_invariant_firing_audited(
                                str(f["invariant_id"]),
                                str(f["enactment_id"]),
                                audited_by_enactment_id=consumer_id,
                            )
                        with contextlib.suppress(Exception):
                            _record_usage_and_close_consumer(
                                store, adapter, consumer_id, dispatch_ms=dispatch_ms
                            )
                        annotate_dispatch_result(
                            span,
                            status="ok",
                            consumer_id=consumer_id,
                            usage=getattr(adapter, "last_usage", None),
                            dispatch_ms=dispatch_ms,
                        )
                    else:
                        annotate_dispatch_result(
                            span,
                            status="no_consumer",
                            usage=getattr(adapter, "last_usage", None),
                            dispatch_ms=dispatch_ms,
                            error="no consumer id resolved",
                        )
                except Exception as exc:
                    annotate_dispatch_result(span, status="error", error=str(exc))
                    logger.exception("[invariant_audit] dispatch failed")
            last_audit = _time.monotonic()
            if observe_dispatch(
                breaker, getattr(adapter, "last_error", None), on_stop_signal=stop.set
            ):
                break
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

    run_inbox_roles, run_remsleep = _selected_roles()
    if run_remsleep and not run_inbox_roles:
        logger.info("RemSleep-only mode: memory recall + consolidation, no Judge/Smoother")

    store = EnactmentStore()
    stop = asyncio.Event()
    # One breaker shared across every role + memory loop: a quota/auth failure
    # or repeated model error seen by any worker halts the whole loop.
    breaker = CircuitBreaker()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)

    judge: AutonomicAdapter | None = None
    smoother: AutonomicAdapter | None = None
    invariant_auditor: AutonomicAdapter | None = None
    if run_inbox_roles:
        judge = _build_adapter(provider, "judge")
        smoother = _build_adapter(provider, "smoother")
        # The audit reviews the governed invariants — judgement over the rules.
        # It reuses the Judge bundle but runs only when the loop is idle.
        invariant_auditor = _build_adapter(provider, "judge")

    memory_recall: AutonomicAdapter | None = None
    memory_consolidation: AutonomicAdapter | None = None
    remsleep_interval = _remsleep_interval_seconds()
    signal_poll = _remsleep_signal_poll_seconds()
    if run_remsleep:
        missing = [
            bundle_id
            for bundle_id in ("memory_recall", "memory_consolidation")
            if bundle_id not in BUNDLES
        ]
        if missing:
            raise RuntimeError(
                "RemSleep is enabled but bundle(s) "
                f"{', '.join(missing)!r} are not loaded"
            )
        memory_recall = _build_adapter(provider, "memory_recall")
        memory_consolidation = _build_adapter(provider, "memory_consolidation")

    try:
        tasks = [_watch_sentinel(stop)]
        if run_inbox_roles and judge is not None and smoother is not None:
            # The dispatcher routes closed enactments → judge_inbox and emitted
            # Friction → smoother_inbox while the role loops run. Workers (the
            # adapters' subprocesses) have PRACTICE_DISABLE_DISPATCHER=1 so they
            # don't double-route; routing is owned by this runner's process.
            tasks.append(dispatcher_task(stop, store=store))
            # Reflective loop: on a slow timescale, route closed *autonomic*
            # enactments to the Judge. The reactive dispatcher above routes only
            # somatic completions, so the Judge examining its own/the Smoother's
            # work happens here, paced apart — two timescales, no self-spin.
            tasks.append(
                _run_reflective_judge_loop(
                    store,
                    stop=stop,
                    interval_seconds=_reflective_interval_seconds(),
                )
            )
            tasks.append(
                run_role_loop(
                    judge,
                    RolePolicy(role="judge"),
                    store,
                    stop=stop,
                    worker_id=f"{provider}-judge",
                    breaker=breaker,
                )
            )
            tasks.append(
                run_role_loop(
                    smoother,
                    RolePolicy(role="smoother"),
                    store,
                    stop=stop,
                    worker_id=f"{provider}-smoother",
                    breaker=breaker,
                )
            )
            if invariant_auditor is not None:
                tasks.append(
                    _run_invariant_audit_loop(
                        invariant_auditor,
                        store,
                        stop=stop,
                        poll_seconds=_invariant_audit_poll_seconds(),
                        cooldown_seconds=_invariant_audit_cooldown_seconds(),
                        breaker=breaker,
                    )
                )
        if memory_recall is not None and memory_consolidation is not None:
            tasks.append(
                _run_memory_recall_loop(
                    memory_recall,
                    store,
                    stop=stop,
                    interval_seconds=remsleep_interval,
                    startup_delay_seconds=(
                        _remsleep_startup_delay_seconds() if run_inbox_roles else 0.0
                    ),
                    max_autonomic_backlog=(
                        _remsleep_max_autonomic_backlog() if run_inbox_roles else -1
                    ),
                    backlog_retry_seconds=_remsleep_backlog_retry_seconds(),
                    breaker=breaker,
                )
            )
            tasks.append(
                _run_memory_consolidation_signal_loop(
                    memory_consolidation,
                    store,
                    stop=stop,
                    poll_seconds=signal_poll,
                    breaker=breaker,
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
