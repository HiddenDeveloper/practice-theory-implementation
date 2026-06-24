---
name: requires_pm_read_pool_before_pm_reload_seed_substrate
input_schema: {}
implementation:
  kind: enactment_check
  trigger: pm_reload_seed_substrate
  friction_kind: practice_quality_affordance_coverage
  message: Practice Management reached pm_reload_seed_substrate before a visible pm_read_pool
    for the substrate pool being relied on.
  forbid_when:
    not:
      step_exists:
        material_name: pm_read_pool
---
Migrated 2026-06-24T23:04:28+00:00 from 13 invariant(s): pm_pool_read_before_reload, pm_read_pool_before_reload, pm_read_pool_before_reload_gate….
