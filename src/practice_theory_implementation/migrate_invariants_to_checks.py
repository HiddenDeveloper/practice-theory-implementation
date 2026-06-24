"""Phase 3 migration planner: free-floating invariants -> affordance checks.

Dry-run first, by design. The ownership sort encodes judgement, so this module
only *plans* — it produces a `MigrationPlan` and a human-readable report; it
does not write substrate. Run it, review the collapse, decide the review cases,
then apply.

The plan (docs/plans/invariants-as-affordance-material-checks.md) v1 scope is
**affordance preconditions only**. Each active invariant is sorted by its
`trigger` material:

- the affordances whose `materials` include the trigger are its owner
  candidates;
- invariants with identical `(trigger, forbid_when)` collapse to ONE check —
  friction-kind label drift (e.g. `quality_affordance_coverage` vs
  `practice_quality_affordance_coverage`) is itself sprawl and is merged;
- exactly one owner -> `ready`; several owners -> `needs_review` (likely a
  material-level contract, v2); zero owners -> `deferred` (stale alias / not
  afforded — tombstone or v2).

Usage:
    uv run python -m practice_theory_implementation.migrate_invariants_to_checks
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from collections.abc import Mapping
from dataclasses import dataclass, replace

from practice_theory_implementation.types import Affordance, Check, Invariant, Substrate


def _canonical(forbid_when: Mapping[str, object]) -> str:
    return json.dumps(forbid_when, sort_keys=True)


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def _required_material(forbid_when: Mapping[str, object]) -> str | None:
    """If the predicate is the common `not step_exists{material_name: M}` form,
    return M — the material whose earlier presence the check requires."""
    if set(forbid_when) != {"not"}:
        return None
    inner = forbid_when["not"]
    if not isinstance(inner, Mapping) or set(inner) != {"step_exists"}:
        return None
    se = inner["step_exists"]
    mat = se.get("material_name") if isinstance(se, Mapping) else None
    return mat if isinstance(mat, str) else None


def _check_id(trigger: str, forbid_when: Mapping[str, object], friction_kind: str) -> str:
    """A readable, stable id for a check. Encodes the trigger so an owner rarely
    collides two checks. `requires_<M>_before_<trigger>` for the precondition
    form; `guard_<trigger>__<kind>` otherwise. A trigger with several distinct
    non-precondition contracts is disambiguated further by `_dedupe_ids`."""
    required = _required_material(forbid_when)
    if required is not None:
        return f"requires_{required}_before_{trigger}"
    return f"guard_{trigger}__{_slug(friction_kind)}"


def _dedupe_ids(checks: list[PlannedCheck]) -> list[PlannedCheck]:
    """Guarantee check_id uniqueness within an owner-set. On a residual
    collision (same trigger+kind, different predicate), append a short stable
    hash of the canonical forbid_when — deterministic, so the firing identity is
    stable across runs."""
    seen: set[tuple[tuple[str, ...], str]] = set()
    out: list[PlannedCheck] = []
    for check in checks:
        key = (check.owner_candidates, check.check_id)
        if key in seen:
            suffix = hashlib.sha1(_canonical(check.forbid_when).encode()).hexdigest()[:6]
            check = replace(check, check_id=f"{check.check_id}_{suffix}")
        seen.add((check.owner_candidates, check.check_id))
        out.append(check)
    return out


def _shortest_message(members: list[Invariant]) -> str:
    msgs = [m.message for m in members if m.message]
    return min(msgs, key=len) if msgs else ""


@dataclass(frozen=True, slots=True)
class PlannedCheck:
    """One surviving check, subsuming a dedup group of source invariants."""

    check_id: str
    trigger: str
    friction_kind: str  # the canonical (most common) kind across the group
    message: str
    forbid_when: Mapping[str, object]
    owner_candidates: tuple[str, ...]  # affordances reaching the trigger
    source_invariant_ids: tuple[str, ...]
    merged_friction_kinds: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Deferred:
    invariant_id: str
    trigger: str
    reason: str


@dataclass(frozen=True, slots=True)
class MigrationPlan:
    ready: tuple[PlannedCheck, ...]  # exactly one owner affordance
    needs_review: tuple[PlannedCheck, ...]  # several candidate owners
    deferred: tuple[Deferred, ...]  # no affordance owner

    @property
    def source_count(self) -> int:
        from_checks = sum(
            len(c.source_invariant_ids) for c in (*self.ready, *self.needs_review)
        )
        return from_checks + len(self.deferred)


def plan_migration(
    invariants: Mapping[str, Invariant], affordances: Mapping[str, Affordance]
) -> MigrationPlan:
    """Sort active invariants into affordance checks, deduped on (trigger,
    forbid_when). Pure: takes the two pools, returns the plan."""
    groups: dict[tuple[str, str], list[Invariant]] = defaultdict(list)
    for inv in invariants.values():
        if inv.status != "active":
            continue
        groups[(inv.trigger, _canonical(inv.forbid_when))].append(inv)

    ready: list[PlannedCheck] = []
    needs_review: list[PlannedCheck] = []
    deferred: list[Deferred] = []

    for (trigger, _canon), members in sorted(groups.items()):
        owners = tuple(
            sorted(a.id for a in affordances.values() if trigger in a.materials)
        )
        kinds = [m.friction_kind for m in members]
        canonical_kind = Counter(kinds).most_common(1)[0][0]
        if not owners:
            for m in members:
                deferred.append(
                    Deferred(
                        invariant_id=m.id,
                        trigger=trigger,
                        reason=(
                            "no affordance reaches this trigger material "
                            "(stale alias / not afforded — tombstone or v2 material contract)"
                        ),
                    )
                )
            continue
        check = PlannedCheck(
            check_id=_check_id(trigger, members[0].forbid_when, canonical_kind),
            trigger=trigger,
            friction_kind=canonical_kind,
            message=_shortest_message(members),
            forbid_when=members[0].forbid_when,
            owner_candidates=owners,
            source_invariant_ids=tuple(sorted(m.id for m in members)),
            merged_friction_kinds=tuple(sorted(set(kinds))),
        )
        (ready if len(owners) == 1 else needs_review).append(check)

    return MigrationPlan(
        ready=tuple(_dedupe_ids(ready)),
        needs_review=tuple(_dedupe_ids(needs_review)),
        deferred=tuple(deferred),
    )


def _precondition_check(planned: PlannedCheck, now: str) -> Check:
    ids = planned.source_invariant_ids
    head = ", ".join(ids[:3]) + ("…" if len(ids) > 3 else "")
    return Check(
        id=planned.check_id,
        name=planned.check_id.replace("_", " "),
        trigger=planned.trigger,
        friction_kind=planned.friction_kind,
        message=planned.message,
        forbid_when=planned.forbid_when,
        content=f"Migrated {now} from {len(ids)} invariant(s): {head}.",
    )


def build_apply_changes(
    plan: MigrationPlan,
    affordances: Mapping[str, Affordance],
    invariants: Mapping[str, Invariant],
    *,
    now: str,
) -> tuple[list[Affordance], list[Invariant]]:
    """Pure: the affordances to rewrite (preconditions appended) and the
    invariants to tombstone. `needs_review` checks are applied to every owner
    candidate (decision 1a); deferred invariants are tombstoned as dead.
    """
    new_pc: dict[str, list[Check]] = defaultdict(list)
    migrated: set[str] = set()
    for planned in (*plan.ready, *plan.needs_review):
        check = _precondition_check(planned, now)
        for owner in planned.owner_candidates:
            new_pc[owner].append(check)
        migrated.update(planned.source_invariant_ids)

    affs_to_write = [
        replace(affordances[owner], preconditions=affordances[owner].preconditions + tuple(checks))
        for owner, checks in sorted(new_pc.items())
    ]

    deferred_ids = {d.invariant_id for d in plan.deferred}
    invs_to_tombstone: list[Invariant] = []
    for iid in sorted(migrated | deferred_ids):
        inv = invariants[iid]
        reason = (
            "migrated to an affordance precondition (phase 3)"
            if iid in migrated
            else "dead: trigger material is a stale alias no affordance reaches (phase 3)"
        )
        invs_to_tombstone.append(
            replace(inv, status="tombstoned", tombstoned_at=now, tombstone_reason=reason)
        )
    return affs_to_write, invs_to_tombstone


def apply_migration(
    plan: MigrationPlan, substrate: Substrate, *, now: str, root: str | None = None
) -> tuple[list[Affordance], list[Invariant]]:
    """Write the migration: rewrite each owner affordance with its new
    preconditions, and tombstone every migrated + deferred invariant."""
    from practice_theory_implementation import substrate_writer

    affs, invs = build_apply_changes(
        plan, substrate.affordances, substrate.invariants, now=now
    )
    for aff in affs:
        substrate_writer.write_affordance(aff, root=root)
    for inv in invs:
        substrate_writer.write_invariant(inv, root=root)
    return affs, invs


def render_report(plan: MigrationPlan) -> str:
    lines: list[str] = []
    lines.append(
        f"Migration plan: {plan.source_count} active invariants -> "
        f"{len(plan.ready)} ready check(s) + {len(plan.needs_review)} needs-review "
        f"+ {len(plan.deferred)} deferred"
    )
    lines.append("")

    def _emit(check: PlannedCheck) -> None:
        owner = (
            check.owner_candidates[0]
            if len(check.owner_candidates) == 1
            else f"AMBIGUOUS {list(check.owner_candidates)}"
        )
        lines.append(f"  [{len(check.source_invariant_ids)}->1] {owner} :: {check.check_id}")
        lines.append(f"        trigger      = {check.trigger}")
        lines.append(f"        friction_kind= {check.friction_kind}")
        if len(check.merged_friction_kinds) > 1:
            lines.append(f"        merged kinds = {list(check.merged_friction_kinds)}")
        lines.append(f"        forbid_when  = {_canonical(check.forbid_when)}")
        lines.append(f"        subsumes     = {list(check.source_invariant_ids)}")
        lines.append("")

    lines.append(f"READY ({len(plan.ready)} single-owner checks):")
    for c in plan.ready:
        _emit(c)
    lines.append(f"NEEDS REVIEW ({len(plan.needs_review)} multi-owner — likely material-level):")
    for c in plan.needs_review:
        _emit(c)
    lines.append(f"DEFERRED ({len(plan.deferred)} no-owner invariants):")
    for d in plan.deferred:
        lines.append(f"  {d.invariant_id} (trigger={d.trigger}) — {d.reason}")
    return "\n".join(lines)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Plan (default) or apply the invariant->affordance-check migration."
    )
    parser.add_argument(
        "--apply", action="store_true", help="write the changes (default: dry-run report)"
    )
    args = parser.parse_args()

    from practice_theory_implementation.substrate_loader import loaded

    sub = loaded().substrate
    plan = plan_migration(sub.invariants, sub.affordances)
    if not args.apply:
        print(render_report(plan))
        return

    from datetime import UTC, datetime

    now = datetime.now(UTC).isoformat(timespec="seconds")
    affs, invs = apply_migration(plan, sub, now=now)
    print(
        f"Applied: rewrote {len(affs)} affordance(s) with new preconditions; "
        f"tombstoned {len(invs)} invariant(s)."
    )
    for aff in affs:
        print(f"  affordance {aff.id} now carries {len(aff.preconditions)} precondition(s)")


if __name__ == "__main__":
    main()
