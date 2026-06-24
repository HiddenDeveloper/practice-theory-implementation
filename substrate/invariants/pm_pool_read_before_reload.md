---
id: pm_pool_read_before_reload
name: Practice Management reload requires pool read
status: tombstoned
trigger: pm_reload_seed_substrate
mode: detect
friction_kind: uses_substrate_authoring_surface
forbid_when:
  not:
    step_exists:
      material_name: pm_read_pool
message: Practice Management substrate stewardship cannot enter reload before the
  exact relied-on pool has been read with pm_read_pool.
tombstoned_at: '2026-06-24T23:04:28+00:00'
tombstone_reason: migrated to an affordance precondition (phase 3)
---
When a Practice Management enactment contains pm_reload_seed_substrate, an earlier pm_read_pool step must be visible in the same enactment. Reload is a substrate-stewardship surface and cannot substitute for the pool-grounding row. This makes the repeated pool-read entry gate deterministic for the reload-first failure pattern named by Friction 876.
