---
name: requires_pm_read_pool_before_pm_create_affordance
input_schema: {}
implementation:
  kind: enactment_check
  trigger: pm_create_affordance
  friction_kind: quality_friction:substrate_authoring_without_pool_read
  message: Practice Management created an affordance without a same-enactment pm_read_pool
    grounding step before the write.
  forbid_when:
    not:
      step_exists:
        material_name: pm_read_pool
---
Migrated 2026-06-24T23:04:28+00:00 from 4 invariant(s): pm_create_affordance_requires_pool_read, pm_create_affordance_requires_prior_pool_read, pm_pool_read_before_create_affordance….
