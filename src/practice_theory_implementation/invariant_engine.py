"""The deterministic invariant engine — runs governed guards, no LLM.

An Invariant is a determinable contract over an enactment's step history,
authored as substrate by the Smoother. This module evaluates them: a small
declarative predicate language (validated at author time, no code-eval) plus
`run_invariants`, which scans a closed enactment and — when a rule is violated —
both RAISES the friction and AUTO-RESOLVES it (detect + auto-resolve), so no
Judge or Smoother LLM is ever dispatched for the determinable case. Judgement
re-enters only when the Smoother authors/refines a rule and when the scheduled
audit reviews how the rules have fired (see [[intelligence-only-where-judgement-needed]]).

Predicate shape: a mapping with exactly one key — a boolean combinator
(`all`/`any`/`not`) or a leaf op. Leaf ops are pure functions over the
enactment's steps and the trigger step's arguments. Extend the language by
adding to `_LEAF_OPS`; `validate_predicate` then accepts it automatically.
"""

from __future__ import annotations

import fnmatch
import json
import logging
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

from practice_theory_implementation.trail import EnactmentRow, EnactmentStore, StepRow
from practice_theory_implementation.types import Invariant

logger = logging.getLogger(__name__)

INVARIANT_OBSERVER_PREFIX = "system:invariant:"


@dataclass(slots=True)
class EvalContext:
    """What a predicate sees: the enactment's steps, the trigger step position,
    and the trigger step's parsed arguments."""

    steps: list[StepRow]
    trigger_index: int
    arguments: dict


# --- leaf predicate ops (pure, deterministic) ------------------------------

LeafOp = Callable[[object, EvalContext], bool]


def _op_any_earlier_step_result_contains(arg: object, ctx: EvalContext) -> bool:
    if not isinstance(arg, str):
        return False
    return any(arg in s.result_summary for s in ctx.steps[: ctx.trigger_index])


def _op_step_exists(arg: object, ctx: EvalContext) -> bool:
    if not isinstance(arg, Mapping):
        return False
    aff = arg.get("affordance_id")
    mat = arg.get("material_name")
    rc = arg.get("result_contains")
    for s in ctx.steps:
        if aff is not None and s.affordance_id != aff:
            continue
        if mat is not None and not fnmatch.fnmatch(s.material_name, str(mat)):
            continue
        if rc is not None and str(rc) not in s.result_summary:
            continue
        return True
    return False


def _op_arg_present(arg: object, ctx: EvalContext) -> bool:
    return isinstance(arg, str) and arg in ctx.arguments


def _op_arg_nonempty(arg: object, ctx: EvalContext) -> bool:
    return isinstance(arg, str) and bool(ctx.arguments.get(arg))


_LEAF_OPS: dict[str, LeafOp] = {
    "any_earlier_step_result_contains": _op_any_earlier_step_result_contains,
    "step_exists": _op_step_exists,
    "arg_present": _op_arg_present,
    "arg_nonempty": _op_arg_nonempty,
}
_STRING_LEAF_OPS = {"any_earlier_step_result_contains", "arg_present", "arg_nonempty"}
_BOOL_OPS = ("all", "any", "not")


def register_leaf_op(name: str, op: LeafOp) -> None:
    """Register a new leaf predicate op (extends what an invariant can express)."""
    _LEAF_OPS[name] = op


# --- validation (runs at author/amend AND load time) -----------------------


def validate_predicate(pred: object) -> str | None:
    """Return an error string if `pred` is not an evaluable predicate, else None.

    Called before an invariant is persisted, so a non-evaluable rule can never
    be saved, and at load time so a malformed file is skipped not crashed.
    """
    if not isinstance(pred, Mapping):
        return f"predicate must be a mapping, got {type(pred).__name__}"
    if len(pred) != 1:
        return f"predicate must have exactly one key, got {sorted(map(str, pred))}"
    op, arg = next(iter(pred.items()))
    if op in ("all", "any"):
        if isinstance(arg, str) or not isinstance(arg, Sequence):
            return f"{op!r} expects a list of predicates"
        for sub in arg:
            if err := validate_predicate(sub):
                return err
        return None
    if op == "not":
        return validate_predicate(arg)
    if op not in _LEAF_OPS:
        known = sorted([*_LEAF_OPS, *_BOOL_OPS])
        return f"unknown predicate op {op!r} (known: {known})"
    if op == "step_exists" and not isinstance(arg, Mapping):
        return "step_exists expects a mapping {affordance_id?, material_name?, result_contains?}"
    if op in _STRING_LEAF_OPS and not isinstance(arg, str):
        return f"{op!r} expects a string argument"
    return None


def evaluate_predicate(pred: Mapping[str, object], ctx: EvalContext) -> bool:
    """Evaluate a (pre-validated) predicate against the context. Deterministic."""
    op, arg = next(iter(pred.items()))
    if op == "all":
        return all(evaluate_predicate(p, ctx) for p in arg)  # type: ignore[union-attr]
    if op == "any":
        return any(evaluate_predicate(p, ctx) for p in arg)  # type: ignore[union-attr]
    if op == "not":
        return not evaluate_predicate(arg, ctx)  # type: ignore[arg-type]
    return _LEAF_OPS[op](arg, ctx)


# --- the engine: run invariants over a closed enactment --------------------


@dataclass(frozen=True, slots=True)
class Firing:
    invariant_id: str
    enactment_id: str
    friction_id: int


def _parse_args(step: StepRow) -> dict:
    try:
        data = json.loads(step.arguments_json)
    except (ValueError, TypeError):
        return {}
    return data if isinstance(data, dict) else {}


def run_invariants(
    store: EnactmentStore,
    enactment: EnactmentRow,
    *,
    invariants: list[Invariant] | None = None,
) -> list[Firing]:
    """Evaluate every active invariant against one closed enactment.

    For each active invariant whose `trigger` material appears as a step, the
    predicate is evaluated against the steps before the (last) trigger step. On
    violation the friction is recorded AND immediately marked addressed by the
    invariant — raised+resolved deterministically, the Smoother inbox untouched.
    Idempotent per (invariant, enactment) via the invariant_firings table.

    `invariants` defaults to the loaded substrate's active invariants; pass an
    explicit list to evaluate a specific set (tests, replays).
    """
    if invariants is None:
        from practice_theory_implementation.substrate_loader import loaded

        invariants = list(loaded().substrate.invariants.values())
    active = [inv for inv in invariants if inv.status == "active"]
    if not active:
        return []
    steps = store.steps_for(enactment.id)
    if not steps:
        return []

    firings: list[Firing] = []
    for inv in active:
        # cspell:ignore idxs
        trigger_idxs = [k for k, s in enumerate(steps) if s.material_name == inv.trigger]
        if not trigger_idxs:
            continue
        if store.invariant_fired(inv.id, enactment.id):
            continue
        ti = trigger_idxs[-1]
        ctx = EvalContext(steps=steps, trigger_index=ti, arguments=_parse_args(steps[ti]))
        try:
            violated = evaluate_predicate(inv.forbid_when, ctx)
        except Exception:
            logger.exception(
                "invariant %s failed to evaluate on %s; skipping", inv.id, enactment.id
            )
            continue
        if not violated:
            continue
        observer = f"{INVARIANT_OBSERVER_PREFIX}{inv.id}"
        # Detect + auto-resolve + record the firing, atomically: the rule closes
        # the Friction in the same breath it raises it, and a crash cannot leave
        # that half-done (which would re-fire and duplicate on retry). See
        # `record_invariant_resolution`.
        friction_id = store.record_invariant_resolution(
            invariant_id=inv.id,
            enactment_id=enactment.id,
            observer_id=observer,
            kind=inv.friction_kind,
            content=inv.message,
            observation_data={
                "invariant_id": inv.id,
                "trigger_material": inv.trigger,
                "trigger_step_id": steps[ti].id,
                "auto_resolved": True,
            },
        )
        _emit_firing(inv.id, enactment.id, friction_id, inv.friction_kind)
        firings.append(Firing(inv.id, enactment.id, friction_id))
    return firings


def _emit_firing(
    invariant_id: str, enactment_id: str, friction_id: int, friction_kind: str
) -> None:
    import contextlib

    with contextlib.suppress(Exception):
        from practice_theory_implementation.observability import emit_autonomic_event

        emit_autonomic_event(
            name="invariant.fired",
            notification=(
                f"invariant {invariant_id} fired on {enactment_id}: "
                f"{friction_kind} raised+resolved deterministically (friction {friction_id})"
            ),
            attributes={
                "practice.invariant.id": invariant_id,
                "practice.invariant.enactment_id": enactment_id,
                "practice.invariant.friction_id": friction_id,
                "practice.invariant.friction_kind": friction_kind,
            },
        )
