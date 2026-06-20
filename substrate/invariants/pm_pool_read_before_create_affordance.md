---
id: pm_pool_read_before_create_affordance
name: Require pool read before creating affordance
status: active
trigger: pm_create_affordance
mode: detect
friction_kind: pm_pool_read_gate_missing
forbid_when:
  not:
    step_exists:
      material_name: pm_read_pool
message: Practice Management created an affordance without a same-enactment pm_read_pool
  grounding step before the write.
---
When a Practice Management enactment reaches `pm_create_affordance`, the earlier trail must contain `pm_read_pool` for the relevant substrate surface. This invariant covers the determinate part of the pool-read gate surfaced by Friction 702: an affordance creation write cannot proceed from reload, remembered context, or bundle prose alone.
