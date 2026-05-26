"""The function registry — binds Material.name to executable code.

Populated by hand at import time. Each binding is visible in one place; no
decorator and no auto-discovery at this stage. Step 1's separation of capture
from execution is preserved: the bundle describes, the registry executes.

The registry is a mutable dict so runtime additions (dynamic materials) are
supported. A runtime-authored material can register its captured surface into
the materials pool (`pools.MATERIALS`) and its callable into FUNCTIONS in a
single import; a future decorator can collapse those two registrations into one
declaration when authoring ergonomics warrants it.
"""

from __future__ import annotations

from collections.abc import Callable

from practice_theory_implementation.materials import (
    about_user_mock,
    garmin_mock,
    judge,
    practice_management,
    reflection_mock,
    smoother,
)
from practice_theory_implementation.types import Substrate

FUNCTIONS: dict[str, Callable[..., object]] = {
    # Engagement-layer
    "consult_about_user": about_user_mock.consult_about_user,
    # Activities Management
    "garmin_list_activities": garmin_mock.garmin_list_activities,
    "garmin_get_activity": garmin_mock.garmin_get_activity,
    "garmin_get_daily_summary": garmin_mock.garmin_get_daily_summary,
    "garmin_get_user_stats": garmin_mock.garmin_get_user_stats,
    # Reflection
    "store_reflection": reflection_mock.store_reflection,
    # Practice Management — meta-materials
    "pm_read_pool": practice_management.pm_read_pool,
    "pm_create_element": practice_management.pm_create_element,
    "pm_amend_element": practice_management.pm_amend_element,
    "pm_create_affordance": practice_management.pm_create_affordance,
    "pm_amend_affordance": practice_management.pm_amend_affordance,
    "pm_create_material": practice_management.pm_create_material,
    "pm_amend_material": practice_management.pm_amend_material,
    "pm_create_bundle": practice_management.pm_create_bundle,
    "pm_amend_bundle": practice_management.pm_amend_bundle,
    # Judge — primitives
    "judge_list_recent_enactments": judge.judge_list_recent_enactments,
    "judge_read_enactment_steps": judge.judge_read_enactment_steps,
    "judge_read_bundle": judge.judge_read_bundle,
    "judge_emit_friction": judge.judge_emit_friction,
    # Smoother — two smoother-specific materials; the other six affordances
    # in the Smoother bundle reuse PM materials registered above.
    "smoother_read_pending_friction": smoother.smoother_read_pending_friction,
    "smoother_mark_addressed": smoother.smoother_mark_addressed,
}


def register(name: str, fn: Callable[..., object]) -> None:
    """Bind a callable to a material name. Used for dynamic registration."""
    FUNCTIONS[name] = fn


def resolve(name: str) -> Callable[..., object]:
    """Look up the callable bound to a material name."""
    try:
        return FUNCTIONS[name]
    except KeyError as exc:
        raise KeyError(f"no function registered for material {name!r}") from exc


def validate_against(substrate: Substrate) -> None:
    """Check every material in the substrate has a binding in the registry.

    Materials in the registry that are not in the substrate are allowed —
    they may be authored functions waiting for a captured-surface entry.
    """
    missing = sorted(name for name in substrate.materials if name not in FUNCTIONS)
    if missing:
        raise ValueError(f"materials in substrate without registry bindings: {missing}")
