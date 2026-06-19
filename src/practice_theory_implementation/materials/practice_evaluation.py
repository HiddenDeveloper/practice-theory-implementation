"""The practice-evaluation engine — measure whether a practice delivers its objective.

This is the single, generic, hand-written piece of evaluation *code*. It knows
nothing about funds, mail, or calendars. Given a practice name, it reads that
practice's own declarative evaluation layer (its `EvaluationSpec`) and runs each
declared signal over the practice's *real* trail — the enactments it actually
produced in normal operation. The practice-specific knowledge lives entirely in
the spec's parameters; the engine only interprets generic signal *kinds*.

Phase 1 is read-only and emits no Friction. It returns structured findings — a
measurement handed to the Judge, who decides whether a concern is real quality
friction or acceptable variation. A practice with no evaluation layer comes back
flagged `spec_present: false` (the deterministic newness signal a later phase
routes to the Smoother to author one).

Module-level state is wired by the server at startup via `configure(...)`,
mirroring the Judge primitives: the engine needs the trail (to read enactments)
and the substrate + catalog (to read the evaluation layer).
"""

from __future__ import annotations

from typing import Any

from practice_theory_implementation.trail import EnactmentRow, EnactmentStore, StepRow
from practice_theory_implementation.types import Bundle, EvaluationSpec, Substrate

# wired by the server at startup
_trail: EnactmentStore | None = None
_substrate: Substrate | None = None
_bundle_catalog: dict[str, Bundle] | None = None


def configure(
    *,
    trail: EnactmentStore,
    substrate: Substrate,
    bundle_catalog: dict[str, Bundle],
) -> None:
    """Wire the evaluation engine to the live trail, substrate, and catalog."""
    global _trail, _substrate, _bundle_catalog
    _trail = trail
    _substrate = substrate
    _bundle_catalog = bundle_catalog


def _need() -> tuple[EnactmentStore, Substrate, dict[str, Bundle]]:
    if _trail is None or _substrate is None or _bundle_catalog is None:
        raise RuntimeError(
            "practice_evaluation not configured; call configure() first"
        )
    return _trail, _substrate, _bundle_catalog


def _specs_for(
    substrate: Substrate, catalog: dict[str, Bundle], name: str
) -> list[EvaluationSpec]:
    """Resolve a practice's evaluation specs: via the bundle's evaluation_ids,
    falling back to any spec that names this practice_id directly."""
    spec_ids: list[str] = []
    bundle = catalog.get(name)
    if bundle is not None:
        spec_ids = list(bundle.evaluation_ids)
    specs = [substrate.evaluations[sid] for sid in spec_ids if sid in substrate.evaluations]
    if not specs:
        specs = [s for s in substrate.evaluations.values() if s.practice_id == name]
    return specs


def _gather_enactments(
    trail: EnactmentStore, practice_id: str, window: int
) -> list[tuple[EnactmentRow, list[StepRow]]]:
    """The window of recent closed, non-empty enactments, newest first.

    Over-fetch a little so in-flight or zero-step (lifecycle-churn) enactments
    that we skip do not shrink the effective window below `window`.
    """
    out: list[tuple[EnactmentRow, list[StepRow]]] = []
    for row in trail.recent_enactments(limit=window * 2, practice_id=practice_id):
        if row.closed_at is None:
            continue
        steps = trail.steps_for(row.id)
        if not steps:
            continue
        out.append((row, steps))
        if len(out) >= window:
            break
    return out


# --- signal computations -------------------------------------------------
# Each takes the signal dict + the newest-first window and returns a finding.
# Pure, deterministic, token-free.


def _materials_of(steps: list[StepRow]) -> set[str]:
    return {s.material_name for s in steps}


def _signal_affordance_coverage(
    sig: dict[str, Any], window: list[tuple[EnactmentRow, list[StepRow]]]
) -> dict[str, Any]:
    required = set(sig.get("required_materials") or [])
    missing_in: list[dict[str, Any]] = []
    for row, steps in window:
        miss = required - _materials_of(steps)
        if miss:
            missing_in.append({"enactment_id": row.id, "missing": sorted(miss)})
    return {
        "status": "concern" if missing_in else "pass",
        "evidence": {
            "required_materials": sorted(required),
            "enactments_missing_required": missing_in,
            "enactments_evaluated": len(window),
        },
    }


def _signal_outcome_presence(
    sig: dict[str, Any], window: list[tuple[EnactmentRow, list[StepRow]]]
) -> dict[str, Any]:
    outcome = set(sig.get("outcome_materials") or [])
    threshold = int(sig.get("max_consecutive_without", 6))
    run = 0
    for _, steps in window:  # newest first
        if outcome & _materials_of(steps):
            break
        run += 1
    return {
        "status": "concern" if run >= threshold else "pass",
        "evidence": {
            "consecutive_passes_without_outcome": run,
            "threshold": threshold,
            "outcome_materials": sorted(outcome),
            "enactments_evaluated": len(window),
        },
    }


def _signal_shape_repetition(
    sig: dict[str, Any], window: list[tuple[EnactmentRow, list[StepRow]]]
) -> dict[str, Any]:
    threshold = int(sig.get("max_identical", 4))
    signatures = [tuple(s.material_name for s in steps) for _, steps in window]
    run = 0
    if signatures:
        first = signatures[0]
        for sg in signatures:
            if sg != first:
                break
            run += 1
    return {
        "status": "concern" if run >= threshold else "pass",
        "evidence": {
            "identical_leading_run": run,
            "threshold": threshold,
            "enactments_evaluated": len(window),
        },
    }


def _signal_recurring_summary_marker(
    sig: dict[str, Any], window: list[tuple[EnactmentRow, list[StepRow]]]
) -> dict[str, Any]:
    markers = [str(m).lower() for m in (sig.get("markers") or [])]
    threshold = int(sig.get("max_consecutive", 5))
    run = 0
    for _, steps in window:  # newest first
        blob = " ".join(s.result_summary.lower() for s in steps)
        if any(m in blob for m in markers):
            run += 1
        else:
            break
    return {
        "status": "concern" if run >= threshold else "pass",
        "evidence": {
            "consecutive_passes_with_marker": run,
            "threshold": threshold,
            "markers": markers,
            "enactments_evaluated": len(window),
        },
    }


_SIGNAL_KINDS = {
    "affordance_coverage": _signal_affordance_coverage,
    "outcome_presence": _signal_outcome_presence,
    "shape_repetition": _signal_shape_repetition,
    "recurring_summary_marker": _signal_recurring_summary_marker,
}

# Required non-empty list parameters per signal kind. The single source of truth
# for what makes a signal well-formed — used by the authoring gate so a
# malformed spec cannot be created, and implicitly by the engine (a signal
# missing its list simply finds nothing). Kinds absent here need no list param.
_SIGNAL_REQUIRED_LISTS = {
    "affordance_coverage": "required_materials",
    "outcome_presence": "outcome_materials",
    "recurring_summary_marker": "markers",
}


def validate_signals(signals: object) -> list[str]:
    """Deterministic well-formedness gate for an eval-spec's signals.

    Returns a list of error strings (empty == valid). A signal must be a mapping
    with a non-empty `id` and a known `kind`, and must carry the non-empty list
    parameter its kind requires. This is the mechanical gate the authoring
    materials enforce so a malformed evaluator cannot enter the substrate.
    """
    errors: list[str] = []
    if not isinstance(signals, list):
        return ["signals must be a list"]
    for i, sig in enumerate(signals):
        where = f"signal[{i}]"
        if not isinstance(sig, dict):
            errors.append(f"{where}: must be a mapping")
            continue
        if not sig.get("id"):
            errors.append(f"{where}: missing id")
        kind = sig.get("kind")
        if kind not in _SIGNAL_KINDS:
            errors.append(
                f"{where}: unknown kind {kind!r}; must be one of "
                f"{sorted(_SIGNAL_KINDS)}"
            )
            continue
        required = _SIGNAL_REQUIRED_LISTS.get(str(kind))
        if required is not None:
            value = sig.get(required)
            if not isinstance(value, list) or not value:
                errors.append(
                    f"{where} ({kind}): requires a non-empty list {required!r}"
                )
    return errors


def _run_signal(
    sig: dict[str, Any], window: list[tuple[EnactmentRow, list[StepRow]]]
) -> dict[str, Any]:
    kind = str(sig.get("kind", ""))
    fn = _SIGNAL_KINDS.get(kind)
    base = {
        "signal_id": sig.get("id"),
        "kind": kind,
        "detail": sig.get("detail"),
    }
    if fn is None:
        return {
            **base,
            "status": "skipped",
            "evidence": {"reason": f"unknown signal kind {kind!r}"},
        }
    return {**base, **fn(sig, window)}


def _evaluate_spec(
    trail: EnactmentStore, spec: EvaluationSpec, window_override: int | None
) -> dict[str, Any]:
    window_n = window_override if window_override and window_override > 0 else spec.window
    enactments = _gather_enactments(trail, spec.practice_id, window_n)
    findings = [_run_signal(dict(sig), enactments) for sig in spec.signals]
    return {
        "spec_id": spec.id,
        "spec_present": True,
        "objective_ref": spec.objective_ref,
        "derived_from": spec.derived_from,
        "window": window_n,
        "enactments_evaluated": len(enactments),
        "evaluated_enactment_ids": [row.id for row, _ in enactments],
        "findings": findings,
        "concern_count": sum(1 for f in findings if f.get("status") == "concern"),
    }


def evaluate_with(
    *,
    trail: EnactmentStore,
    substrate: Substrate,
    bundle_catalog: dict[str, Bundle],
    name: str,
    window: int | None = None,
) -> dict[str, Any]:
    """Pure core: evaluate a practice against explicit dependencies.

    The public material binds module-level state and calls this; the routing
    layer (which runs in the autonomic-runner process, not the MCP server) calls
    it directly with its own trail + loaded substrate, so it needs no global
    configuration.
    """
    specs = _specs_for(substrate, bundle_catalog, name)
    if not specs:
        return {
            "practice_id": name,
            "spec_present": False,
            "newness_signal": True,
            "detail": (
                "no evaluation layer found for this practice; it is not yet "
                "measurable. A spec should be authored before quality friction "
                "can be detected."
            ),
        }
    results = [_evaluate_spec(trail, spec, window) for spec in specs]
    if len(results) == 1:
        return {"practice_id": name, **results[0]}
    return {
        "practice_id": name,
        "spec_present": True,
        "results": results,
        "concern_count": sum(r["concern_count"] for r in results),
    }


def evaluate_quality_for_practice(
    name: str, window: int | None = None
) -> dict[str, Any]:
    """Run a practice's evaluation layer over its real trail and return findings.

    Read-only. Emits no Friction. A practice with no evaluation layer returns
    `spec_present: false` with `newness_signal: true` — the deterministic signal
    that this practice is not yet measurable and needs a spec authored.
    """
    trail, substrate, catalog = _need()
    return evaluate_with(
        trail=trail,
        substrate=substrate,
        bundle_catalog=catalog,
        name=name,
        window=window,
    )
