---
id: practice_management_pool_read_before_reload
name: Practice Management reads pool before reload
status: tombstoned
trigger: pm_reload_seed_substrate
mode: detect
friction_kind: practice_quality_affordance_coverage
forbid_when:
  not:
    step_exists:
      material_name: pm_read_pool
message: Practice Management substrate stewardship invoked pm_reload_seed_substrate
  before the required pm_read_pool entry row for the relied-on pool.
tombstoned_at: '2026-06-24T23:04:28+00:00'
tombstone_reason: migrated to an affordance precondition (phase 3)
---
When a Practice Management substrate-stewardship enactment reaches reload, the required pool-grounding row must already be visible. A prior pm_read_pool step is the deterministic minimum evidence; if it is absent before pm_reload_seed_substrate, raise practice_quality_affordance_coverage for the missing entry gate.
