"""The Smoother's governance of invariants: author, amend, tombstone.

The keystone constraint — deterministic rules are governed substrate the LLM
owns, not frozen Python. These guard that the lifecycle round-trips through
files (dual-write), that a non-evaluable predicate can never be saved, and that
tombstone is a soft-retire (file kept, status flipped).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from practice_theory_implementation.materials import practice_management as pm
from practice_theory_implementation.types import Substrate


@pytest.fixture
def configured(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Substrate:
    """A configured PM bound to a fresh substrate writing under tmp_path."""
    monkeypatch.setenv("PRACTICE_SUBSTRATE_DIR", str(tmp_path))
    substrate = Substrate()
    pm.configure(
        substrate=substrate,
        bundle_catalog={},
        register_material_function=lambda *a, **k: None,
    )
    return substrate


def _create(**over: object) -> dict:
    args: dict = dict(
        id="r1",
        name="Rule one",
        trigger="smoother_mark_addressed",
        friction_kind="k",
        message="m",
        forbid_when={"any_earlier_step_result_contains": '"persisted": false'},
        content="body",
    )
    args.update(over)
    return pm.pm_create_invariant(**args)  # type: ignore[arg-type]


def test_author_persists_and_registers(configured: Substrate, tmp_path: Path) -> None:
    r = _create()
    assert "created" in r
    assert (tmp_path / "invariants" / "r1.md").is_file()
    assert "r1" in configured.invariants
    assert configured.invariants["r1"].status == "active"


def test_author_rejects_non_evaluable_predicate(
    configured: Substrate, tmp_path: Path
) -> None:
    r = _create(id="bad", forbid_when={"not_a_real_op": 1})
    assert "error" in r and "predicate" in r["error"]
    assert "bad" not in configured.invariants
    assert not (tmp_path / "invariants" / "bad.md").is_file()


def test_author_rejects_duplicate(configured: Substrate) -> None:
    _create()
    assert "error" in _create()


def test_amend_preserves_unset_and_revalidates(configured: Substrate) -> None:
    _create()
    r = pm.pm_amend_invariant(id="r1", message="sharper")
    assert "amended" in r
    inv = configured.invariants["r1"]
    assert inv.message == "sharper"
    assert inv.trigger == "smoother_mark_addressed"  # preserved
    # a bad predicate on amend is rejected, leaving the rule unchanged
    bad = pm.pm_amend_invariant(id="r1", forbid_when={"nope": 1})
    assert "error" in bad
    assert configured.invariants["r1"].forbid_when == {
        "any_earlier_step_result_contains": '"persisted": false'
    }


def test_tombstone_is_soft_retire(configured: Substrate, tmp_path: Path) -> None:
    _create()
    r = pm.pm_tombstone_invariant(id="r1", reason="superseded")
    assert "tombstoned" in r
    inv = configured.invariants["r1"]
    assert inv.status == "tombstoned"
    assert inv.tombstone_reason == "superseded"
    assert inv.tombstoned_at is not None
    assert (tmp_path / "invariants" / "r1.md").is_file()  # file kept, not deleted
    # double-tombstone is rejected
    assert "error" in pm.pm_tombstone_invariant(id="r1", reason="again")


def test_amend_and_tombstone_missing(configured: Substrate) -> None:
    assert "error" in pm.pm_amend_invariant(id="ghost")
    assert "error" in pm.pm_tombstone_invariant(id="ghost", reason="x")
