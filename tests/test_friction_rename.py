"""The Smoother condenses the Judge's provisional Friction names.

The Judge names a Friction to give it form; the Smoother considers that name and
may rename it toward the canonical vocabulary as part of smoothing — the
condensation that keeps the kind-space from sprawling into one-offs.
"""

from __future__ import annotations

from pathlib import Path

from practice_theory_implementation.materials import smoother
from practice_theory_implementation.trail import EnactmentStore


def _friction(store: EnactmentStore, kind: str) -> int:
    return store.record_friction(
        observing_enactment_id="judge",
        target_enactment_id="e",
        kind=kind,
        content="observed",
    )


def test_friction_kinds_vocabulary(tmp_path: Path) -> None:
    store = EnactmentStore(tmp_path / "trail.db")
    _friction(store, "rule_neglect")
    _friction(store, "rule_neglect")
    _friction(store, "weird_one_off")
    vocab = store.friction_kinds()
    assert vocab[0] == {"kind": "rule_neglect", "count": 2}  # most common first
    assert {"kind": "weird_one_off", "count": 1} in vocab


def test_rename_condenses_and_preserves_old(tmp_path: Path) -> None:
    store = EnactmentStore(tmp_path / "trail.db")
    fid = _friction(store, "weird_one_off")
    _friction(store, "rule_neglect")

    old = store.rename_friction(fid, "rule_neglect", content="condensed wording")
    assert old == "weird_one_off"
    # the kind-space condensed: the one-off folded into the canonical kind
    assert store.friction_kinds() == [{"kind": "rule_neglect", "count": 2}]
    renamed = next(f for f in store.all_friction() if f.id == fid)
    assert renamed.kind == "rule_neglect"
    assert renamed.content == "condensed wording"


def test_rename_missing_returns_none(tmp_path: Path) -> None:
    store = EnactmentStore(tmp_path / "trail.db")
    assert store.rename_friction(424242, "x") is None


def test_smoother_rename_material(tmp_path: Path) -> None:
    store = EnactmentStore(tmp_path / "trail.db")
    eid = store.open_enactment("smoother", mode="autonomic")
    fid = _friction(store, "provisional_name")
    smoother.configure(trail=store, active_enactment_id_getter=lambda: eid)

    kinds = smoother.smoother_read_friction_kinds()
    assert {"kind": "provisional_name", "count": 1} in kinds

    result = smoother.smoother_rename_friction(fid, "rule_neglect")
    assert result == {"renamed": fid, "from": "provisional_name", "to": "rule_neglect"}
    assert next(f for f in store.all_friction() if f.id == fid).kind == "rule_neglect"


def test_smoother_rename_requires_active_enactment(tmp_path: Path) -> None:
    store = EnactmentStore(tmp_path / "trail.db")
    fid = _friction(store, "k")
    smoother.configure(trail=store, active_enactment_id_getter=lambda: None)
    assert "error" in smoother.smoother_rename_friction(fid, "x")
