"""Tests for the Phase-2 practice-evaluation routing (deterministic parts).

The Judge-dispatch loop itself needs a live adapter and is exercised in the
autonomic runner; here we test the pure, deterministic pieces: the set-diff
newness check, the objective-coverage check, idempotent Friction emission, and
the Judge brief composition.
"""

from __future__ import annotations

import json

import pytest

from practice_theory_implementation import practice_evaluation_routing as routing
from practice_theory_implementation.substrate_loader import LoadedSubstrate
from practice_theory_implementation.trail import TRAIL_PATH_ENV, EnactmentStore
from practice_theory_implementation.types import Bundle, EvaluationSpec, Substrate


def _bundle(bid: str, *, evaluation_ids=(), teleo=(), mode="somatic") -> Bundle:
    return Bundle(
        id=bid,
        name=bid,
        description="",
        teleo_affective_ids=tuple(teleo),
        understanding_ids=(),
        rules_ids=(),
        affordance_ids=(),
        evaluation_ids=tuple(evaluation_ids),
        mode=mode,
    )


def _spec(sid: str, practice_id: str, *, objective_ref=None, signals=()) -> EvaluationSpec:
    return EvaluationSpec(
        id=sid,
        name=sid,
        practice_id=practice_id,
        objective_ref=objective_ref,
        signals=tuple(signals),
    )


def _loaded(bundles, specs) -> LoadedSubstrate:
    return LoadedSubstrate(
        substrate=Substrate(evaluations={s.id: s for s in specs}),
        bundles={b.id: b for b in bundles},
        engagement_bundle=None,
        errors=[],
    )


@pytest.fixture
def store(tmp_path, monkeypatch: pytest.MonkeyPatch) -> EnactmentStore:
    path = tmp_path / "trail.db"
    monkeypatch.setenv(TRAIL_PATH_ENV, str(path))
    return EnactmentStore(path)


def test_unevaluated_excludes_specced_and_autonomic() -> None:
    spec = _spec("eval_a", "a", objective_ref="te_a")
    loaded = _loaded(
        [
            _bundle("a", evaluation_ids=["eval_a"], teleo=["te_a"]),
            _bundle("b"),  # somatic, no spec -> unevaluated
            _bundle("auto", mode="autonomic"),  # not in scope
        ],
        [spec],
    )
    assert routing.unevaluated_somatic_practices(loaded) == ["b"]


def test_unevaluated_accepts_spec_by_practice_id_fallback() -> None:
    # spec not referenced by evaluation_ids but names the practice directly
    spec = _spec("eval_a", "a", objective_ref="te_a")
    loaded = _loaded([_bundle("a", teleo=["te_a"])], [spec])
    assert routing.unevaluated_somatic_practices(loaded) == []


def test_objective_uncovered_detects_missing_and_mismatched() -> None:
    loaded = _loaded(
        [
            _bundle("good", evaluation_ids=["eval_good"], teleo=["te_good"]),
            _bundle("noref", evaluation_ids=["eval_noref"], teleo=["te_noref"]),
            _bundle("mismatch", evaluation_ids=["eval_mis"], teleo=["te_mis"]),
        ],
        [
            _spec("eval_good", "good", objective_ref="te_good"),
            _spec("eval_noref", "noref", objective_ref=None),
            _spec("eval_mis", "mismatch", objective_ref="te_other"),
        ],
    )
    flagged = {(b, s) for b, s, _ in routing.objective_uncovered(loaded)}
    assert flagged == {("noref", "eval_noref"), ("mismatch", "eval_mis")}


def test_route_governance_emits_and_is_idempotent(store: EnactmentStore) -> None:
    loaded = _loaded(
        [
            _bundle("b"),  # missing evaluation
            _bundle("mismatch", evaluation_ids=["eval_mis"], teleo=["te_mis"]),
        ],
        [_spec("eval_mis", "mismatch", objective_ref="te_other")],
    )
    first = routing.route_evaluation_governance(store, loaded)
    assert first.missing_evaluation == 1
    assert first.objective_uncovered == 1

    pending = store.pending_friction(limit=50)
    kinds = {fr.kind for fr in pending}
    assert routing.MISSING_EVALUATION_KIND in kinds
    assert routing.OBJECTIVE_UNCOVERED_KIND in kinds
    # observation_data carries the practice_id for downstream routing
    missing = next(fr for fr in pending if fr.kind == routing.MISSING_EVALUATION_KIND)
    assert json.loads(missing.observation_data_json)["practice_id"] == "b"

    # a second pass raises nothing new — idempotent
    second = routing.route_evaluation_governance(store, loaded)
    assert second.missing_evaluation == 0
    assert second.objective_uncovered == 0
    assert len(store.pending_friction(limit=50)) == len(pending)


def test_practices_with_concerns_runs_engine(store: EnactmentStore) -> None:
    spec = _spec(
        "eval_demo",
        "demo",
        objective_ref="te_demo",
        signals=[
            {
                "id": "outcomes",
                "kind": "outcome_presence",
                "outcome_materials": ["submit_order"],
                "max_consecutive_without": 2,
            }
        ],
    )
    loaded = _loaded([_bundle("demo", evaluation_ids=["eval_demo"], teleo=["te_demo"])], [spec])
    for _ in range(3):
        eid = store.open_enactment("demo", mode="somatic")
        store.record_step(
            enactment_id=eid,
            affordance_id="aff",
            material_name="decide",
            arguments={},
            result="hold",
            started_at="2026-06-19T00:00:00+00:00",
            completed_at="2026-06-19T00:00:01+00:00",
            duration_ms=1000,
        )
        store.close_enactment(eid)

    concerns = routing.practices_with_concerns(loaded, store)
    assert len(concerns) == 1
    assert concerns[0]["practice_id"] == "demo"
    assert concerns[0]["concern_count"] >= 1


def test_compose_concern_brief_includes_concerns_only() -> None:
    result = {
        "practice_id": "demo",
        "findings": [
            {"signal_id": "s1", "kind": "outcome_presence", "status": "concern",
             "detail": "no orders", "evidence": {"x": 1}},
            {"signal_id": "s2", "kind": "shape_repetition", "status": "pass",
             "detail": "fine", "evidence": {}},
        ],
    }
    brief = routing.compose_concern_brief(result)
    assert "demo" in brief
    assert "s1" in brief
    assert "emit_friction" in brief
    assert "s2" not in brief  # pass findings are not listed


# --- window watermark (Judge re-review suppression) ------------------------


def _single_spec_result(enactment_ids, concern_signals):
    return {
        "practice_id": "demo",
        "spec_present": True,
        "evaluated_enactment_ids": list(enactment_ids),
        "findings": [
            {"signal_id": s, "kind": "affordance_coverage", "status": "concern"}
            for s in concern_signals
        ],
    }


def test_window_signature_stable_when_window_and_concerns_unchanged() -> None:
    a = _single_spec_result(["e3", "e2", "e1"], ["s1"])
    b = _single_spec_result(["e1", "e2", "e3"], ["s1"])  # same set, different order
    assert routing.evaluation_window_signature(a) == routing.evaluation_window_signature(b)


def test_window_signature_changes_when_a_new_enactment_appears() -> None:
    before = _single_spec_result(["e1", "e2", "e3"], ["s1"])
    after = _single_spec_result(["e4", "e1", "e2"], ["s1"])  # window advanced
    assert routing.evaluation_window_signature(before) != routing.evaluation_window_signature(after)


def test_window_signature_changes_when_a_new_concern_trips() -> None:
    before = _single_spec_result(["e1", "e2"], ["s1"])
    after = _single_spec_result(["e1", "e2"], ["s1", "s2"])  # same window, new concern
    assert routing.evaluation_window_signature(before) != routing.evaluation_window_signature(after)


def test_window_signature_ignores_pass_findings_and_rewording() -> None:
    # Identical window + concerns, but extra `pass` findings / detail churn must
    # not change the signature (a Smoother re-wording on a frozen window).
    base = _single_spec_result(["e1", "e2"], ["s1"])
    reworded = _single_spec_result(["e1", "e2"], ["s1"])
    reworded["findings"].append(
        {"signal_id": "s9", "kind": "shape_repetition", "status": "pass"}
    )
    reworded["detail"] = "freshly re-worded narrative that should not matter"
    assert routing.evaluation_window_signature(
        base
    ) == routing.evaluation_window_signature(reworded)


def test_window_signature_handles_multi_spec_results() -> None:
    multi = {
        "practice_id": "demo",
        "spec_present": True,
        "results": [
            {"evaluated_enactment_ids": ["e1", "e2"],
             "findings": [{"signal_id": "s1", "status": "concern"}]},
            {"evaluated_enactment_ids": ["e2", "e3"],
             "findings": [{"signal_id": "s2", "status": "pass"}]},
        ],
        "concern_count": 1,
    }
    sig = routing.evaluation_window_signature(multi)
    assert "e1" in sig and "e3" in sig and "s1" in sig
    assert "s2" not in sig.split(";concerns:")[1]  # pass finding not a concern
