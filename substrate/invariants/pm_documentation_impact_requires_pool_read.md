---
id: pm_documentation_impact_requires_pool_read
name: Practice Management documentation-impact requires prior pool read
status: tombstoned
trigger: pm_check_documentation_impact
mode: detect
friction_kind: quality_friction:substrate_authoring_without_pool_read
forbid_when:
  not:
    step_exists:
      material_name: pm_read_pool
message: Practice Management checked documentation impact without an earlier pm_read_pool
  step in the same enactment, so the documentation judgement was not grounded in the
  current substrate pool surface it depends on.
tombstoned_at: '2026-06-24T23:04:28+00:00'
tombstone_reason: migrated to an affordance precondition (phase 3)
---
This governed invariant addresses the remaining determinable documentation-impact part of Friction 571. The targeted Friction names Practice Management quality signal `uses_substrate_authoring_surface`: recent substrate-management enactments included authoring, amendment, reload, or documentation-impact steps with no `pm_read_pool`. Existing rules `rule_pm_read_pool_before_authoring` and `rule_pm_preview_before_apply` already say documentation-impact stewardship after substrate change is grounded work and must be preceded by a current substrate pool read; existing invariants cover `pm_create_affordance`, `pm_amend_bundle`, and `pm_reload_seed_substrate`. This invariant covers the documentation-impact shape deterministically by triggering on `pm_check_documentation_impact` when no earlier `pm_read_pool` exists in the same enactment. It intentionally checks only presence of an earlier pool read, because whether the exact pool read was sufficient remains judgement-shaped.
