"""pm_amend_affordance wires check-material references and preserves governance.

This is the check-as-material replacement for author_invariant: a determinable
check is authored as a material, then referenced from the affordance it governs
via amend_affordance. The amend must validate the reference resolves and must
never silently drop existing check_materials / transitional preconditions.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from practice_theory_implementation.materials import practice_management as pm
from practice_theory_implementation.types import Affordance, Material, Substrate


@pytest.fixture
def configured(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Substrate:
    monkeypatch.setenv("PRACTICE_SUBSTRATE_DIR", str(tmp_path))
    s = Substrate()
    s.materials["check_x"] = Material(name="check_x", description="", input_schema={})
    s.materials["act"] = Material(name="act", description="", input_schema={})
    s.affordances["aff"] = Affordance(
        id="aff", name="Aff", description="d", materials=("act",)
    )
    pm.configure(
        substrate=s, bundle_catalog={}, register_material_function=lambda *a, **k: None
    )
    return s


def test_amend_sets_check_material_reference(configured: Substrate, tmp_path: Path) -> None:
    r = pm.pm_amend_affordance("aff", check_materials=["check_x"])
    assert "amended" in r
    assert configured.affordances["aff"].check_materials == ("check_x",)
    assert (tmp_path / "affordances" / "aff.md").is_file()


def test_amend_rejects_unknown_check_material(configured: Substrate) -> None:
    r = pm.pm_amend_affordance("aff", check_materials=["nope"])
    assert "error" in r and "check-materials not in substrate" in r["error"]


def test_amend_preserves_existing_check_materials(configured: Substrate) -> None:
    configured.affordances["aff"] = Affordance(
        id="aff", name="Aff", description="d", materials=("act",), check_materials=("check_x",),
    )
    pm.pm_amend_affordance("aff", description="new desc")  # amend an unrelated field
    a = configured.affordances["aff"]
    assert a.description == "new desc"
    assert a.check_materials == ("check_x",)  # preserved, not wiped
