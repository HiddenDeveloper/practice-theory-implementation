---
id: pm_read_pool_before_reload
name: Practice Management reads the relied-on pool before reload
status: tombstoned
trigger: pm_reload_seed_substrate
mode: detect
friction_kind: practice_quality_affordance_coverage
forbid_when:
  not:
    step_exists:
      material_name: pm_read_pool
message: Practice Management reached pm_reload_seed_substrate before a visible pm_read_pool
  for the substrate pool the stewardship work relies on.
tombstoned_at: '2026-06-24T23:04:28+00:00'
tombstone_reason: migrated to an affordance precondition (phase 3)
---
For Practice Management substrate stewardship, reload is not an entry move. A closed enactment that contains `pm_reload_seed_substrate` must have an earlier visible `pm_read_pool` row; otherwise the pool-grounding gate has been skipped and the deterministic omission should be raised directly instead of rediscovered by hand.
