"""Deterministic triage between a closed enactment and the LLM Judge.

The Judge LLM is expensive. Routing *every* closed enactment to it — which is
what the reflective loop did — spends tokens examining clean, successful work
that a cheap deterministic check could clear, and (with the reflective loop
feeding the Judge's own enactments back) manufactures unbounded inbox growth.

This module gates that dispatch. Each closed enactment is run through a
registry of deterministic detectors (pure trail reads, no tokens) that classify
it three ways:

- CLEAN     — no deterministic friction signal. Record a no-finding in the
              triage_log and stop. The LLM is never involved.
- FRICTION  — a Friction is *provable* without judgement (e.g. the bundle the
              enactment names no longer resolves). Emit it deterministically; it
              flows to the Smoother inbox via the normal Friction route. No LLM.
- AMBIGUOUS — a signal needs intelligent judgement to name. Only here is a
              judge_inbox row created and the Judge LLM dispatched.

Resolution precedence is FRICTION > AMBIGUOUS > CLEAN. New harnesses or
heuristics extend the system by registering a detector — the routing,
idempotency (triage_log), and OTEL accounting are unchanged.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum

from practice_theory_implementation.harness_errors import DISPATCH_FAILED_MATERIAL
from practice_theory_implementation.trail import EnactmentRow, EnactmentStore, StepRow

logger = logging.getLogger(__name__)

TRIAGE_OBSERVER_ID = "system:triage"


class Outcome(StrEnum):
    CLEAN = "clean"
    FRICTION = "friction"
    AMBIGUOUS = "ambiguous"


@dataclass(frozen=True, slots=True)
class EnactmentView:
    """Everything a detector needs about one enactment — gathered once."""

    enactment: EnactmentRow
    steps: list[StepRow]
    bundle_resolves: bool

    @property
    def bundle_id(self) -> str:
        return self.enactment.practice_id


@dataclass(frozen=True, slots=True)
class TriageResult:
    outcome: Outcome
    kind: str | None = None
    content: str | None = None
    observation_data: dict | None = None
    reason: str | None = None


Detector = Callable[[EnactmentView], "TriageResult | None"]


# --- detectors -------------------------------------------------------------
# Pure, deterministic, token-free. Each returns a TriageResult or None (abstain).


def _detect_unresolved_bundle(view: EnactmentView) -> TriageResult | None:
    """Bundle the enactment names no longer resolves → provable missing_bundle.

    This is exactly the case the Smoother LLM was burning dispatches to no-op on
    (Friction 287, `user_focused_engagement`). Now emitted deterministically.
    """
    if view.bundle_resolves:
        return None
    return TriageResult(
        outcome=Outcome.FRICTION,
        kind="missing_bundle",
        content=(
            f"The enactment is tagged to bundle `{view.bundle_id}`, which does "
            f"not resolve in the current catalog. Determined deterministically "
            f"by triage (bundle id not in the loaded substrate)."
        ),
        observation_data={
            "target_enactment_id": view.enactment.id,
            "target_bundle_id": view.bundle_id,
            "target_closed_at": view.enactment.closed_at,
            "basis": "bundle_id not in current catalog",
            "detector": "unresolved_bundle",
        },
    )


def _step_has_error(step: StepRow) -> bool:
    # invoke_affordance returns `{"error": "..."}` on failure; the trail stores
    # a summarised form of that result. Match the json error key, not a bare
    # "error" substring, to avoid flagging steps that merely mention the word.
    summary = step.result_summary.lower()
    return '"error"' in summary or "'error'" in summary


def _is_dispatch_failure(view: EnactmentView) -> bool:
    return any(s.material_name == DISPATCH_FAILED_MATERIAL for s in view.steps)


def _detect_recorded_step_error(view: EnactmentView) -> TriageResult | None:
    """A step recorded an error result → needs the Judge to name the friction."""
    # A failed-dispatch enactment is environmental, cleared deterministically by
    # _detect_dispatch_failure; do not raise its partial error steps to the Judge.
    if _is_dispatch_failure(view):
        return None
    errored = [s for s in view.steps if _step_has_error(s)]
    if not errored:
        return None
    return TriageResult(
        outcome=Outcome.AMBIGUOUS,
        kind="recorded_step_error",
        reason=(
            f"{len(errored)} step(s) recorded an error result "
            f"(e.g. {errored[0].affordance_id}/{errored[0].material_name})"
        ),
    )


def _detect_dispatch_failure(view: EnactmentView) -> TriageResult | None:
    """A dispatch that died after opening its enactment is closed with a system
    failure marker. Clear it deterministically — the failure is environmental
    (a dead subprocess: crash or quota), already recorded on the trail and in
    OTEL, with no practitioner conduct to judge. Without this, a quota outage
    that fails many dispatches would manufacture a burst of Judge work."""
    if not _is_dispatch_failure(view):
        return None
    return TriageResult(
        outcome=Outcome.CLEAN,
        reason="autonomic dispatch failed (environmental); recorded deterministically",
    )


def _detect_zero_steps(view: EnactmentView) -> TriageResult | None:
    """Closed enactment with no steps → lifecycle churn, not LLM-worthy."""
    if view.steps:
        return None
    return TriageResult(
        outcome=Outcome.CLEAN, reason="zero-step enactment (lifecycle churn)"
    )


def _detect_clean_success(view: EnactmentView) -> TriageResult | None:
    """Fallback: a resolved bundle with steps and no error signal → no-finding.

    Embodies "if no friction can be identified deterministically, the LLM is not
    involved" — absence of any detector signal is itself a deterministic
    no-finding, not a reason to spend a Judge dispatch.
    """
    return TriageResult(outcome=Outcome.CLEAN, reason="no deterministic friction signal")


# Order matters only as the scan order; resolution precedence is applied in
# `triage_enactment` (FRICTION > AMBIGUOUS > CLEAN). clean_success is the
# catch-all and must stay last.
_DETECTORS: list[Detector] = [
    _detect_unresolved_bundle,
    _detect_dispatch_failure,
    _detect_recorded_step_error,
    _detect_zero_steps,
    _detect_clean_success,
]


def register_detector(detector: Detector) -> None:
    """Add a deterministic detector (insert before the clean_success catch-all)."""
    _DETECTORS.insert(max(0, len(_DETECTORS) - 1), detector)


def _bundle_resolves(bundle_id: str) -> bool:
    from practice_theory_implementation.substrate_loader import loaded

    load = loaded()
    if bundle_id in load.bundles:
        return True
    eng = load.engagement_bundle
    return eng is not None and getattr(eng, "id", None) == bundle_id


def _view(store: EnactmentStore, enactment: EnactmentRow) -> EnactmentView:
    return EnactmentView(
        enactment=enactment,
        steps=store.steps_for(enactment.id),
        bundle_resolves=_bundle_resolves(enactment.practice_id),
    )


def triage_enactment(store: EnactmentStore, enactment: EnactmentRow) -> TriageResult:
    """Run the detector registry over one enactment and resolve to one outcome.

    Precedence FRICTION > AMBIGUOUS > CLEAN: a provable friction wins; else a
    signal needing judgement; else a no-finding.
    """
    view = _view(store, enactment)
    results = [r for det in _DETECTORS if (r := det(view)) is not None]
    for wanted in (Outcome.FRICTION, Outcome.AMBIGUOUS, Outcome.CLEAN):
        for result in results:
            if result.outcome is wanted:
                return result
    # No detector decided (the clean_success catch-all guarantees this never
    # happens, but default to judgement rather than silently dropping).
    return TriageResult(outcome=Outcome.AMBIGUOUS, reason="undetermined; defer to Judge")


@dataclass(slots=True)
class TriageSummary:
    mode: str
    clean: int = 0
    friction: int = 0
    ambiguous: int = 0
    failed: int = 0
    examined: int = field(default=0)

    @property
    def notification(self) -> str:
        return (
            f"triage[{self.mode}]: examined={self.examined} "
            f"clean={self.clean} friction={self.friction} "
            f"ambiguous={self.ambiguous} failed={self.failed}"
        )


def triage_and_route(
    store: EnactmentStore, *, mode: str, since: str | None = None, limit: int = 200
) -> TriageSummary:
    """Triage closed `mode` enactments and route only the ambiguous to the LLM.

    Replaces the bulk `route_*_to_judge_inbox` for the live loops. CLEAN →
    no-finding (triage_log only). FRICTION → deterministic Friction (→ Smoother
    inbox via the normal Friction route). AMBIGUOUS → judge_inbox (Judge LLM).
    A detector/triage failure leaves the enactment un-decided for the next pass
    rather than committing a half-finished route.
    """
    from practice_theory_implementation.invariant_engine import run_invariants

    candidates = store.closed_enactments_pending_triage(
        mode=mode, since=since, limit=limit
    )
    summary = TriageSummary(mode=mode, examined=len(candidates))
    for enactment in candidates:
        # Deterministic governed invariants run first: any determinable contract
        # violation is raised AND auto-resolved here, no LLM. Independent of the
        # 3-way classification below.
        try:
            run_invariants(store, enactment)
        except Exception:
            logger.exception("invariant run failed for %s; continuing", enactment.id)
        try:
            result = triage_enactment(store, enactment)
        except Exception:
            logger.exception(
                "triage failed for %s; leaving un-decided for next pass",
                enactment.id,
            )
            summary.failed += 1
            continue
        try:
            _apply(store, enactment, result)
        except Exception:
            logger.exception("triage routing failed for %s; will retry", enactment.id)
            summary.failed += 1
            continue
        if result.outcome is Outcome.FRICTION:
            summary.friction += 1
        elif result.outcome is Outcome.AMBIGUOUS:
            summary.ambiguous += 1
        else:
            summary.clean += 1
    if summary.examined:
        logger.info("%s", summary.notification)
    return summary


def _apply(
    store: EnactmentStore, enactment: EnactmentRow, result: TriageResult
) -> None:
    """Commit a triage decision. Action first, then mark decided (at-least-once
    on the action — a crash between the two re-triages rather than silently
    losing a Friction)."""
    if result.outcome is Outcome.FRICTION:
        store.record_friction(
            observing_enactment_id=TRIAGE_OBSERVER_ID,
            target_enactment_id=enactment.id,
            kind=result.kind or "friction",
            content=result.content or "deterministic triage friction",
            observation_data=result.observation_data,
        )
        store.record_triage(enactment.id, outcome="friction", kind=result.kind)
    elif result.outcome is Outcome.AMBIGUOUS:
        store.enqueue_judge_inbox(
            enactment_id=enactment.id,
            bundle_id=enactment.practice_id,
            closed_at=enactment.closed_at or "",
        )
        store.record_triage(enactment.id, outcome="ambiguous", kind=result.kind)
    else:
        store.record_triage(
            enactment.id, outcome="clean", kind=result.reason or "no_friction"
        )
