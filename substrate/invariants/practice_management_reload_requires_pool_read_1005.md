---
id: practice_management_reload_requires_pool_read_1005
name: Practice Management reload requires pool grounding
status: tombstoned
trigger: pm_reload_seed_substrate
mode: detect
friction_kind: quality_friction_substrate_authoring_without_pool_read
forbid_when:
  not:
    step_exists:
      material_name: pm_read_pool
message: Practice Management reload began before a visible pm_read_pool row for the
  substrate pool supplying ids or current content.
tombstoned_at: '2026-06-24T23:04:28+00:00'
tombstone_reason: migrated to an affordance precondition (phase 3)
---
For Practice Management substrate stewardship, reload is not an entry move. When a closed enactment contains pm_reload_seed_substrate, an earlier pm_read_pool step must be visible so the pool supplying ids or current content is grounded before reload context can drive authoring, amendment, documentation checks, bundle wiring, verification, or closure.
