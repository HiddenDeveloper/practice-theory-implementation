---
name: requires_pm_read_pool_before_pm_check_documentation_impact
input_schema: {}
implementation:
  kind: enactment_check
  trigger: pm_check_documentation_impact
  friction_kind: quality_affordance_coverage
  message: Practice Management invoked pm_check_documentation_impact before a visible
    pm_read_pool for the relied-on substrate pool.
  forbid_when:
    not:
      step_exists:
        material_name: pm_read_pool
---
Migrated 2026-06-24T23:04:28+00:00 from 4 invariant(s): pm_check_documentation_impact_requires_prior_pool_read, pm_check_documentation_impact_requires_prior_pool_read_861, pm_documentation_impact_requires_pool_read….
