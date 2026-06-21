---
id: pm_read_pool_before_reload_gate
name: Practice Management reads pool before reload
status: active
trigger: pm_reload_seed_substrate
mode: detect
friction_kind: quality_affordance_coverage
forbid_when:
  not:
    step_exists:
      material_name: pm_read_pool
message: Practice Management reached pm_reload_seed_substrate before a visible pm_read_pool
  for the substrate pool being relied on.
---
For Practice Management substrate stewardship, reload is not an entry move. If an enactment reaches pm_reload_seed_substrate before any earlier pm_read_pool row, raise quality_affordance_coverage so the missing pool-grounding gate is detected deterministically instead of repeatedly re-found by hand.
