---
id: pm_documentation_impact_requires_prior_pool_read
name: Practice Management documentation impact requires prior pool read
status: tombstoned
trigger: pm_check_documentation_impact
mode: detect
friction_kind: uses_substrate_authoring_surface
forbid_when:
  not:
    step_exists:
      material_name: pm_read_pool
message: Practice Management substrate stewardship invoked pm_check_documentation_impact
  before a visible pm_read_pool for the relied-on pool. Read the exact pool first,
  or stop with a concrete substrate-surface blocker.
tombstoned_at: '2026-06-24T23:04:28+00:00'
tombstone_reason: migrated to an affordance precondition (phase 3)
---
When a Practice Management enactment invokes pm_check_documentation_impact, the trail must already expose a pm_read_pool row for the pool whose ids or current content the documentation-impact check relies on. Documentation context is not a substitute for pool grounding; if the pool cannot be read, record a concrete blocker instead of continuing.
