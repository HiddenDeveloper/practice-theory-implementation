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
from practice_theory_implementation.types import Invariant, Substrate

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


@dataclass(frozen=True, slots=True)
class _Evaluable:
    """One determinable check to evaluate, unifying the two sources active during
    the migration: a legacy free-floating `Invariant` and an affordance-owned
    `Check`. `fire_id` is the stable firing/idempotency identity — the bare
    invariant id, or `affordance:<owner_id>::<check_id>` — so the two sources
    never collide in the firing ledger."""

    fire_id: str
    trigger: str
    friction_kind: str
    message: str
    forbid_when: Mapping[str, object]


def _evaluable_from_invariant(inv: Invariant) -> _Evaluable:
    return _Evaluable(inv.id, inv.trigger, inv.friction_kind, inv.message, inv.forbid_when)


def gather_active_checks(substrate: Substrate) -> list[_Evaluable]:
    """Every active determinable check, from both sources during the migration.

    The legacy free-floating `invariants` pool (retired in a later phase) plus
    affordance-owned `preconditions` (the dissolved home — see
    docs/plans/invariants-as-affordance-material-checks.md). Affordance checks
    fire under the identity `affordance:<owner_id>::<check_id>`.
    """
    out: list[_Evaluable] = []
    for inv in substrate.invariants.values():
        if inv.status == "active":
            out.append(_evaluable_from_invariant(inv))
    for aff in substrate.affordances.values():
        for chk in aff.preconditions:
            if chk.status == "active":
                out.append(
                    _Evaluable(
                        fire_id=f"affordance:{aff.id}::{chk.id}",
                        trigger=chk.trigger,
                        friction_kind=chk.friction_kind,
                        message=chk.message,
                        forbid_when=chk.forbid_when,
                    )
                )
    return out


def _parse_args(step: StepRow) -> dict:
    try:
        data = json.loads(step.arguments_json)
    except (ValueError, TypeError):
        return {}
    return data if isinstance(data, dict) else {}


@dataclass(frozen=True, slots=True)
class Violation:
    """What a check-material returns when a determinable contract is breached:
    enough to raise+resolve the friction with no LLM."""

    friction_kind: str
    message: str
    trigger_step_id: int


def build_enactment_check(
    *,
    trigger: str,
    forbid_when: Mapping[str, object],
    friction_kind: str,
    message: str,
) -> Callable[[list[StepRow]], Violation | None]:
    """Build a check-material callable from a step-predicate.

    The runtime of the `enactment_check` material kind — the determinable check
    as a deterministic function over an enactment's steps, so it lives in the
    materials layer (registry-resolvable by name) rather than a separate
    `invariants` pool (see docs/plans/determinable-checks-are-materials.md). The
    callable is self-contained: it does its own trigger-gating, so one
    check-material can be referenced by many affordances. It evaluates
    `forbid_when` against the steps before the last `trigger` step; a satisfied
    predicate is a violation. Validates the predicate at build time so a bad
    `forbid_when` never reaches a live enactment.
    """
    if predicate_error := validate_predicate(forbid_when):
        raise ValueError(f"enactment_check forbid_when invalid: {predicate_error}")

    def check(steps: list[StepRow]) -> Violation | None:
        # cspell:ignore idxs
        trigger_idxs = [k for k, s in enumerate(steps) if s.material_name == trigger]
        if not trigger_idxs:
            return None
        ti = trigger_idxs[-1]
        ctx = EvalContext(steps=steps, trigger_index=ti, arguments=_parse_args(steps[ti]))
        if evaluate_predicate(forbid_when, ctx):
            return Violation(
                friction_kind=friction_kind,
                message=message,
                trigger_step_id=steps[ti].id,
            )
        return None

    return check


def run_invariants(
    store: EnactmentStore,
    enactment: EnactmentRow,
    *,
    invariants: list[Invariant] | None = None,
    substrate: Substrate | None = None,
) -> list[Firing]:
    """Evaluate every active determinable check against one closed enactment.

    A check is a legacy free-floating `Invariant` or an affordance-owned
    `Check`; both are evaluated by the same predicate machinery. For each check
    whose `trigger` material appears as a step, the predicate is evaluated
    against the steps before the (last) trigger step. On violation the friction
    is recorded AND immediately marked addressed — raised+resolved
    deterministically, the Smoother inbox untouched. Idempotent per
    (check, enactment) via the invariant_firings table, keyed on the check's
    stable firing identity.

    Source: pass an explicit `invariants` list to evaluate exactly that set
    (tests, replays). Otherwise the checks come from `substrate` (or the loaded
    substrate when omitted) — the union of the legacy `invariants` pool and
    affordance `preconditions` via `gather_active_checks`.
    """
    if invariants is not None:
        evaluables = [_evaluable_from_invariant(i) for i in invariants if i.status == "active"]
    else:
        if substrate is None:
            from practice_theory_implementation.substrate_loader import loaded

            substrate = loaded().substrate
        evaluables = gather_active_checks(substrate)
    if not evaluables:
        return []
    steps = store.steps_for(enactment.id)
    if not steps:
        return []

    firings: list[Firing] = []
    for ev in evaluables:
        # cspell:ignore idxs
        trigger_idxs = [k for k, s in enumerate(steps) if s.material_name == ev.trigger]
        if not trigger_idxs:
            continue
        if store.invariant_fired(ev.fire_id, enactment.id):
            continue
        ti = trigger_idxs[-1]
        ctx = EvalContext(steps=steps, trigger_index=ti, arguments=_parse_args(steps[ti]))
        try:
            violated = evaluate_predicate(ev.forbid_when, ctx)
        except Exception:
            logger.exception(
                "check %s failed to evaluate on %s; skipping", ev.fire_id, enactment.id
            )
            continue
        if not violated:
            continue
        observer = f"{INVARIANT_OBSERVER_PREFIX}{ev.fire_id}"
        # Detect + auto-resolve + record the firing, atomically: the rule closes
        # the Friction in the same breath it raises it, and a crash cannot leave
        # that half-done (which would re-fire and duplicate on retry). See
        # `record_invariant_resolution`.
        friction_id = store.record_invariant_resolution(
            invariant_id=ev.fire_id,
            enactment_id=enactment.id,
            observer_id=observer,
            kind=ev.friction_kind,
            content=ev.message,
            observation_data={
                "invariant_id": ev.fire_id,
                "trigger_material": ev.trigger,
                "trigger_step_id": steps[ti].id,
                "auto_resolved": True,
            },
        )
        _emit_firing(ev.fire_id, enactment.id, friction_id, ev.friction_kind)
        firings.append(Firing(ev.fire_id, enactment.id, friction_id))
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
