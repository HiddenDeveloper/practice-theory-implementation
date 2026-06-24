"""Phase 3 migration planner: invariants -> affordance checks (dry-run logic).

Covers the sort + dedup that collapses the sprawl: friction-kind drift merges,
single/multi/zero-owner routing, and check-id uniqueness within an owner.
"""

from __future__ import annotations

from practice_theory_implementation.migrate_invariants_to_checks import plan_migration
from practice_theory_implementation.types import Affordance, Invariant

LIST_BEFORE = {"not": {"step_exists": {"material_name": "garmin_list_activities"}}}


def _inv(id: str, trigger: str, friction_kind: str, forbid_when, status="active") -> Invariant:
    return Invariant(
        id=id,
        name=id,
        trigger=trigger,
        friction_kind=friction_kind,
        message=f"msg {id}",
        forbid_when=forbid_when,
        content="",
        status=status,
    )


def _aff(id: str, *materials: str) -> Affordance:
    return Affordance(id=id, name=id, description="", materials=tuple(materials))


def test_friction_kind_drift_collapses_to_one_check() -> None:
    trig = "garmin_get_daily_summary"
    invs = {
        "a": _inv("a", trig, "quality_affordance_coverage", LIST_BEFORE),
        "b": _inv("b", trig, "practice_quality_affordance_coverage", LIST_BEFORE),
        "c": _inv("c", trig, "quality_affordance_coverage_gap", LIST_BEFORE),
    }
    affs = {"daily_summary": _aff("daily_summary", trig, "garmin_list_activities")}
    plan = plan_migration(invs, affs)
    assert len(plan.ready) == 1
    c = plan.ready[0]
    assert c.source_invariant_ids == ("a", "b", "c")  # all three merged
    assert set(c.merged_friction_kinds) == {
        "quality_affordance_coverage",
        "practice_quality_affordance_coverage",
        "quality_affordance_coverage_gap",
    }
    assert c.check_id == "requires_garmin_list_activities_before_garmin_get_daily_summary"
    assert c.owner_candidates == ("daily_summary",)


def test_multi_owner_goes_to_needs_review() -> None:
    invs = {"a": _inv("a", "garmin_get_activity", "k", LIST_BEFORE)}
    affs = {
        "activity_detail": _aff("activity_detail", "garmin_get_activity", "garmin_list_activities"),
        "iwt": _aff("iwt", "garmin_get_activity"),
    }
    plan = plan_migration(invs, affs)
    assert plan.ready == ()
    assert len(plan.needs_review) == 1
    assert set(plan.needs_review[0].owner_candidates) == {"activity_detail", "iwt"}


def test_no_owner_is_deferred() -> None:
    invs = {"a": _inv("a", "garmin_daily_summary", "k", LIST_BEFORE)}  # stale alias, not afforded
    affs = {"daily_summary": _aff("daily_summary", "garmin_get_daily_summary")}
    plan = plan_migration(invs, affs)
    assert plan.ready == () and plan.needs_review == ()
    assert [d.invariant_id for d in plan.deferred] == ["a"]


def test_tombstoned_invariants_are_excluded() -> None:
    invs = {"dead": _inv("dead", "t", "k", {"arg_present": "x"}, status="tombstoned")}
    affs = {"o": _aff("o", "t")}
    plan = plan_migration(invs, affs)
    assert plan.ready == () and plan.deferred == ()


def test_distinct_guard_contracts_on_one_trigger_get_unique_ids() -> None:
    invs = {
        "g1": _inv("g1", "smoother_mark_addressed", "kind_one", {"arg_present": "x"}),
        "g2": _inv("g2", "smoother_mark_addressed", "kind_two", {"arg_nonempty": "y"}),
    }
    affs = {"mark": _aff("mark", "smoother_mark_addressed")}
    plan = plan_migration(invs, affs)
    ids = sorted(c.check_id for c in plan.ready)
    assert len(ids) == 2 and len(set(ids)) == 2
    assert all(i.startswith("guard_smoother_mark_addressed__") for i in ids)


def test_residual_collision_same_trigger_and_kind_gets_hash_suffix() -> None:
    # Same trigger + same friction_kind, different predicate -> same base id;
    # the dedupe pass must still make them unique.
    invs = {
        "g1": _inv("g1", "t", "samekind", {"any_earlier_step_result_contains": "a"}),
        "g2": _inv("g2", "t", "samekind", {"any_earlier_step_result_contains": "b"}),
    }
    affs = {"o": _aff("o", "t")}
    plan = plan_migration(invs, affs)
    ids = sorted(c.check_id for c in plan.ready)
    assert len(set(ids)) == 2
    assert ids[0].startswith("guard_t__samekind")


def test_source_count_accounts_for_every_active_invariant() -> None:
    invs = {
        "ready": _inv("ready", "m1", "k", {"not": {"step_exists": {"material_name": "pre"}}}),
        "deferred": _inv("deferred", "orphan_material", "k", {"arg_present": "x"}),
    }
    affs = {"o": _aff("o", "m1", "pre")}
    plan = plan_migration(invs, affs)
    assert plan.source_count == 2
    assert len(plan.ready) == 1 and len(plan.deferred) == 1
