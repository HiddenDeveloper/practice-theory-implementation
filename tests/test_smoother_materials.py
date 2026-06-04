from __future__ import annotations

from pathlib import Path

from practice_theory_implementation.materials import smoother
from practice_theory_implementation.trail import EnactmentStore


def _store(tmp_path: Path) -> EnactmentStore:
    return EnactmentStore(tmp_path / "trail.db")


def test_read_pending_friction_can_narrow_to_exact_id(tmp_path: Path) -> None:
    store = _store(tmp_path)
    first_id = store.record_friction(
        observing_enactment_id="judge-1",
        target_enactment_id="target-1",
        kind="earlier",
        content="first",
    )
    second_id = store.record_friction(
        observing_enactment_id="judge-2",
        target_enactment_id="target-2",
        kind="wanted",
        content="second",
        observation_data={"basis": "visible"},
    )
    smoother.configure(trail=store, active_enactment_id_getter=lambda: "smoother-1")

    result = smoother.smoother_read_pending_friction(
        limit=1, friction_id=second_id
    )

    assert [item["id"] for item in result] == [second_id]
    assert result[0]["kind"] == "wanted"
    assert result[0]["observation_data"] == {"basis": "visible"}
    assert first_id != second_id


def test_read_pending_friction_exact_id_omits_addressed_items(
    tmp_path: Path,
) -> None:
    store = _store(tmp_path)
    friction_id = store.record_friction(
        observing_enactment_id="judge-1",
        target_enactment_id="target-1",
        kind="done",
        content="already addressed",
    )
    smoother.configure(trail=store, active_enactment_id_getter=lambda: "smoother-1")

    assert smoother.smoother_mark_addressed(friction_id)["addressed"] == friction_id

    assert smoother.smoother_read_pending_friction(friction_id=friction_id) == []


def test_mark_addressed_accepts_optional_rationale(tmp_path: Path) -> None:
    store = _store(tmp_path)
    friction_id = store.record_friction(
        observing_enactment_id="judge-1",
        target_enactment_id="target-1",
        kind="no_mutation_basis",
        content="closure needs its basis on the accepted mark",
    )
    smoother.configure(trail=store, active_enactment_id_getter=lambda: "smoother-1")

    result = smoother.smoother_mark_addressed(
        friction_id, rationale="No substrate mutation was appropriate."
    )

    assert result == {
        "addressed": friction_id,
        "by_enactment_id": "smoother-1",
        "rationale": "No substrate mutation was appropriate.",
    }
