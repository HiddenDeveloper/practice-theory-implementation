"""Dispatcher — routes closed enactments and new Friction into the inboxes.

Runs as an asyncio task started by the server at startup. Polls every
PRACTICE_DISPATCHER_POLL_INTERVAL_SECONDS (default 2.0) and calls the trail
store's idempotent routing methods. New rows in the source tables become new
rows in the inbox tables; old rows stay where they were.

A boot cutoff is captured at startup so historical events from previous
process lifetimes are not re-routed.

The dispatcher is server-side. The autonomic adapters (Anthropic, Codex,
Scripted) are workers that read the inboxes via the MCP autonomic surface;
they have no awareness of the dispatcher itself.
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
    while not stop_event.is_set():
        try:
            j = await asyncio.to_thread(
                store.route_closed_enactments_to_judge_inbox, None
            )
            s = await asyncio.to_thread(
                store.route_friction_to_smoother_inbox, None
            )
            if j or s:
                logger.info(
                    "dispatcher routed: judge_inbox +%d, smoother_inbox +%d", j, s
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
    """
    j = store.route_closed_enactments_to_judge_inbox(since=None)
    s = store.route_friction_to_smoother_inbox(since=None)
    return j, s
