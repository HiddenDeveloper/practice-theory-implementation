---
id: no_close_on_unpersisted_amendment
name: Don't mark addressed when only non-persisted amendment work is visible
status: tombstoned
trigger: smoother_mark_addressed
mode: detect
friction_kind: non_persisted_amendment_marked_addressed
forbid_when:
  all:
  - any_earlier_step_result_contains: '"persisted": false'
  - not:
      any:
      - any_earlier_step_result_contains: '"persisted": true'
      - any_earlier_step_result_contains: '"affordance"'
      - any_earlier_step_result_contains: '"bundle"'
      - any_earlier_step_result_contains: '"pool"'
      - any_earlier_step_result_contains: '"invariant"'
message: This enactment marked a Friction addressed after an amendment reported persisted=false,
  and no earlier persisted amendment surface was visible before the addressed mark;
  the closure appears to rest only on a change that did not save.
tombstoned_at: '2026-06-24T23:04:28+00:00'
tombstone_reason: migrated to an affordance precondition (phase 3)
---
A governed deterministic invariant: a Smoother must not close a Friction as addressed when amendment work before the addressed mark only shows a non-persisted result. This invariant still catches the determinable case where an earlier step reports `persisted: false` and no visible persisted substrate amendment surface appears before closure. It no longer treats every earlier `persisted: false` as disqualifying: if the same enactment later records a persisted material amendment (`persisted: true`) or another persisted substrate amendment surface (`affordance`, `bundle`, `pool`, or `invariant`) before `smoother_mark_addressed`, the invariant leaves that case for judgement/audit instead of auto-firing. This addresses the false positive where a failed code-owned material amendment was followed by a persisted affordance amendment that supplied the closure basis.
