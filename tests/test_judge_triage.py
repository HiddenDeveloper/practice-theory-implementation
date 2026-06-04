"""Deterministic triage gates the LLM Judge.

The reflective loop used to route every closed enactment to the Judge LLM —
expensive, and (feeding the Judge its own output) self-amplifying. Triage runs
a deterministic 3-way classification first: CLEAN → no-finding (no LLM),
FRICTION → emit deterministically (no LLM, flows to the Smoother), AMBIGUOUS →
the only path that creates a judge_inbox row. These guard that split and its
idempotency.
"""

from __future__ import annotations

from pathlib import Path

from practice_theory_implementation import judge_triage as jt
from practice_theory_implementation.trail import EnactmentStore


def _seed(
    store: EnactmentStore,
    bundle: str,
    *,
    mode: str = "autonomic",
    steps: int = 1,
    error: bool = False,
) -> str:
    eid = store.open_enactment(bundle, mode=mode)
    for _ in range(steps):
        store.record_step(
            enactment_id=eid,
            affordance_id="a",
            material_name="m",
            arguments={"x": 1},
            result={"error": "boom"} if error else {"ok": True},
            started_at="2026-06-04T00:00:00+00:00",
            completed_at="2026-06-04T00:00:01+00:00",
            duration_ms=5,
        )
    store.close_enactment(eid)
    return eid


def test_clean_enactment_records_no_finding_no_inbox(tmp_path: Path) -> None:
    store = EnactmentStore(tmp_path / "trail.db")
    _seed(store, "judge", steps=2)

    summary = jt.triage_and_route(store, mode="autonomic")

    assert summary.clean == 1
    assert summary.ambiguous == 0 and summary.friction == 0
    assert store.pending_judge_inbox_count() == 0
    assert store.all_friction() == []


def test_unresolved_bundle_emits_friction_no_inbox(tmp_path: Path) -> None:
    store = EnactmentStore(tmp_path / "trail.db")
    missing = _seed(store, "user_focused_engagement")

    summary = jt.triage_and_route(store, mode="autonomic")

    assert summary.friction == 1
    assert store.pending_judge_inbox_count() == 0
    friction = store.all_friction()
    assert len(friction) == 1
    assert friction[0].kind == "missing_bundle"
    assert friction[0].target_enactment_id == missing


def test_recorded_step_error_is_ambiguous_and_routed(tmp_path: Path) -> None:
    store = EnactmentStore(tmp_path / "trail.db")
    errored = _seed(store, "smoother", error=True)

    summary = jt.triage_and_route(store, mode="autonomic")

    assert summary.ambiguous == 1
    row = store.next_judge_work(worker_id="t")
    assert row is not None and row.enactment_id == errored


def test_triage_is_idempotent(tmp_path: Path) -> None:
    store = EnactmentStore(tmp_path / "trail.db")
    _seed(store, "judge", steps=2)
    _seed(store, "user_focused_engagement")
    _seed(store, "smoother", error=True)

    first = jt.triage_and_route(store, mode="autonomic")
    assert first.examined == 3
    second = jt.triage_and_route(store, mode="autonomic")
    assert second.examined == 0  # nothing re-decided


def test_mode_scoping(tmp_path: Path) -> None:
    store = EnactmentStore(tmp_path / "trail.db")
    _seed(store, "judge", mode="autonomic", steps=1)
    _seed(store, "continuous_self", mode="somatic", steps=1)

    autonomic = jt.triage_and_route(store, mode="autonomic")
    assert autonomic.examined == 1
    somatic = jt.triage_and_route(store, mode="somatic")
    assert somatic.examined == 1


def test_triage_enactment_precedence_friction_over_ambiguous(tmp_path: Path) -> None:
    # An unresolved bundle that also recorded an error resolves to FRICTION
    # (provable, no LLM) rather than AMBIGUOUS.
    store = EnactmentStore(tmp_path / "trail.db")
    eid = _seed(store, "user_focused_engagement", error=True)
    enactment = store.recent_enactments(limit=1)[0]
    assert enactment.id == eid
    result = jt.triage_enactment(store, enactment)
    assert result.outcome is jt.Outcome.FRICTION
