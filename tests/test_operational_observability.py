from __future__ import annotations

from pathlib import Path

from practice_theory_implementation.materials import operational_observability
from practice_theory_implementation.trail import EnactmentStore, UsageRecord


def _store(tmp_path: Path, monkeypatch) -> EnactmentStore:
    path = tmp_path / "trail.db"
    monkeypatch.setenv("PRACTICE_TRAIL_PATH", str(path))
    return EnactmentStore(path)


def test_read_system_observability_reports_counts_timing_and_usage(
    tmp_path: Path, monkeypatch
) -> None:
    store = _store(tmp_path, monkeypatch)
    try:
        eid = store.open_enactment("judge", mode="autonomic")
        store.record_step(
            enactment_id=eid,
            affordance_id="examine_recent_enactment",
            material_name="judge_read_enactment_history",
            arguments={"enactment_id": eid},
            result={"id": eid},
            started_at="2026-01-01T00:00:00+00:00",
            completed_at="2026-01-01T00:00:01+00:00",
            duration_ms=1000,
        )
        store.close_enactment(eid)
        store.route_autonomic_history_to_judge_inbox(since=None)
        store.record_usage(
            eid,
            UsageRecord(
                provider="codex",
                model="gpt-5.5",
                input_tokens=100,
                output_tokens=5,
                cache_read_tokens=50,
                num_turns=1,
            ),
            dispatch_ms=1234,
        )
    finally:
        store.close()

    result = operational_observability.read_system_observability(limit=3)

    assert result["trail"]["counts"]["pending_judge_inbox"] == 1
    assert result["trail"]["started_at"]["pending_judge_inbox"] is not None
    assert result["trail"]["recent_usage"][0]["model"] == "gpt-5.5"
    assert result["trail"]["recent_usage"][0]["dispatch_ms"] == 1234


def test_read_autonomic_maintenance_context_reports_smoother_purpose(
    tmp_path: Path, monkeypatch
) -> None:
    store = _store(tmp_path, monkeypatch)
    try:
        target_id = store.open_enactment("judge", mode="autonomic")
        store.close_enactment(target_id)
        smoother_id = store.open_enactment("smoother", mode="autonomic")
        friction_id = store.record_friction(
            observing_enactment_id=target_id,
            target_enactment_id=target_id,
            kind="basis_visibility_gap",
            content="Make exact Friction content visible before closure.",
            observation_data={"basis": "missing targeted read"},
        )
        store.record_step(
            enactment_id=smoother_id,
            affordance_id="read_pending_friction",
            material_name="smoother_read_pending_friction",
            arguments={"friction_id": friction_id},
            result={"id": friction_id},
            started_at="2026-01-01T00:00:00+00:00",
            completed_at="2026-01-01T00:00:01+00:00",
            duration_ms=1000,
        )
        store.record_step(
            enactment_id=smoother_id,
            affordance_id="amend_pool_element",
            material_name="pm_amend_element",
            arguments={"pool": "rules", "id": "rule_smoother_mark_when_done"},
            result={"amended": {"pool": "rules", "id": "rule_smoother_mark_when_done"}},
            started_at="2026-01-01T00:00:01+00:00",
            completed_at="2026-01-01T00:00:02+00:00",
            duration_ms=1000,
        )
        assert store.mark_friction_addressed(friction_id, smoother_id)
        store.close_enactment(smoother_id)
    finally:
        store.close()

    result = operational_observability.read_autonomic_maintenance_context(limit=5)
    item = result["smoother_enactments"][0]

    assert item["enactment_id"] == smoother_id
    assert item["friction"]["id"] == friction_id
    assert item["closure_basis_visible"] is True
    assert "rules:rule_smoother_mark_when_done" in item["changed_substrate_ids"]
