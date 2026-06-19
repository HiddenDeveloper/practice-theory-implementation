"""Unit tests for the generic practice-evaluation engine.

Each test builds a synthetic trail for a fictional practice, declares one signal
in an EvaluationSpec, configures the engine against an in-memory catalog, and
asserts the per-signal finding. The engine is generic, so these never mention a
real practice's domain.
"""

from __future__ import annotations

from typing import Any

import pytest

from practice_theory_implementation.materials import practice_evaluation
from practice_theory_implementation.trail import TRAIL_PATH_ENV, EnactmentStore
from practice_theory_implementation.types import Bundle, EvaluationSpec, Substrate

PRACTICE = "demo_practice"


def _add_enactment(trail: EnactmentStore, steps: list[tuple[str, Any]]) -> str:
    """One closed enactment whose steps are (material_name, result) pairs."""
    eid = trail.open_enactment(PRACTICE, mode="somatic")
    for material_name, result in steps:
        trail.record_step(
            enactment_id=eid,
            affordance_id=f"aff_{material_name}",
            material_name=material_name,
            arguments={},
            result=result,
            started_at="2026-06-19T00:00:00+00:00",
            completed_at="2026-06-19T00:00:01+00:00",
            duration_ms=1000,
        )
    trail.close_enactment(eid)
    return eid


def _configure(
    trail: EnactmentStore, signal: dict[str, Any], *, window: int = 8
) -> None:
    spec = EvaluationSpec(
        id="eval_demo",
        name="demo eval",
        practice_id=PRACTICE,
        window=window,
        objective_ref="te_demo",
        signals=(signal,),
    )
    substrate = Substrate(evaluations={"eval_demo": spec})
    bundle = Bundle(
        id=PRACTICE,
        name="Demo",
        description="",
        teleo_affective_ids=(),
        understanding_ids=(),
        rules_ids=(),
        affordance_ids=(),
        evaluation_ids=("eval_demo",),
    )
    practice_evaluation.configure(
        trail=trail, substrate=substrate, bundle_catalog={PRACTICE: bundle}
    )


@pytest.fixture
def trail(tmp_path, monkeypatch: pytest.MonkeyPatch) -> EnactmentStore:
    path = tmp_path / "trail.db"
    monkeypatch.setenv(TRAIL_PATH_ENV, str(path))
    return EnactmentStore(path)


def _finding(result: dict[str, Any]) -> dict[str, Any]:
    assert result["spec_present"] is True
    assert len(result["findings"]) == 1
    return result["findings"][0]


def test_no_spec_returns_newness_signal(trail: EnactmentStore) -> None:
    substrate = Substrate()
    practice_evaluation.configure(
        trail=trail, substrate=substrate, bundle_catalog={}
    )
    result = practice_evaluation.evaluate_quality_for_practice("nonexistent")
    assert result["spec_present"] is False
    assert result["newness_signal"] is True


def test_affordance_coverage_pass_and_concern(trail: EnactmentStore) -> None:
    signal = {
        "id": "reads",
        "kind": "affordance_coverage",
        "required_materials": ["read_state", "read_market"],
    }
    # all passes cover the required reads
    _add_enactment(trail, [("read_state", "ok"), ("read_market", "ok"), ("decide", "hold")])
    _configure(trail, signal)
    assert _finding(practice_evaluation.evaluate_quality_for_practice(PRACTICE))["status"] == "pass"

    # a later pass that skips read_market -> concern, naming the enactment
    missing_eid = _add_enactment(trail, [("read_state", "ok"), ("decide", "hold")])
    finding = _finding(practice_evaluation.evaluate_quality_for_practice(PRACTICE))
    assert finding["status"] == "concern"
    missing = finding["evidence"]["enactments_missing_required"]
    assert any(
        m["enactment_id"] == missing_eid and m["missing"] == ["read_market"]
        for m in missing
    )


def test_outcome_presence_concern_after_threshold(trail: EnactmentStore) -> None:
    signal = {
        "id": "outcomes",
        "kind": "outcome_presence",
        "outcome_materials": ["submit_order"],
        "max_consecutive_without": 3,
    }
    for _ in range(4):
        _add_enactment(trail, [("read_state", "ok"), ("decide", "hold")])
    _configure(trail, signal)
    finding = _finding(practice_evaluation.evaluate_quality_for_practice(PRACTICE))
    assert finding["status"] == "concern"
    assert finding["evidence"]["consecutive_passes_without_outcome"] >= 3

    # an outcome in the most recent pass resets the leading run -> pass
    _add_enactment(trail, [("read_state", "ok"), ("submit_order", "filled")])
    finding = _finding(practice_evaluation.evaluate_quality_for_practice(PRACTICE))
    assert finding["status"] == "pass"
    assert finding["evidence"]["consecutive_passes_without_outcome"] == 0


def test_shape_repetition_concern(trail: EnactmentStore) -> None:
    signal = {"id": "repeat", "kind": "shape_repetition", "max_identical": 3}
    shape = [("read_state", "ok"), ("decide", "hold"), ("report", "done")]
    for _ in range(3):
        _add_enactment(trail, shape)
    _configure(trail, signal)
    finding = _finding(practice_evaluation.evaluate_quality_for_practice(PRACTICE))
    assert finding["status"] == "concern"
    assert finding["evidence"]["identical_leading_run"] == 3

    # a different shape on top breaks the leading run -> pass
    _add_enactment(trail, [("read_state", "ok"), ("submit_order", "filled")])
    finding = _finding(practice_evaluation.evaluate_quality_for_practice(PRACTICE))
    assert finding["status"] == "pass"


def test_recurring_summary_marker_concern(trail: EnactmentStore) -> None:
    signal = {
        "id": "gaps",
        "kind": "recurring_summary_marker",
        "markers": ["measurement gap"],
        "max_consecutive": 3,
    }
    for _ in range(3):
        _add_enactment(trail, [("value", "portfolio value with a measurement gap remaining")])
    _configure(trail, signal)
    finding = _finding(practice_evaluation.evaluate_quality_for_practice(PRACTICE))
    assert finding["status"] == "concern"
    assert finding["evidence"]["consecutive_passes_with_marker"] >= 3


def test_validate_signals_gate() -> None:
    good = [
        {"id": "a", "kind": "affordance_coverage", "required_materials": ["m"]},
        {"id": "b", "kind": "shape_repetition"},  # no required list
    ]
    assert practice_evaluation.validate_signals(good) == []

    unknown = practice_evaluation.validate_signals([{"id": "a", "kind": "nope"}])
    assert unknown and "unknown kind" in unknown[0]

    missing_list = practice_evaluation.validate_signals(
        [{"id": "a", "kind": "outcome_presence"}]
    )
    assert missing_list and "non-empty list" in missing_list[0]

    no_id = practice_evaluation.validate_signals(
        [{"kind": "shape_repetition"}]
    )
    assert no_id and "missing id" in no_id[0]

    assert practice_evaluation.validate_signals("not a list")  # type: ignore[arg-type]


def test_window_override_limits_enactments(trail: EnactmentStore) -> None:
    signal = {"id": "repeat", "kind": "shape_repetition", "max_identical": 3}
    for _ in range(5):
        _add_enactment(trail, [("a", "x")])
    _configure(trail, signal)
    result = practice_evaluation.evaluate_quality_for_practice(PRACTICE, window=2)
    assert result["enactments_evaluated"] == 2
    assert result["window"] == 2
