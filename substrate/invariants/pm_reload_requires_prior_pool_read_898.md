---
id: pm_reload_requires_prior_pool_read_898
name: Practice Management reload requires prior pool read
status: tombstoned
trigger: pm_reload_seed_substrate
mode: detect
friction_kind: practice_quality_affordance_coverage
forbid_when:
  not:
    step_exists:
      material_name: pm_read_pool
message: Practice Management substrate reload must not be the first stewardship move;
  read the exact relied-on pool with pm_read_pool before pm_reload_seed_substrate.
tombstoned_at: '2026-06-24T23:04:28+00:00'
tombstone_reason: migrated to an affordance precondition (phase 3)
---
When a Practice Management enactment invokes pm_reload_seed_substrate, the earlier trail must already contain pm_read_pool for the substrate pool whose ids or current content the work relies on. This deterministic guard addresses the repeated evaluated pattern in Friction 898 where reload began substrate stewardship without the required pool-grounding row.
