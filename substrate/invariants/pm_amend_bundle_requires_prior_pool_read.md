---
id: pm_amend_bundle_requires_prior_pool_read
name: Amend bundle requires prior pool read
status: tombstoned
trigger: pm_amend_bundle
mode: detect
friction_kind: practice_quality_substrate_authoring_without_pool_read
forbid_when:
  not:
    step_exists:
      material_name: pm_read_pool
message: Practice Management invoked pm_amend_bundle without an earlier pm_read_pool
  grounding step in the same enactment.
tombstoned_at: '2026-06-24T23:04:28+00:00'
tombstone_reason: migrated to an affordance precondition (phase 3)
---
For Practice Management bundle wiring, a current-enactment pm_read_pool step must appear before pm_amend_bundle. This invariant makes the repeated substrate-authoring-without-pool-read contract deterministic for the bundle-selection path named by Friction 718.
