---
id: pm_pool_read_before_create_affordance
name: Require pool read before creating affordance
status: tombstoned
trigger: pm_create_affordance
mode: detect
friction_kind: pm_pool_read_gate_missing
forbid_when:
  not:
    step_exists:
      material_name: pm_read_pool
message: Practice Management created an affordance without a same-enactment pm_read_pool
  grounding step before the write.
tombstoned_at: '2026-06-24T23:04:28+00:00'
tombstone_reason: migrated to an affordance precondition (phase 3)
---
When a Practice Management enactment reaches `pm_create_affordance`, the earlier trail must contain `pm_read_pool` for the relevant substrate surface. This invariant covers the determinate part of the pool-read gate surfaced by Friction 702: an affordance creation write cannot proceed from reload, remembered context, or bundle prose alone.
