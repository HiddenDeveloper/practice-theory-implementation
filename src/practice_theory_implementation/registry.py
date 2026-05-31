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
    garmin_mock,
    judge,
    practice_management,
    reflection_mock,
    smoother,
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
    "ensure_self_rooted_spine": engagement_context.ensure_self_rooted_spine,
    "recall_relevant_episodes": episodic_memory.recall_relevant_episodes,
    "recall_recent_episodes": episodic_memory.recall_recent_episodes,
    "recall_contextual_episodes": episodic_memory.recall_contextual_episodes,
    # Activities Management
    "garmin_list_activities": garmin_mock.garmin_list_activities,
    "garmin_get_activity": garmin_mock.garmin_get_activity,
    "garmin_get_daily_summary": garmin_mock.garmin_get_daily_summary,
    "garmin_get_user_stats": garmin_mock.garmin_get_user_stats,
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
        "dynamic material implementation kind must be one of "
        "'constant', 'echo', or 'expression'"
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
    """Register all dynamic material functions loaded from the substrate overlay."""
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
