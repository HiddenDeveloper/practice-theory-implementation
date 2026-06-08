"""The deterministic invariant engine — predicate language + detect/auto-resolve.

Guards the core of the governed-invariants subsystem: a determinable contract
over an enactment's steps is caught and resolved with no LLM. The worked rule
(`no_close_on_unpersisted_amendment`) reproduces, deterministically, the finding
that cost a Judge dispatch (Friction 137 on enactment 9bc25487).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from practice_theory_implementation import invariant_engine as ie
from practice_theory_implementation.trail import EnactmentStore, StepRow
from practice_theory_implementation.types import Invariant

PERSISTED_FALSE = '"persisted": false'

RULE = Invariant(
    id="no_close_on_unpersisted_amendment",
    name="Don't mark addressed after a non-persisted amendment",
    trigger="smoother_mark_addressed",
    friction_kind="non_persisted_amendment_marked_addressed",
    message="closure rests on a change that did not save",
    forbid_when={"any_earlier_step_result_contains": PERSISTED_FALSE},
    content="body",
)


# --- predicate validation --------------------------------------------------


def test_validate_accepts_known_predicates() -> None:
    assert ie.validate_predicate({"any_earlier_step_result_contains": "x"}) is None
    assert ie.validate_predicate({"step_exists": {"material_name": "pm_*"}}) is None
    assert ie.validate_predicate({"not": {"arg_present": "rationale"}}) is None
    assert (
        ie.validate_predicate(
            {"all": [{"arg_present": "a"}, {"any": [{"arg_nonempty": "b"}]}]}
        )
        is None
    )


def test_validate_rejects_malformed() -> None:
    assert "unknown predicate op" in (ie.validate_predicate({"nope": 1}) or "")
    assert "exactly one key" in (ie.validate_predicate({"a": 1, "b": 2}) or "")
    assert "mapping" in (ie.validate_predicate("notamap") or "")  # cspell:ignore notamap
    assert "expects a list" in (ie.validate_predicate({"all": "x"}) or "")
    assert "expects a string" in (
        ie.validate_predicate({"any_earlier_step_result_contains": 5}) or ""
    )


# --- predicate evaluation --------------------------------------------------


def _step(i: int, material: str, result: str, affordance: str = "a") -> StepRow:
    return StepRow(
        id=i,
        enactment_id="e",
        affordance_id=affordance,
        material_name=material,
        arguments_json="{}",
        result_summary=result,
        started_at="t",
        completed_at="t",
        duration_ms=1,
    )


def test_any_earlier_step_result_contains_respects_order() -> None:
    steps = [
        _step(1, "pm_amend_material", '{"persisted": false}'),
        _step(2, "smoother_mark_addressed", '{"addressed": 1}'),
    ]
    ctx = ie.EvalContext(steps=steps, trigger_index=1, arguments={})
    assert ie.evaluate_predicate(RULE.forbid_when, ctx) is True
    # If the persisted:false step came AFTER the trigger, it is not "earlier".
    ctx_after = ie.EvalContext(steps=steps, trigger_index=0, arguments={})
    assert ie.evaluate_predicate(RULE.forbid_when, ctx_after) is False


def test_step_exists_glob_and_arg_ops() -> None:
    steps = [_step(1, "pm_amend_material", "ok")]
    ctx = ie.EvalContext(steps=steps, trigger_index=1, arguments={"rationale": "x"})
    assert ie.evaluate_predicate({"step_exists": {"material_name": "pm_*"}}, ctx)
    assert not ie.evaluate_predicate({"step_exists": {"material_name": "judge_*"}}, ctx)
    assert ie.evaluate_predicate({"arg_present": "rationale"}, ctx)
    assert not ie.evaluate_predicate({"arg_present": "missing"}, ctx)
    assert ie.evaluate_predicate({"arg_nonempty": "rationale"}, ctx)


# --- run_invariants: detect + auto-resolve ---------------------------------


def _seed_unpersisted_then_close(store: EnactmentStore) -> str:
    eid = store.open_enactment("smoother", mode="autonomic")
    store.record_step(
        enactment_id=eid,
        affordance_id="amend_material",
        material_name="pm_amend_material",
        arguments={"name": "judge_list_recent_enactments"},
        result={"amended": {"material": "judge_list_recent_enactments", "persisted": False}},
        started_at="2026-06-04T00:00:00+00:00",
        completed_at="2026-06-04T00:00:01+00:00",
        duration_ms=1,
    )
    store.record_step(
        enactment_id=eid,
        affordance_id="mark_friction_addressed",
        material_name="smoother_mark_addressed",
        arguments={"friction_id": 102},
        result={"addressed": 102},
        started_at="2026-06-04T00:00:02+00:00",
        completed_at="2026-06-04T00:00:03+00:00",
        duration_ms=1,
    )
    store.close_enactment(eid)
    return eid


def test_fires_raises_and_auto_resolves(tmp_path: Path) -> None:
    store = EnactmentStore(tmp_path / "trail.db")
    eid = _seed_unpersisted_then_close(store)
    enactment = store.recent_enactments(limit=1)[0]

    firings = ie.run_invariants(store, enactment, invariants=[RULE])

    assert len(firings) == 1
    f = firings[0]
    assert f.invariant_id == RULE.id
    friction = next(fr for fr in store.all_friction() if fr.id == f.friction_id)
    assert friction.kind == "non_persisted_amendment_marked_addressed"
    assert friction.observing_enactment_id == f"system:invariant:{RULE.id}"
    assert friction.addressed_at is not None  # auto-resolved, never hits the Smoother
    # the Smoother inbox is untouched
    assert store.pending_smoother_inbox_count() == 0
    assert store.invariant_fired(RULE.id, eid)


def test_idempotent(tmp_path: Path) -> None:
    store = EnactmentStore(tmp_path / "trail.db")
    _seed_unpersisted_then_close(store)
    enactment = store.recent_enactments(limit=1)[0]
    assert len(ie.run_invariants(store, enactment, invariants=[RULE])) == 1
    assert ie.run_invariants(store, enactment, invariants=[RULE]) == []


def test_no_violation_does_not_fire(tmp_path: Path) -> None:
    store = EnactmentStore(tmp_path / "trail.db")
    eid = store.open_enactment("smoother", mode="autonomic")
    store.record_step(
        enactment_id=eid,
        affordance_id="amend_material",
        material_name="pm_amend_material",
        arguments={},
        result={"amended": {"material": "x", "persisted": True}},
        started_at="t",
        completed_at="t",
        duration_ms=1,
    )
    store.record_step(
        enactment_id=eid,
        affordance_id="mark_friction_addressed",
        material_name="smoother_mark_addressed",
        arguments={},
        result={"addressed": 1},
        started_at="t",
        completed_at="t",
        duration_ms=1,
    )
    store.close_enactment(eid)
    enactment = store.recent_enactments(limit=1)[0]
    assert ie.run_invariants(store, enactment, invariants=[RULE]) == []


def test_tombstoned_rule_skipped(tmp_path: Path) -> None:
    store = EnactmentStore(tmp_path / "trail.db")
    _seed_unpersisted_then_close(store)
    enactment = store.recent_enactments(limit=1)[0]
    from dataclasses import replace

    dead = replace(RULE, status="tombstoned")
    assert ie.run_invariants(store, enactment, invariants=[dead]) == []


# --- atomicity: friction + addressed + firing commit as one transaction ----


class _FailOnFiringCursor:
    """Passes every statement through to a real cursor except the
    invariant_firings INSERT, which raises — a stand-in for a crash after the
    Friction insert but before the firing is committed."""

    def __init__(self, real: sqlite3.Cursor) -> None:
        self._real = real

    def execute(self, sql: str, *args: object, **kwargs: object) -> object:
        if "invariant_firings" in sql:
            raise sqlite3.OperationalError("simulated crash before firing commit")
        return self._real.execute(sql, *args, **kwargs)

    def __getattr__(self, name: str) -> object:
        return getattr(self._real, name)


class _FailOnFiringConn:
    def __init__(self, real: sqlite3.Connection) -> None:
        self._real = real

    def cursor(self) -> _FailOnFiringCursor:
        return _FailOnFiringCursor(self._real.cursor())

    def __getattr__(self, name: str) -> object:
        return getattr(self._real, name)


def test_resolution_rolls_back_when_firing_write_fails(tmp_path: Path) -> None:
    store = EnactmentStore(tmp_path / "trail.db")
    eid = store.open_enactment("smoother", mode="autonomic")
    store.close_enactment(eid)

    real_conn = store._conn
    store._conn = _FailOnFiringConn(real_conn)  # type: ignore[assignment]
    try:
        with pytest.raises(sqlite3.OperationalError):
            store.record_invariant_resolution(
                invariant_id=RULE.id,
                enactment_id=eid,
                observer_id=f"system:invariant:{RULE.id}",
                kind=RULE.friction_kind,
                content=RULE.message,
            )
    finally:
        store._conn = real_conn  # restore so the read-side assertions work

    # The Friction insert must have rolled back with the failed firing: no
    # half-resolved state, so a retry re-fires cleanly instead of leaving a
    # duplicate (and never an unaddressed Friction leaking to the Smoother).
    assert store.all_friction() == []
    assert store.invariant_fired(RULE.id, eid) is False
    assert store.pending_smoother_inbox_count() == 0
