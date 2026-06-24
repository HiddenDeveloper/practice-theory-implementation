---
name: requires_pm_read_pool_before_pm_amend_bundle
input_schema: {}
implementation:
  kind: enactment_check
  trigger: pm_amend_bundle
  friction_kind: practice_quality_affordance_coverage
  message: Practice Management amended bundle wiring without a same-enactment pm_read_pool
    grounding step before the write.
  forbid_when:
    not:
      step_exists:
        material_name: pm_read_pool
---
Migrated 2026-06-24T23:04:28+00:00 from 5 invariant(s): pm_amend_bundle_pool_read_affordance_coverage_957, pm_amend_bundle_requires_pool_read, pm_amend_bundle_requires_prior_pool_read….
