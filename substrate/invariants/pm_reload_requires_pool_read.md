---
id: pm_reload_requires_pool_read
name: Practice Management reload requires pool read
status: active
trigger: pm_reload_seed_substrate
mode: detect
friction_kind: quality_friction_substrate_authoring_without_pool_read
forbid_when:
  not:
    step_exists:
      material_name: pm_read_pool
message: Practice Management invoked pm_reload_seed_substrate before any visible pm_read_pool
  grounding row. Read the exact pool whose ids or content the stewardship work relies
  on before reload or stop with a substrate-surface blocker.
---
For Practice Management substrate stewardship, reload is a substrate-authoring entry point. A closed enactment containing pm_reload_seed_substrate is invalid when no earlier pm_read_pool step is visible, because the practitioner has not exposed the pool whose ids or current content the work relies on before proceeding to reload and later substrate actions.
