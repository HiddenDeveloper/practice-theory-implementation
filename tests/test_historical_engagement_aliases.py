from __future__ import annotations

from pathlib import Path

import pytest

from practice_theory_implementation.material_surfaces import MATERIAL_SURFACES
from practice_theory_implementation.materials import practice_management
from practice_theory_implementation.substrate_loader import load_substrate
from practice_theory_implementation.types import (
    Affordance,
    Bundle,
    Material,
    PoolElement,
    Substrate,
)


def _write_bundle(path: Path, *, bundle_id: str, engagement: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "---",
                f"id: {bundle_id}",
                f"name: {bundle_id}",
                "mode: somatic",
                f"engagement: {str(engagement).lower()}",
                "teleo_affective_ids:",
                "- te",
                "understanding_ids:",
                "- und",
                "rules_ids:",
                "- rule",
                "affordance_ids:",
                "- aff",
                "---",
                "bundle body",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_pool(path: Path, *, entity_id: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"---\nid: {entity_id}\nname: {entity_id}\n---\nbody\n",
        encoding="utf-8",
    )


def _write_affordance(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "---\nid: aff\nname: aff\nmaterials: []\n---\naffordance body\n",
        encoding="utf-8",
    )


def test_loader_rejects_historical_engagement_bundle_id(tmp_path: Path) -> None:
    _write_pool(tmp_path / "teleo_affective" / "te.md", entity_id="te")
    _write_pool(tmp_path / "understanding" / "und.md", entity_id="und")
    _write_pool(tmp_path / "rules" / "rule.md", entity_id="rule")
    _write_affordance(tmp_path / "affordances" / "aff.md")
    _write_bundle(
        tmp_path / "bundles" / "continuous_self.md",
        bundle_id="continuous_self",
        engagement=True,
    )
    _write_bundle(
        tmp_path / "bundles" / "user_focused_engagement.md",
        bundle_id="user_focused_engagement",
    )

    loaded = load_substrate(root=tmp_path, material_surfaces=MATERIAL_SURFACES)

    assert "user_focused_engagement" not in loaded.bundles
    assert any(
        "historical engagement id is reserved" in error for error in loaded.errors
    )


def test_practice_management_refuses_to_recreate_historical_engagement_bundle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PRACTICE_SUBSTRATE_DIR", str(tmp_path))
    substrate = Substrate(
        teleo_affective={"te": PoolElement(id="te", name="te", content="body")},
        understanding={"und": PoolElement(id="und", name="und", content="body")},
        rules={"rule": PoolElement(id="rule", name="rule", content="body")},
        affordances={
            "aff": Affordance(
                id="aff", name="aff", description="body", materials=("mat",)
            )
        },
        materials={"mat": Material(name="mat", description="body", input_schema={})},
    )
    catalog: dict[str, Bundle] = {}
    practice_management.configure(
        substrate=substrate,
        bundle_catalog=catalog,
        register_material_function=lambda _name, _implementation: None,
    )

    result = practice_management.pm_create_bundle(
        id="user_focused_engagement",
        name="User Focused Engagement",
        description="legacy alias",
        teleo_affective_ids=["te"],
        understanding_ids=["und"],
        rules_ids=["rule"],
        affordance_ids=["aff"],
    )

    assert "reserved as a historical engagement id" in result["error"]
    assert "user_focused_engagement" not in catalog
    assert not (tmp_path / "bundles" / "user_focused_engagement.md").exists()
