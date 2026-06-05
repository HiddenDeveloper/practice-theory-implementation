"""Dispatcher — routes closed enactments and new Friction into the inboxes.

Runs as an asyncio task started by the server at startup. Polls every
PRACTICE_DISPATCHER_POLL_INTERVAL_SECONDS (default 2.0) and calls the trail
store's idempotent routing methods. New rows in the source tables become new
rows in the inbox tables; old rows stay where they were.

A boot cutoff is captured at startup for logging. It is not currently used
as a filter — routing relies on `INSERT OR IGNORE` against the inbox tables,
so historical events from previous process lifetimes are re-routed harmlessly
and a fresh autonomic server can pick up closed somatic enactments left
behind by an earlier run.

The dispatcher is server-side. The autonomic adapters (Anthropic SDK,
Claude CLI, Codex, Scripted) are workers that read the inboxes via the MCP
autonomic surface; they have no awareness of the dispatcher itself.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import os
from datetime import UTC, datetime
from typing import Final

from practice_theory_implementation.trail import EnactmentStore

logger = logging.getLogger(__name__)

POLL_INTERVAL_ENV: Final[str] = "PRACTICE_DISPATCHER_POLL_INTERVAL_SECONDS"
DEFAULT_POLL_INTERVAL_SECONDS: Final[float] = 2.0


def _resolve_poll_interval() -> float:
    raw = os.environ.get(POLL_INTERVAL_ENV, "").strip()
    if not raw:
        return DEFAULT_POLL_INTERVAL_SECONDS
    try:
        return max(0.25, float(raw))
    except ValueError:
        logger.warning(
            "invalid %s=%r, falling back to %s",
            POLL_INTERVAL_ENV,
            raw,
            DEFAULT_POLL_INTERVAL_SECONDS,
        )
        return DEFAULT_POLL_INTERVAL_SECONDS


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


async def dispatcher_task(
    stop_event: asyncio.Event,
    *,
    store: EnactmentStore,
) -> None:
    """Long-running asyncio task; routes new events into inboxes until stop."""
    boot_cutoff = _now_iso()
    poll = _resolve_poll_interval()
    logger.info(
        "autonomic dispatcher started: boot_cutoff=%s poll_every=%.2fs",
        boot_cutoff,
        poll,
    )
    # The boot_cutoff is recorded but not currently used as a filter — the
    # routing methods use INSERT OR IGNORE so re-routing is harmless, and
    # passing None routes events from previous server lifetimes too. Useful
    # when the autonomic server boots and inherits closed somatic enactments.
    _ = boot_cutoff
    from practice_theory_implementation.judge_triage import triage_and_route

    while not stop_event.is_set():
        try:
            # Somatic completions go through deterministic triage: only the
            # ambiguous reach the Judge LLM; provable Friction is emitted here
            # and clean work is recorded as a no-finding (no tokens).
            summary = await asyncio.to_thread(
                triage_and_route, store, mode="somatic", since=None
            )
            s = await asyncio.to_thread(store.route_friction_to_smoother_inbox, None)
            if summary.ambiguous or summary.friction or s:
                logger.info(
                    "dispatcher triaged[somatic]: judge_inbox +%d friction +%d "
                    "clean %d, smoother_inbox +%d",
                    summary.ambiguous,
                    summary.friction,
                    summary.clean,
                    s,
                )
        except Exception:
            logger.exception("dispatcher poll failed; continuing")
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(stop_event.wait(), timeout=poll)
    logger.info("autonomic dispatcher stopped")


def route_now(store: EnactmentStore) -> tuple[int, int]:
    """Synchronous single-shot routing. Useful for tests and the verify.

    Bypasses the asyncio task and the boot-cutoff filter; routes everything
    in the source tables idempotently.

    Exercises the *production* dispatch semantics, not the legacy bulk route:
    closed enactments go through deterministic `triage_and_route` so clean work
    is cleared as a no-finding (no Judge dispatch) and only the ambiguous reach
    the judge_inbox. Both the reactive (somatic) and reflective (autonomic)
    triage passes run — the somatic dispatcher and the autonomic runner each
    drive one in production; the verify drives both in one process (its first
    pass produces somatic completions, its strange-loop pass autonomic ones).
    Friction (deterministic-triage or LLM-emitted) is then routed to the
    Smoother inbox, mirroring the somatic dispatcher's friction route.

    Returns (judge_inbox additions, smoother_inbox additions): judge additions
    are the ambiguous enactments routed across both modes.
    """
    from practice_theory_implementation.judge_triage import triage_and_route

    somatic = triage_and_route(store, mode="somatic", since=None)
    autonomic = triage_and_route(store, mode="autonomic", since=None)
    s = store.route_friction_to_smoother_inbox(since=None)
    return somatic.ambiguous + autonomic.ambiguous, s
