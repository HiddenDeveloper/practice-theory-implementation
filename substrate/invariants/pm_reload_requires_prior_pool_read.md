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
message: Practice Management reload occurred before a same-enactment pm_read_pool
  grounding row. Read the exact relied-on pool first, or record a concrete pool-read
  blocker instead of reloading from ungrounded substrate context.
---
Friction 773 made the repeated Practice Management `uses_substrate_authoring_surface` miss determinable for the observed window: every missing case reached `pm_reload_seed_substrate` without `pm_read_pool` while nearby passing traces showed the pool read was reachable. This invariant catches that reload entry violation deterministically so future passes do not rely on Judge rediscovery. It is intentionally scoped to the reload trigger; other substrate write triggers remain judgement territory unless future Friction shows the same determinable pattern without reload.
