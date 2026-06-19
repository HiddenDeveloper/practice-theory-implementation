"""Phase-3 authoring: eval-spec create/amend + the bundle evaluation_ids round-trip.

Guards that the pooled evaluation-authoring capability persists through files
(dual-write) and that amending a bundle never silently drops its evaluation
layer — the regression the writer/PM round-trip fix closes.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from practice_theory_implementation.material_surfaces import MATERIAL_SURFACES
from practice_theory_implementation.materials import practice_management as pm
from practice_theory_implementation.substrate_loader import (
    load_substrate,
    split_frontmatter,
)
from practice_theory_implementation.types import Substrate


@pytest.fixture
def configured(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Substrate:
    monkeypatch.setenv("PRACTICE_SUBSTRATE_DIR", str(tmp_path))
    substrate = Substrate()
    pm.configure(
        substrate=substrate,
        bundle_catalog={},
        register_material_function=lambda *a, **k: None,
    )
    return substrate


_SIGNALS = [
    {
        "id": "outcomes",
        "kind": "outcome_presence",
        "outcome_materials": ["submit_order"],
        "max_consecutive_without": 6,
    }
]


def test_create_evaluation_persists_and_mirrors(
    configured: Substrate, tmp_path: Path
) -> None:
    r = pm.pm_create_evaluation(
        id="eval_demo",
        name="Demo eval",
        practice_id="demo",
        signals=_SIGNALS,
        objective_ref="te_demo",
    )
    assert "created" in r
    assert (tmp_path / "evaluations" / "eval_demo.md").is_file()
    assert "eval_demo" in configured.evaluations
    spec = configured.evaluations["eval_demo"]
    assert spec.practice_id == "demo"
    assert spec.objective_ref == "te_demo"
    assert spec.signals[0]["kind"] == "outcome_presence"


def test_create_evaluation_rejects_duplicate_and_bad_signals(
    configured: Substrate,
) -> None:
    pm.pm_create_evaluation(
        id="eval_demo", name="d", practice_id="demo", signals=_SIGNALS
    )
    dup = pm.pm_create_evaluation(
        id="eval_demo", name="d", practice_id="demo", signals=_SIGNALS
    )
    assert "error" in dup and "already exists" in dup["error"]
    bad = pm.pm_create_evaluation(
        id="eval_bad", name="d", practice_id="demo", signals="not a list"  # type: ignore[arg-type]
    )
    assert "error" in bad


def test_amend_evaluation_preserves_omitted_fields(configured: Substrate) -> None:
    pm.pm_create_evaluation(
        id="eval_demo",
        name="Demo eval",
        practice_id="demo",
        signals=_SIGNALS,
        objective_ref="te_demo",
        window=8,
    )
    r = pm.pm_amend_evaluation(id="eval_demo", window=4)
    assert "amended" in r
    spec = configured.evaluations["eval_demo"]
    assert spec.window == 4
    # untouched fields are preserved
    assert spec.objective_ref == "te_demo"
    assert spec.practice_id == "demo"
    assert spec.signals[0]["kind"] == "outcome_presence"


def test_amend_bundle_preserves_evaluation_ids(
    configured: Substrate, tmp_path: Path
) -> None:
    from practice_theory_implementation.types import PoolElement

    configured.teleo_affective["te_demo"] = PoolElement(
        id="te_demo", name="te", content="x"
    )
    pm.pm_create_evaluation(
        id="eval_demo",
        name="d",
        practice_id="demo",
        signals=_SIGNALS,
        objective_ref="te_demo",
    )
    created = pm.pm_create_bundle(
        id="demo",
        name="Demo",
        description="d",
        teleo_affective_ids=["te_demo"],
        understanding_ids=[],
        rules_ids=[],
        affordance_ids=[],
        evaluation_ids=["eval_demo"],
    )
    assert "created" in created
    # the written file carries the evaluation layer
    fm, _ = split_frontmatter(
        (tmp_path / "bundles" / "demo.md").read_text(encoding="utf-8"),
        source="demo.md",
    )
    assert fm["evaluation_ids"] == ["eval_demo"]

    # an amend that omits evaluation_ids must NOT drop the link
    amended = pm.pm_amend_bundle(id="demo", name="Demo renamed")
    assert "amended" in amended
    fm2, _ = split_frontmatter(
        (tmp_path / "bundles" / "demo.md").read_text(encoding="utf-8"),
        source="demo.md",
    )
    assert fm2["evaluation_ids"] == ["eval_demo"]


def test_both_authoring_practices_compose_pooled_capability() -> None:
    loaded = load_substrate(material_surfaces=MATERIAL_SURFACES)
    for bid in ("practice_management", "smoother"):
        bundle = loaded.bundles[bid]
        assert "und_substrate_authoring" in bundle.understanding_ids
        assert "author_evaluation" in bundle.affordance_ids
        assert "amend_evaluation" in bundle.affordance_ids


def test_create_evaluation_rejects_malformed_signals(configured: Substrate) -> None:
    r = pm.pm_create_evaluation(
        id="eval_bad",
        name="x",
        practice_id="demo",
        signals=[{"id": "s", "kind": "outcome_presence"}],  # missing required list
    )
    assert "error" in r and "invalid signals" in r["error"]
    assert "eval_bad" not in configured.evaluations


def test_coverage_gate_blocks_uncovered_wiring(
    configured: Substrate, monkeypatch: pytest.MonkeyPatch
) -> None:
    from practice_theory_implementation.types import PoolElement

    configured.teleo_affective["te_demo"] = PoolElement(
        id="te_demo", name="te", content="x"
    )
    configured.teleo_affective["te_other"] = PoolElement(
        id="te_other", name="o", content="x"
    )
    pm.pm_create_evaluation(
        id="eval_demo",
        name="d",
        practice_id="demo",
        signals=_SIGNALS,
        objective_ref="te_demo",
    )
    # wiring the spec into a bundle whose objective it does NOT cover is blocked
    blocked = pm.pm_create_bundle(
        id="demo",
        name="Demo",
        description="d",
        teleo_affective_ids=["te_other"],
        understanding_ids=[],
        rules_ids=[],
        affordance_ids=[],
        evaluation_ids=["eval_demo"],
    )
    assert "error" in blocked and "coverage gate" in blocked["error"]
    # wiring into a bundle that DOES carry the objective succeeds
    ok = pm.pm_create_bundle(
        id="demo",
        name="Demo",
        description="d",
        teleo_affective_ids=["te_demo"],
        understanding_ids=[],
        rules_ids=[],
        affordance_ids=[],
        evaluation_ids=["eval_demo"],
    )
    assert "created" in ok


def test_autonomic_config_enables_evaluation_loop(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from practice_theory_implementation import autonomic_runner as ar

    monkeypatch.setenv("PRACTICE_PRACTICE_EVAL_ENABLED", "")
    monkeypatch.setenv("PRACTICE_PRACTICE_EVAL_COOLDOWN_SECONDS", "")
    ar._apply_autonomic_config(
        {"practice_evaluation": {"enabled": True, "cooldown_seconds": 900}}
    )
    assert ar._practice_eval_enabled() is True
    assert ar._practice_eval_cooldown_seconds() == 900.0
