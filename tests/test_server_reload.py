from __future__ import annotations

import pathlib

import pytest


def test_material_module_discovery_covers_all_on_disk(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """pm_reload_seed_substrate must reload every material module on disk.

    Regression: the reload used a hand-maintained module tuple that omitted
    paper_fund, market_data, operational_observability, status_dashboard and
    others, so an edit to one of those code-owned material bodies stayed stale
    until a full server restart. Discovery is now dynamic; this guards it from
    drifting back to a partial list.
    """
    monkeypatch.setenv("PRACTICE_TRAIL_PATH", str(tmp_path / "trail.db"))
    from practice_theory_implementation import materials as materials_pkg
    from practice_theory_implementation import server

    discovered = {name.rsplit(".", 1)[1] for name in server._material_module_names()}

    materials_dir = pathlib.Path(materials_pkg.__file__).parent
    on_disk = {p.stem for p in materials_dir.glob("*.py") if p.stem != "__init__"}

    assert discovered == on_disk
    for previously_missing in (
        "paper_fund",
        "market_data",
        "operational_observability",
        "status_dashboard",
    ):
        assert previously_missing in discovered
