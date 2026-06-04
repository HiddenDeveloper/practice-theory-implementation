"""Smoother materials — read Friction and mark it addressed.

The actual substrate amendment is done by Practice Management's meta-materials
(`pm_amend_bundle`, `pm_amend_element`, etc.), which the Smoother's bundle
reaches for as affordances. This module only adds the two pieces specific to
the Smoother: reading pending Friction, and marking Friction addressed.

Wired by the server at startup via `configure(...)`.
"""

from __future__ import annotations

import json
from typing import Any

from practice_theory_implementation.trail import EnactmentStore

_trail: EnactmentStore | None = None
_active_enactment_id_getter: Any = None  # callable[[], str | None]


def configure(
    *,
    trail: EnactmentStore,
    active_enactment_id_getter: Any,
) -> None:
    """Wire the Smoother to the trail and current-enactment getter."""
    global _trail, _active_enactment_id_getter
    _trail = trail
    _active_enactment_id_getter = active_enactment_id_getter


def _need() -> tuple[EnactmentStore, Any]:
    if _trail is None or _active_enactment_id_getter is None:
        raise RuntimeError("smoother materials not configured; call configure() first")
    return _trail, _active_enactment_id_getter


def smoother_read_pending_friction(
    limit: int = 10, friction_id: int | None = None
) -> list[dict[str, Any]]:
    """Return pending Friction, optionally narrowed to one id."""
    trail, _ = _need()
    pending = trail.pending_friction(limit=limit, friction_id=friction_id)
    out: list[dict[str, Any]] = []
    for f in pending:
        observation_data = (
            json.loads(f.observation_data_json)
            if f.observation_data_json
            else None
        )
        out.append(
            {
                "id": f.id,
                "target_enactment_id": f.target_enactment_id,
                "kind": f.kind,
                "content": f.content,
                "observation_data": observation_data,
                "observed_at": f.observed_at,
            }
        )
    return out


def smoother_read_friction_kinds(limit: int = 200) -> list[dict[str, Any]]:
    """Return the current Friction-kind vocabulary with counts (most common
    first), so a rename can condense toward an existing kind."""
    trail, _ = _need()
    return trail.friction_kinds(limit=limit)


def smoother_rename_friction(
    friction_id: int, new_kind: str, content: str | None = None
) -> dict[str, Any]:
    """Condense a Friction's name: rename the Judge's provisional kind toward the
    canonical vocabulary (optionally re-wording its content). Recorded as a step,
    so the old→new is preserved on the trail."""
    trail, get_active = _need()
    active_id = get_active()
    if active_id is None:
        return {"error": "no active enactment; Smoother must be enacted to rename"}
    old_kind = trail.rename_friction(friction_id, new_kind, content=content)
    if old_kind is None:
        return {"error": f"friction {friction_id!r} not found"}
    return {"renamed": friction_id, "from": old_kind, "to": new_kind}


def smoother_mark_addressed(
    friction_id: int, rationale: str | None = None
) -> dict[str, Any]:
    """Mark a Friction as addressed by the current Smoother enactment."""
    trail, get_active = _need()
    active_id = get_active()
    if active_id is None:
        return {"error": "no active enactment; Smoother must be enacted to mark addressed"}
    ok = trail.mark_friction_addressed(friction_id, active_id)
    if not ok:
        return {"error": f"friction {friction_id!r} not found or already addressed"}
    result: dict[str, Any] = {"addressed": friction_id, "by_enactment_id": active_id}
    if rationale:
        result["rationale"] = rationale
    return result
