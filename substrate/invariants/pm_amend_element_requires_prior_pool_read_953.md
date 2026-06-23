---
id: pm_amend_element_requires_prior_pool_read_953
name: Practice Management pool-element amendment requires prior pool read
status: active
trigger: pm_amend_element
mode: detect
friction_kind: quality_affordance_coverage
forbid_when:
  not:
    step_exists:
      material_name: pm_read_pool
message: Practice Management invoked pm_amend_element without an earlier pm_read_pool
  grounding step in the same enactment.
---
Friction 953 confirmed that Practice Management still has a genuine `uses_substrate_authoring_surface` quality-affordance concern: evaluated substrate-stewardship passes reached reload, documentation-impact, authoring, amendment, evaluation, or bundle-wiring surfaces without the required same-enactment `pm_read_pool`. Existing active invariants cover the target sequence's reload, create-affordance, bundle-amendment, and documentation-impact shapes; this invariant fills the generic pool-element amendment path deterministically. When `pm_amend_element` appears, a prior `pm_read_pool` must already be visible. The invariant intentionally checks only for the pool-read row; whether the exact pool read was sufficient remains judgement-shaped.
