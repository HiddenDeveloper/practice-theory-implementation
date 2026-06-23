---
id: pm_read_pool_before_reload_seed_substrate_v990
name: Practice Management reload requires prior pool read
status: active
trigger: pm_reload_seed_substrate
mode: detect
friction_kind: quality_signal_affordance_coverage
forbid_when:
  not:
    step_exists:
      material_name: pm_read_pool
message: Practice Management invoked pm_reload_seed_substrate before a visible pm_read_pool
  for the substrate pool being relied on.
---
For Practice Management substrate stewardship, a reload is not an entry move. If an enactment contains `pm_reload_seed_substrate`, it must already contain a visible `pm_read_pool` step earlier in the same enactment. This deterministically covers the recurring quality signal where Practice Management begins from reload and then proceeds into authoring, documentation-impact, or bundle amendment without the pool-grounding row.
