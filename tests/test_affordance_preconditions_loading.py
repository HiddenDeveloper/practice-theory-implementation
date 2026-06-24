"""Affordance inline `preconditions` parsing (phase 1).

Phase 1 of dissolving the free-floating `invariants` pool into affordance-owned
checks (docs/plans/invariants-as-affordance-material-checks.md). An affordance
may now carry its determinable usage contracts inline. The engine does not yet
consume them (phase 2) — this covers loader parsing + graceful skips only.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

from practice_theory_implementation import substrate_loader


def _write_affordance(root: Path, stem: str, frontmatter: str, body: str = "Body.") -> None:
    d = root / "affordances"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{stem}.md").write_text(f"---\n{frontmatter}\n---\n{body}\n", encoding="utf-8")


def _load(root: Path) -> tuple[dict, list[str]]:
    errors: list[str] = []
    affs = substrate_loader._load_affordances(root, errors)
    return affs, errors


def test_affordance_with_no_preconditions_is_empty_tuple(tmp_path: Path) -> None:
    _write_affordance(
        tmp_path,
        "recent_activity",
        textwrap.dedent("""
            id: recent_activity
            name: Recent activity
            materials:
            - garmin_list_activities
        """).strip(),
    )
    affs, errors = _load(tmp_path)
    assert errors == []
    assert affs["recent_activity"].preconditions == ()


def test_valid_precondition_parses_into_check(tmp_path: Path) -> None:
    _write_affordance(
        tmp_path,
        "activity_detail",
        textwrap.dedent("""
            id: activity_detail
            name: Activity detail
            materials:
            - garmin_list_activities
            - garmin_get_activity
            preconditions:
            - id: requires_prior_list
              name: List before detail
              trigger: garmin_get_activity
              friction_kind: quality_affordance_coverage_gap
              message: detail reached before listing
              forbid_when:
                not:
                  step_exists:
                    material_name: garmin_list_activities
        """).strip(),
    )
    affs, errors = _load(tmp_path)
    assert errors == []
    checks = affs["activity_detail"].preconditions
    assert len(checks) == 1
    c = checks[0]
    assert c.id == "requires_prior_list"
    assert c.trigger == "garmin_get_activity"
    assert c.friction_kind == "quality_affordance_coverage_gap"
    assert c.status == "active" and c.mode == "detect"
    assert c.forbid_when == {
        "not": {"step_exists": {"material_name": "garmin_list_activities"}}
    }


def test_malformed_predicate_is_skipped_gracefully(tmp_path: Path) -> None:
    _write_affordance(
        tmp_path,
        "bad",
        textwrap.dedent("""
            id: bad
            name: Bad
            materials: []
            preconditions:
            - id: broken
              trigger: m
              friction_kind: k
              forbid_when:
                step_exists: not-a-mapping
        """).strip(),
    )
    affs, errors = _load(tmp_path)
    assert affs["bad"].preconditions == ()  # bad check dropped, affordance still loads
    assert any("broken" in e for e in errors)


def test_missing_id_and_duplicate_id_are_recorded(tmp_path: Path) -> None:
    _write_affordance(
        tmp_path,
        "dup",
        textwrap.dedent("""
            id: dup
            name: Dup
            materials: []
            preconditions:
            - trigger: m
              friction_kind: k
              forbid_when:
                arg_present: x
            - id: c1
              trigger: m
              friction_kind: k
              forbid_when:
                arg_present: x
            - id: c1
              trigger: m
              friction_kind: k
              forbid_when:
                arg_present: x
        """).strip(),
    )
    affs, errors = _load(tmp_path)
    assert [c.id for c in affs["dup"].preconditions] == ["c1"]  # one valid; others dropped
    assert any("missing a string id" in e for e in errors)
    assert any("duplicate precondition id" in e for e in errors)


def test_tombstoned_check_is_loaded(tmp_path: Path) -> None:
    _write_affordance(
        tmp_path,
        "ts",
        textwrap.dedent("""
            id: ts
            name: Ts
            materials: []
            preconditions:
            - id: retired
              trigger: m
              friction_kind: k
              status: tombstoned
              forbid_when:
                arg_present: x
        """).strip(),
    )
    affs, errors = _load(tmp_path)
    assert errors == []
    assert affs["ts"].preconditions[0].status == "tombstoned"


def test_write_affordance_preconditions_round_trips(tmp_path: Path) -> None:
    """write_affordance emits preconditions that _load_affordances reads back equal."""
    from practice_theory_implementation import substrate_writer
    from practice_theory_implementation.types import Affordance, Check

    check = Check(
        id="requires_x_before_t",
        name="requires x before t",
        trigger="t",
        friction_kind="quality_affordance_coverage",
        message="t reached before x",
        forbid_when={"not": {"step_exists": {"material_name": "x"}}},
    )
    aff = Affordance(
        id="a1", name="A1", description="body prose", materials=("t", "x"),
        preconditions=(check,),
    )
    substrate_writer.write_affordance(aff, root=tmp_path)

    affs, errors = _load(tmp_path)
    assert errors == []
    assert affs["a1"].preconditions == (check,)  # frozen-dataclass equality, lossless
