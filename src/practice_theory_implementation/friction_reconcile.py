"""Deterministic reconciliation of the Friction lifecycle.

A Smoother dispatch consumes its inbox row when the dispatch *runs*, not when
the Friction is addressed. A pass that reads the Friction and then closes without
amending, marking it addressed, or recording a decline therefore strands it:
consumed (so `next_smoother_work` never re-claims it) yet unaddressed (so it is
never resolved), with the `INSERT OR IGNORE` Friction route blocking a fresh
inbox row. Nothing reconciles the two facts, so a single incomplete pass strands
the Friction permanently.

This closes that gap deterministically (no LLM): a consumed-but-unaddressed
Friction whose consuming enactment has *closed* is re-routed for another Smoother
pass, up to `RECONCILE_MAX_ATTEMPTS`; past the cap it is tombstoned with a
recorded basis. The lifecycle then always terminates in addressed, declined, or
tombstoned — never limbo. Detecting "consumed, consumer closed, still
unaddressed" needs no judgement, so it belongs in code, not the loop.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from practice_theory_implementation.trail import EnactmentStore

logger = logging.getLogger(__name__)

# Re-route attempts before a stranded Friction is tombstoned. Bounded so a
# genuinely un-actionable Friction (e.g. a tooling quirk the Smoother cannot
# amend) cannot loop forever.
RECONCILE_MAX_ATTEMPTS = 3
RECONCILE_OBSERVER = "system:reconcile"


@dataclass(slots=True)
class ReconcileSummary:
    examined: int = 0
    rerouted: int = 0
    tombstoned: int = 0

    @property
    def notification(self) -> str:
        return (
            f"friction reconcile: examined={self.examined} "
            f"rerouted={self.rerouted} tombstoned={self.tombstoned}"
        )


def reconcile_smoother_frictions(
    store: EnactmentStore,
    *,
    max_attempts: int = RECONCILE_MAX_ATTEMPTS,
    limit: int = 200,
) -> ReconcileSummary:
    """Re-route consumed-but-unaddressed Frictions; tombstone past the cap.

    Re-route bumps the attempt counter and clears the consume/claim fields so the
    Smoother re-claims the work. At/over the cap, the Friction is tombstoned —
    marked addressed by a `system:reconcile` observer whose id records the basis
    (`unresolved_after_N_attempts`) — so the pending queue stays honest.
    """
    candidates = store.smoother_frictions_to_reconcile(limit=limit)
    summary = ReconcileSummary(examined=len(candidates))
    for friction_id, attempts in candidates:
        if attempts >= max_attempts:
            basis = f"{RECONCILE_OBSERVER}:unresolved_after_{attempts}_attempts"
            store.mark_friction_addressed(friction_id, basis)
            summary.tombstoned += 1
        else:
            store.reroute_smoother_friction(friction_id)
            summary.rerouted += 1
    if summary.examined:
        logger.info("%s", summary.notification)
    return summary
