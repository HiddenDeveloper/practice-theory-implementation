---
id: pm_reload_seed_substrate_requires_prior_pool_read
name: Practice Management reload requires prior pool read
status: tombstoned
trigger: pm_reload_seed_substrate
mode: detect
friction_kind: quality_friction
forbid_when:
  not:
    step_exists:
      material_name: pm_read_pool
message: Practice Management substrate stewardship invoked pm_reload_seed_substrate
  before the required pm_read_pool entry gate. Read the exact relied-on pool before
  reload, or stop with a substrate-surface blocker.
tombstoned_at: '2026-06-24T23:04:28+00:00'
tombstone_reason: migrated to an affordance precondition (phase 3)
---
For Practice Management substrate stewardship, reload is not an entry move. If a closed enactment contains pm_reload_seed_substrate and no earlier pm_read_pool step, deterministically surface the missing-pool-read quality friction that the Judge has repeatedly found by hand.
