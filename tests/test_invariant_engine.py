"""The deterministic check engine — predicate language + check-materials.

A determinable check is a deterministic function over an enactment's steps (a
check-material). This guards the predicate language, `build_enactment_check`
(the `enactment_check` material kind's runtime), and `run_enactment_checks`,
which resolves the check-materials an affordance references and raises+resolves
their violations with no LLM.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from practice_theory_implementation import invariant_engine as ie
from practice_theory_implementation import registry
from practice_theory_implementation.trail import EnactmentStore, StepRow
from practice_theory_implementation.types import Affordance, Substrate

PERSISTED_FALSE = '"persisted": false'
LIST_BEFORE_DETAIL = {"not": {"step_exists": {"material_name": "garmin_list_activities"}}}


# --- predicate validation --------------------------------------------------


def test_validate_accepts_known_predicates() -> None:
    assert ie.validate_predicate({"any_earlier_step_result_contains": "x"}) is None
    assert ie.validate_predicate({"step_exists": {"material_name": "pm_*"}}) is None
    assert ie.validate_predicate({"not": {"arg_present": "rationale"}}) is None
    assert (
        ie.validate_predicate({"all": [{"arg_present": "a"}, {"any": [{"arg_nonempty": "b"}]}]})
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
        id=i, enactment_id="e", affordance_id=affordance, material_name=material,
        arguments_json="{}", result_summary=result, started_at="t", completed_at="t",
        duration_ms=1,
    )


def test_any_earlier_step_result_contains_respects_order() -> None:
    pred = {"any_earlier_step_result_contains": PERSISTED_FALSE}
    steps = [
        _step(1, "pm_amend_material", '{"persisted": false}'),
        _step(2, "smoother_mark_addressed", '{"addressed": 1}'),
    ]
    assert ie.evaluate_predicate(pred, ie.EvalContext(steps=steps, trigger_index=1, arguments={}))
    # The persisted:false step AFTER the trigger is not "earlier".
    assert not ie.evaluate_predicate(
        pred, ie.EvalContext(steps=steps, trigger_index=0, arguments={})
    )


def test_step_exists_glob_and_arg_ops() -> None:
    ctx = ie.EvalContext(steps=[_step(1, "pm_amend_material", "ok")], trigger_index=1,
                         arguments={"rationale": "x"})
    assert ie.evaluate_predicate({"step_exists": {"material_name": "pm_*"}}, ctx)
    assert not ie.evaluate_predicate({"step_exists": {"material_name": "judge_*"}}, ctx)
    assert ie.evaluate_predicate({"arg_present": "rationale"}, ctx)
    assert not ie.evaluate_predicate({"arg_present": "missing"}, ctx)
    assert ie.evaluate_predicate({"arg_nonempty": "rationale"}, ctx)


# --- build_enactment_check: a check is a deterministic function over steps ---


def test_build_enactment_check_fires_when_predicate_holds() -> None:
    check = ie.build_enactment_check(
        trigger="garmin_get_activity", forbid_when=LIST_BEFORE_DETAIL,
        friction_kind="quality_affordance_coverage", message="detail before list",
    )
    v = check([_step(1, "garmin_get_activity", "ok")])
    assert v is not None
    assert v.friction_kind == "quality_affordance_coverage"
    assert v.message == "detail before list"
    assert v.trigger_step_id == 1


def test_build_enactment_check_clears_when_satisfied_or_untriggered() -> None:
    check = ie.build_enactment_check(
        trigger="garmin_get_activity", forbid_when=LIST_BEFORE_DETAIL,
        friction_kind="k", message="m",
    )
    ok = [_step(1, "garmin_list_activities", "ok"), _step(2, "garmin_get_activity", "ok")]
    assert check(ok) is None  # list before detail -> satisfied
    assert check([_step(1, "something_else", "ok")]) is None  # trigger never used


def test_build_enactment_check_rejects_bad_predicate() -> None:
    with pytest.raises(ValueError, match="forbid_when invalid"):
        ie.build_enactment_check(
            trigger="t", forbid_when={"nope": 1}, friction_kind="k", message="m"
        )


def test_registry_builds_enactment_check_material() -> None:
    fn = registry.build_dynamic_material_function(
        "check_list_before_detail",
        {
            "kind": "enactment_check", "trigger": "garmin_get_activity",
            "friction_kind": "quality_affordance_coverage", "message": "detail before list",
            "forbid_when": LIST_BEFORE_DETAIL,
        },
    )
    assert fn.__name__ == "check_list_before_detail"
    assert fn([_step(1, "garmin_get_activity", "ok")]) is not None
    list_then_detail = [
        _step(1, "garmin_list_activities", "x"), _step(2, "garmin_get_activity", "x")
    ]
    assert fn(list_then_detail) is None


def test_registry_enactment_check_requires_fields() -> None:
    with pytest.raises(ValueError, match="enactment_check requires"):
        registry.build_dynamic_material_function("bad", {"kind": "enactment_check", "trigger": "t"})


# --- run_enactment_checks: resolve referenced check-materials, raise+resolve -


def _seed_unpersisted_then_close(store: EnactmentStore) -> str:
    eid = store.open_enactment("smoother", mode="autonomic")
    store.record_step(
        enactment_id=eid, affordance_id="amend_material", material_name="pm_amend_material",
        arguments={"name": "x"},
        result={"amended": {"material": "x", "persisted": False}},
        started_at="2026-06-04T00:00:00+00:00", completed_at="2026-06-04T00:00:01+00:00",
        duration_ms=1,
    )
    store.record_step(
        enactment_id=eid, affordance_id="mark_friction_addressed",
        material_name="smoother_mark_addressed", arguments={"friction_id": 102},
        result={"addressed": 102}, started_at="2026-06-04T00:00:02+00:00",
        completed_at="2026-06-04T00:00:03+00:00", duration_ms=1,
    )
    store.close_enactment(eid)
    return eid


def _register_check(name: str) -> str:
    registry.register(
        name,
        ie.build_enactment_check(
            trigger="smoother_mark_addressed",
            forbid_when={"any_earlier_step_result_contains": PERSISTED_FALSE},
            friction_kind="non_persisted_amendment_marked_addressed",
            message="closure rests on a change that did not save",
        ),
    )
    return name


def _substrate_referencing(name: str, *affordance_ids: str) -> Substrate:
    affs = {
        aid: Affordance(id=aid, name=aid, description="", materials=(), check_materials=(name,))
        for aid in affordance_ids
    }
    return Substrate(affordances=affs)


def test_referenced_check_fires_raises_and_auto_resolves(tmp_path: Path) -> None:
    name = _register_check("test_check_no_close_on_unpersisted")
    store = EnactmentStore(tmp_path / "trail.db")
    eid = _seed_unpersisted_then_close(store)
    en = store.recent_enactments(limit=1)[0]

    firings = ie.run_enactment_checks(store, en, substrate=_substrate_referencing(name, "mark"))
    assert len(firings) == 1
    f = firings[0]
    assert f.invariant_id == name  # firing keyed on the check-material name
    fr = next(x for x in store.all_friction() if x.id == f.friction_id)
    assert fr.kind == "non_persisted_amendment_marked_addressed"
    assert fr.observing_enactment_id == f"system:invariant:{name}"
    assert fr.addressed_at is not None  # auto-resolved, never hits the Smoother
    assert store.pending_smoother_inbox_count() == 0
    assert store.invariant_fired(name, eid)


def test_idempotent(tmp_path: Path) -> None:
    name = _register_check("test_check_idempotent")
    store = EnactmentStore(tmp_path / "trail.db")
    _seed_unpersisted_then_close(store)
    en = store.recent_enactments(limit=1)[0]
    sub = _substrate_referencing(name, "mark")
    assert len(ie.run_enactment_checks(store, en, substrate=sub)) == 1
    assert ie.run_enactment_checks(store, en, substrate=sub) == []


def test_no_violation_does_not_fire(tmp_path: Path) -> None:
    name = _register_check("test_check_no_violation")
    store = EnactmentStore(tmp_path / "trail.db")
    eid = store.open_enactment("smoother", mode="autonomic")
    store.record_step(
        enactment_id=eid, affordance_id="mark_friction_addressed",
        material_name="smoother_mark_addressed", arguments={}, result={"addressed": 1},
        started_at="t", completed_at="t", duration_ms=1,
    )  # trigger present but no earlier persisted:false
    store.close_enactment(eid)
    en = store.recent_enactments(limit=1)[0]
    assert ie.run_enactment_checks(store, en, substrate=_substrate_referencing(name, "mark")) == []


def test_referenced_check_deduped_across_affordances(tmp_path: Path) -> None:
    name = _register_check("test_check_shared")
    store = EnactmentStore(tmp_path / "trail.db")
    _seed_unpersisted_then_close(store)
    en = store.recent_enactments(limit=1)[0]
    # one check-material, two referencing affordances -> one firing
    firings = ie.run_enactment_checks(store, en, substrate=_substrate_referencing(name, "a1", "a2"))
    assert len(firings) == 1


def test_unknown_check_reference_does_not_crash(tmp_path: Path) -> None:
    store = EnactmentStore(tmp_path / "trail.db")
    _seed_unpersisted_then_close(store)
    en = store.recent_enactments(limit=1)[0]
    sub = _substrate_referencing("nope_missing", "a")
    assert ie.run_enactment_checks(store, en, substrate=sub) == []


# --- atomicity: friction + addressed + firing commit as one transaction ----


class _FailOnFiringCursor:
    """A cursor that raises on the invariant_firings INSERT — a stand-in for a
    crash after the Friction insert but before the firing is committed."""

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
                invariant_id="some_check", enactment_id=eid,
                observer_id="system:invariant:some_check", kind="k", content="m",
            )
    finally:
        store._conn = real_conn

    # The Friction insert rolled back with the failed firing: no half-resolved
    # state, so a retry re-fires cleanly and nothing leaks to the Smoother.
    assert store.all_friction() == []
    assert store.invariant_fired("some_check", eid) is False
    assert store.pending_smoother_inbox_count() == 0


def test_write_and_load_enactment_check_material(tmp_path: Path) -> None:
    """A written enactment_check dynamic material loads, registers, and fires."""
    from practice_theory_implementation import substrate_loader, substrate_writer

    name = "check_x_before_t"
    substrate_writer.write_dynamic_material(
        name,
        "rationale",  # description
        {},  # input_schema
        {
            "kind": "enactment_check", "trigger": "t", "friction_kind": "k", "message": "m",
            "forbid_when": {"not": {"step_exists": {"material_name": "x"}}},
        },
        root=tmp_path,
    )
    errors: list[str] = []
    mats = substrate_loader._load_dynamic_materials(tmp_path, errors, {})
    assert errors == [] and name in mats
    fn = registry.resolve(name)  # the loader registered the callable
    assert fn([_step(1, "t", "")]) is not None  # trigger present, no earlier x -> violation
