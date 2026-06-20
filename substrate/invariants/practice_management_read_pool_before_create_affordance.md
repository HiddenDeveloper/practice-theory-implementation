---
id: practice_management_read_pool_before_create_affordance
name: Practice Management reads pool before creating affordance
status: active
trigger: pm_create_affordance
mode: detect
friction_kind: quality_friction_affordance_coverage
forbid_when:
  not:
    step_exists:
      material_name: pm_read_pool
message: Practice Management created an affordance without an earlier pm_read_pool
  step in the same enactment. Read the relevant pool surface before authoring.
---
For Practice Management authoring, a `pm_create_affordance` step is invalid unless the same enactment has already exposed the relevant substrate surface through `pm_read_pool`. This invariant makes the `uses_substrate_authoring_surface` contract deterministic for the affordance-authoring path confirmed in Friction 714.
