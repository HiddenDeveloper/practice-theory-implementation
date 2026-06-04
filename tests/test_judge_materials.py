from __future__ import annotations

from pathlib import Path

from practice_theory_implementation.materials import judge
from practice_theory_implementation.trail import EnactmentStore
from practice_theory_implementation.types import Substrate


def _store(tmp_path: Path) -> EnactmentStore:
    return EnactmentStore(tmp_path / "trail.db")


def test_list_recent_enactments_filters_bundle_before_limit(tmp_path: Path) -> None:
    store = _store(tmp_path)
    target_id = store.open_enactment("smoother", mode="autonomic")

    for _ in range(10):
        store.open_enactment("judge", mode="autonomic")

    judge.configure(
        trail=store,
        substrate=Substrate(),
        bundle_catalog={},
        observing_enactment_id_getter=lambda: "judge-1",
    )

    result = judge.judge_list_recent_enactments(limit=1, bundle_id="smoother")

    assert [row["id"] for row in result] == [target_id]
