---
id: pm_reload_requires_prior_pool_read
name: Practice Management reload requires prior pool read
status: active
trigger: pm_reload_seed_substrate
mode: detect
friction_kind: practice_quality_gap
forbid_when:
  not:
    step_exists:
      material_name: pm_read_pool
message: Practice Management reached pm_reload_seed_substrate before any pm_read_pool
  grounding row. The pass is interrupted until the exact relied-on pool is read or
  a concrete substrate-surface blocker is recorded.
---
Friction 815 confirms that the Practice Management pool-grounding gate has become a repeated, determinable contract rather than a judgement-only concern: recent Practice Management enactments repeatedly reached pm_reload_seed_substrate and then documentation-impact, authoring, amendment, or bundle-wiring surfaces without any earlier pm_read_pool row, while a nearby comparator showed pm_read_pool is reachable. For Practice Management substrate stewardship, reload is a stewardship surface and cannot be the entry move. When a closed enactment contains pm_reload_seed_substrate with no earlier pm_read_pool row, deterministically flag the same pool-grounding failure the Judge has repeatedly found by hand. The required recovery is to read the exact pool whose ids or current content the work relies on, or stop with a concrete substrate-surface blocker before any further stewardship action, verification, bundle wiring, or closure.
