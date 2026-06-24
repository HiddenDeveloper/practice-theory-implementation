---
id: pm_check_documentation_impact_requires_prior_pool_read_861
name: Documentation impact requires prior pool read
status: tombstoned
trigger: pm_check_documentation_impact
mode: detect
friction_kind: practice_quality_substrate_authoring_without_pool_read
forbid_when:
  not:
    step_exists:
      material_name: pm_read_pool
message: Practice Management invoked pm_check_documentation_impact without an earlier
  pm_read_pool grounding step in the same enactment.
tombstoned_at: '2026-06-24T23:04:28+00:00'
tombstone_reason: migrated to an affordance precondition (phase 3)
---
Friction 861 confirms the Practice Management `uses_substrate_authoring_surface` quality concern still includes documentation-impact paths where `pm_check_documentation_impact` appears without a visible same-enactment `pm_read_pool`. This invariant makes that determinable contract deterministic for documentation-impact stewardship: when `pm_check_documentation_impact` is triggered, a prior `pm_read_pool` step must already be present. It intentionally checks only the presence of the pool-read row; whether the exact pool was sufficient remains judgement-shaped.
