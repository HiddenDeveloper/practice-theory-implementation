---
id: pm_reload_requires_prior_pool_read
name: Practice Management reload requires prior pool read
status: active
trigger: pm_reload_seed_substrate
mode: detect
friction_kind: practice_quality_affordance_coverage
forbid_when:
  not:
    step_exists:
      material_name: pm_read_pool
message: Practice Management substrate stewardship reached pm_reload_seed_substrate
  before any visible pm_read_pool row. The pass is interrupted until the exact relied-on
  pool is read or a concrete pool-read blocker is recorded.
---
When a Practice Management enactment reaches pm_reload_seed_substrate, the earlier trail must already contain pm_read_pool. This deterministic check covers the recurring entry failure named in Friction 835: reload began substrate stewardship without the pool-grounding row the bundle already requires. The invariant is deliberately narrow: it enforces the reload entry gate and leaves exact-pool adequacy, blocker adequacy, and non-reload stewardship paths to judgement or future narrower invariants when their recorded shape is determinable.
