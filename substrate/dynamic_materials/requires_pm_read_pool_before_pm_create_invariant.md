---
name: requires_pm_read_pool_before_pm_create_invariant
input_schema: {}
implementation:
  kind: enactment_check
  trigger: pm_create_invariant
  friction_kind: practice_quality_affordance_coverage
  message: Practice Management invoked pm_create_invariant without an earlier pm_read_pool
    grounding step in the same enactment.
  forbid_when:
    not:
      step_exists:
        material_name: pm_read_pool
---
Migrated 2026-06-24T23:04:28+00:00 from 1 invariant(s): pm_create_invariant_requires_prior_pool_read_971.
