---
id: practice_management_read_pool_before_amend_bundle
name: Practice Management reads pool before bundle wiring
status: tombstoned
trigger: pm_amend_bundle
mode: detect
friction_kind: quality_friction_affordance_coverage
forbid_when:
  not:
    step_exists:
      material_name: pm_read_pool
message: Practice Management amended bundle wiring without an earlier pm_read_pool
  step in the same enactment. Read the relevant pool surface before selecting or changing
  bundle ids.
tombstoned_at: '2026-06-24T23:04:28+00:00'
tombstone_reason: migrated to an affordance precondition (phase 3)
---
For Practice Management bundle wiring, a `pm_amend_bundle` step is invalid unless the same enactment has already exposed the relevant substrate surface through `pm_read_pool`. This invariant makes the `uses_substrate_authoring_surface` contract deterministic for the bundle-wiring path confirmed in Friction 714.
