"""Judge primitives — read the trail, read bundles, emit Friction.

The Judge's intelligence does not live here. These are primitives — small
operations the Judge LLM composes during an enactment to read what happened
and name what is worth attending to. The heuristics live in the Judge
bundle's understanding and rules (the prose the LLM reads when it enacts).

Module-level state is wired by the server at startup via `configure(...)`.
The Judge needs the trail (read enactments, emit Friction), the substrate
(read bundles), the catalog (find a bundle by id), and the current
observing enactment id (so Friction records which Judge enactment emitted
it).
"""

from __future__ import annotations

from typing import Any

from practice_theory_implementation.trail import EnactmentStore
from practice_theory_implementation.types import Bundle, Substrate

# wired by the server at startup
_trail: EnactmentStore | None = None
_substrate: Substrate | None = None
_bundle_catalog: dict[str, Bundle] | None = None
_observing_enactment_id_getter: Any = None  # callable[[], str | None]


def configure(
    *,
    trail: EnactmentStore,
    substrate: Substrate,
    bundle_catalog: dict[str, Bundle],
    observing_enactment_id_getter: Any,
) -> None:
    """Wire the Judge primitives to the live trail, substrate, catalog,
    and a getter for the current Judge enactment id."""
    global _trail, _substrate, _bundle_catalog, _observing_enactment_id_getter
    _trail = trail
    _substrate = substrate
    _bundle_catalog = bundle_catalog
    _observing_enactment_id_getter = observing_enactment_id_getter


def _need() -> tuple[EnactmentStore, Substrate, dict[str, Bundle], Any]:
    if (
        _trail is None
        or _substrate is None
        or _bundle_catalog is None
        or _observing_enactment_id_getter is None
    ):
        raise RuntimeError("judge materials not configured; call configure() first")
    return _trail, _substrate, _bundle_catalog, _observing_enactment_id_getter


def judge_list_recent_enactments(
    limit: int = 10,
    bundle_id: str | None = None,
) -> list[dict[str, Any]]:
    """List recent enactments, most-recent first. Optionally filter by bundle id."""
    trail, _, _, _ = _need()
    rows = trail.recent_enactments(limit=limit, practice_id=bundle_id)
    return [
        {
            "id": r.id,
            "bundle_id": r.practice_id,
            "parent_enactment_id": r.parent_enactment_id,
            "opened_at": r.opened_at,
            "closed_at": r.closed_at,
        }
        for r in rows
    ]


def judge_read_enactment_steps(enactment_id: str) -> list[dict[str, Any]]:
    """Read every step recorded against the given enactment, in order."""
    trail, _, _, _ = _need()
    steps = trail.steps_for(enactment_id)
    return [
        {
            "id": s.id,
            "affordance_id": s.affordance_id,
            "material_name": s.material_name,
            "arguments_json": s.arguments_json,
            "result_summary": s.result_summary,
            "started_at": s.started_at,
            "completed_at": s.completed_at,
            "duration_ms": s.duration_ms,
        }
        for s in steps
    ]


def judge_read_bundle(bundle_id: str) -> dict[str, Any]:
    """Return the bundle's structure as data: id, name, description, mode,
    and the ids it selects (teleo_affective, understanding, rules, affordances)."""
    _, _, catalog, _ = _need()
    if bundle_id not in catalog:
        return {"error": f"bundle {bundle_id!r} not in catalog"}
    b = catalog[bundle_id]
    return {
        "id": b.id,
        "name": b.name,
        "description": b.description,
        "mode": b.mode,
        "teleo_affective_ids": list(b.teleo_affective_ids),
        "understanding_ids": list(b.understanding_ids),
        "rules_ids": list(b.rules_ids),
        "affordance_ids": list(b.affordance_ids),
    }


def judge_emit_friction(
    target_enactment_id: str,
    kind: str,
    content: str,
    observation_data: object | None = None,
) -> dict[str, Any]:
    """Record a Friction observation. `kind` is a short tag; `content` is a
    freeform description of what was observed; `observation_data` is
    optional structured evidence (the observation itself, not a remedy)."""
    trail, _, _, get_observer = _need()
    observer_id = get_observer()
    if observer_id is None:
        return {
            "error": "no active observing enactment; Judge must be enacted to emit Friction"
        }
    friction_id = trail.record_friction(
        observing_enactment_id=observer_id,
        target_enactment_id=target_enactment_id,
        kind=kind,
        content=content,
        observation_data=observation_data,
    )
    return {
        "emitted": {
            "friction_id": friction_id,
            "kind": kind,
            "target_enactment_id": target_enactment_id,
            "observing_enactment_id": observer_id,
        }
    }
