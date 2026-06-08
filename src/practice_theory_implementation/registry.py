"""The function registry — binds Material.name to executable code.

Populated by hand at import time. Each binding is visible in one place; no
decorator and no auto-discovery at this stage. Step 1's separation of capture
from execution is preserved: the bundle describes, the registry executes.

The registry is a mutable dict so runtime additions are supported. A
runtime-authored material can register its captured surface into the materials
pool and register a dynamic callable immediately; persisted dynamic callables
are rebuilt into FUNCTIONS when the server starts.
"""

from __future__ import annotations

import ast
from collections.abc import Callable, Iterable, Mapping
from types import CodeType
from typing import Any

from practice_theory_implementation.materials import (
    calendar_mock,
    engagement_context,
    episodic_memory,
    garmin,
    google_calendar,
    google_mail,
    judge,
    operational_observability,
    practice_management,
    reflection_mock,
    remsleep,
    smoother,
    status_dashboard,
)
from practice_theory_implementation.types import Substrate

_ALLOWED_EXPRESSION_NODES = (
    ast.Expression,
    ast.Constant,
    ast.Name,
    ast.Load,
    ast.Dict,
    ast.List,
    ast.Tuple,
    ast.Set,
    ast.Subscript,
    ast.Slice,
    ast.BinOp,
    ast.UnaryOp,
    ast.BoolOp,
    ast.Compare,
    ast.IfExp,
    ast.JoinedStr,
    ast.FormattedValue,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.FloorDiv,
    ast.Mod,
    ast.USub,
    ast.UAdd,
    ast.Not,
    ast.And,
    ast.Or,
    ast.Eq,
    ast.NotEq,
    ast.Lt,
    ast.LtE,
    ast.Gt,
    ast.GtE,
    ast.In,
    ast.NotIn,
    ast.Is,
    ast.IsNot,
)

FUNCTIONS: dict[str, Callable[..., object]] = {
    # Engagement-layer
    "consult_canonical_profile": engagement_context.consult_canonical_profile,
    "consult_canonical_self": engagement_context.consult_canonical_self,
    "consult_canonical_context": engagement_context.consult_canonical_context,
    "consult_engagement_context": engagement_context.consult_engagement_context,
    "read_non_episodic_memory": engagement_context.read_non_episodic_memory,
    "write_non_episodic_memory": engagement_context.write_non_episodic_memory,
    "update_canonical_field": engagement_context.update_canonical_field,
    "ensure_self_rooted_spine": engagement_context.ensure_self_rooted_spine,
    "read_system_observability": operational_observability.read_system_observability,
    "render_status_dashboard": status_dashboard.render_status_dashboard,
    "read_autonomic_maintenance_context": (
        operational_observability.read_autonomic_maintenance_context
    ),
    "recall_relevant_episodes": episodic_memory.recall_relevant_episodes,
    "recall_recent_episodes": episodic_memory.recall_recent_episodes,
    "recall_contextual_episodes": episodic_memory.recall_contextual_episodes,
    # Gmail / Correspondent
    "gmail_user_search_threads": google_mail.gmail_user_search_threads,
    "gmail_user_get_thread": google_mail.gmail_user_get_thread,
    "gmail_user_list_drafts": google_mail.gmail_user_list_drafts,
    "gmail_user_create_draft": google_mail.gmail_user_create_draft,
    "gmail_user_update_draft": google_mail.gmail_user_update_draft,
    "gmail_user_delete_draft": google_mail.gmail_user_delete_draft,
    "gmail_user_send_draft": google_mail.gmail_user_send_draft,
    "gmail_test_search_threads": google_mail.gmail_test_search_threads,
    "gmail_test_get_thread": google_mail.gmail_test_get_thread,
    "gmail_test_list_drafts": google_mail.gmail_test_list_drafts,
    "gmail_test_create_draft": google_mail.gmail_test_create_draft,
    "gmail_test_update_draft": google_mail.gmail_test_update_draft,
    "gmail_test_delete_draft": google_mail.gmail_test_delete_draft,
    "gmail_test_send_draft": google_mail.gmail_test_send_draft,
    "calendar_user_list_events": google_calendar.calendar_user_list_events,
    "calendar_user_create_event": google_calendar.calendar_user_create_event,
    "calendar_user_patch_event": google_calendar.calendar_user_patch_event,
    "calendar_user_delete_event": google_calendar.calendar_user_delete_event,
    "calendar_user_respond_event": google_calendar.calendar_user_respond_event,
    "calendar_test_list_events": google_calendar.calendar_test_list_events,
    "calendar_test_create_event": google_calendar.calendar_test_create_event,
    "calendar_test_patch_event": google_calendar.calendar_test_patch_event,
    "calendar_test_delete_event": google_calendar.calendar_test_delete_event,
    "calendar_test_respond_event": google_calendar.calendar_test_respond_event,
    # Activities Management
    "garmin_list_activities": garmin.garmin_list_activities,
    "garmin_get_activity": garmin.garmin_get_activity,
    "garmin_get_daily_summary": garmin.garmin_get_daily_summary,
    "garmin_get_user_stats": garmin.garmin_get_user_stats,
    "garmin_route_aware_iwt_analysis": garmin.garmin_route_aware_iwt_analysis,
    # Calendar Stewardship — Google-Calendar-shaped mock
    "cal_list_events": calendar_mock.cal_list_events,
    "cal_propose_reschedule": calendar_mock.cal_propose_reschedule,
    "cal_invite_stance": calendar_mock.cal_invite_stance,
    "cal_issue_reschedule": calendar_mock.cal_issue_reschedule,
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
    "pm_create_invariant": practice_management.pm_create_invariant,
    "pm_amend_invariant": practice_management.pm_amend_invariant,
    "pm_tombstone_invariant": practice_management.pm_tombstone_invariant,
    "pm_reload_seed_substrate": practice_management.pm_reload_seed_substrate,
    "pm_check_documentation_impact": practice_management.pm_check_documentation_impact,
    # Judge — primitives
    "judge_list_recent_enactments": judge.judge_list_recent_enactments,
    "judge_read_enactment_steps": judge.judge_read_enactment_steps,
    "judge_read_bundle": judge.judge_read_bundle,
    "judge_emit_friction": judge.judge_emit_friction,
    # Smoother — two smoother-specific materials; the other six affordances
    # in the Smoother bundle reuse PM materials registered above.
    "smoother_read_pending_friction": smoother.smoother_read_pending_friction,
    "smoother_mark_addressed": smoother.smoother_mark_addressed,
    "smoother_read_friction_kinds": smoother.smoother_read_friction_kinds,
    "smoother_rename_friction": smoother.smoother_rename_friction,
    # RemSleep / memory recall and consolidation.
    "remsleep_read_checkpoint": remsleep.remsleep_read_checkpoint,
    "remsleep_recall_unreviewed_episodes": remsleep.remsleep_recall_unreviewed_episodes,
    "remsleep_read_updated_graph_nodes": remsleep.remsleep_read_updated_graph_nodes,
    "remsleep_dispatch_memory_signal": remsleep.remsleep_dispatch_memory_signal,
    "remsleep_read_memory_signals": remsleep.remsleep_read_memory_signals,
    "remsleep_mark_memory_signal_handled": remsleep.remsleep_mark_memory_signal_handled,
    "remsleep_stage_memory_candidate": remsleep.remsleep_stage_memory_candidate,
    "remsleep_record_checkpoint": remsleep.remsleep_record_checkpoint,
}


def register(name: str, fn: Callable[..., object]) -> None:
    """Bind a callable to a material name. Used for dynamic registration."""
    FUNCTIONS[name] = fn


def _compile_dynamic_expression(expression: str) -> CodeType:
    tree = ast.parse(expression, mode="eval")
    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED_EXPRESSION_NODES):
            raise ValueError(
                f"unsupported expression node {type(node).__name__}; "
                "dynamic material expressions may only combine literals and args"
            )
        if isinstance(node, ast.Name) and node.id != "args":
            raise ValueError(
                f"unknown name {node.id!r}; dynamic material expressions only expose args"
            )
    return compile(tree, "<dynamic-material>", "eval")


def build_dynamic_material_function(
    name: str,
    implementation: Mapping[str, Any],
) -> Callable[..., object]:
    """Build a callable from a persisted dynamic-material implementation."""
    kind = implementation.get("kind")
    if kind == "constant":
        result = implementation.get("result")

        def constant_material(**_arguments: object) -> object:
            return result

        constant_material.__name__ = name
        return constant_material
    if kind == "echo":

        def echo_material(**arguments: object) -> object:
            return {"arguments": arguments}

        echo_material.__name__ = name
        return echo_material
    if kind == "expression":
        expression = implementation.get("expression")
        if not isinstance(expression, str) or not expression.strip():
            raise ValueError("expression implementation requires a non-blank expression")
        code = _compile_dynamic_expression(expression)

        def expression_material(**arguments: object) -> object:
            return eval(code, {"__builtins__": {}}, {"args": arguments})

        expression_material.__name__ = name
        return expression_material
    raise ValueError(
        "dynamic material implementation kind must be one of 'constant', 'echo', or 'expression'"
    )


def register_dynamic_material(
    name: str,
    implementation: Mapping[str, Any],
) -> None:
    """Build and register one dynamic material function."""
    register(name, build_dynamic_material_function(name, implementation))


def register_dynamic_materials(
    material_functions: Iterable[tuple[str, Mapping[str, Any]]],
) -> None:
    """Register all dynamic material functions loaded from substrate files."""
    for name, implementation in material_functions:
        register_dynamic_material(name, implementation)


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
