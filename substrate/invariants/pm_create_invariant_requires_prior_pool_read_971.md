---
id: pm_create_invariant_requires_prior_pool_read_971
name: Practice Management invariant authoring requires prior pool read
status: tombstoned
trigger: pm_create_invariant
mode: detect
friction_kind: practice_quality_affordance_coverage
forbid_when:
  not:
    step_exists:
      material_name: pm_read_pool
message: Practice Management invoked pm_create_invariant without an earlier pm_read_pool
  grounding step in the same enactment.
tombstoned_at: '2026-06-24T23:04:28+00:00'
tombstone_reason: migrated to an affordance precondition (phase 3)
---
Friction 971 confirms the Practice Management `uses_substrate_authoring_surface` quality concern is still being rediscovered across evaluated windows: substrate stewardship reached reload, authoring, amendment, documentation-impact, evaluation, or invariant surfaces without a same-enactment `pm_read_pool`, even though the bundle already makes that row the entry gate. Existing active invariants cover the named target sequence's reload, create-affordance, documentation-impact, create/amend pool-element, and bundle-amendment paths. This invariant fills the invariant-authoring path deterministically: when `pm_create_invariant` appears, an earlier `pm_read_pool` must already be visible. It intentionally checks only for the pool-read row; whether the exact pool read was sufficient remains judgement-shaped.
