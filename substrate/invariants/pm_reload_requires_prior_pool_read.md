---
id: pm_reload_requires_prior_pool_read
name: Practice Management reload requires pool grounding
status: tombstoned
trigger: pm_reload_seed_substrate
mode: detect
friction_kind: uses_substrate_authoring_surface
forbid_when:
  not:
    step_exists:
      material_name: pm_read_pool
message: Practice Management reached pm_reload_seed_substrate before a visible pm_read_pool
  row for the substrate pool the stewardship pass relies on. Read the exact pool first
  or stop with a concrete substrate-surface blocker.
tombstoned_at: '2026-06-24T23:04:28+00:00'
tombstone_reason: migrated to an affordance precondition (phase 3)
---
Friction 839 shows the Practice Management `uses_substrate_authoring_surface` quality concern is repeatedly re-found in evaluated windows where `pm_reload_seed_substrate` appears before any `pm_read_pool`, followed in some traces by documentation checks or authoring/amendment. This invariant makes that determinate entry-gate failure machine-detectable: a Practice Management reload step is forbidden unless an earlier same-enactment `pm_read_pool` exposed the substrate pool being relied on. The create attempt for this id failed only because the invariant already existed; this amendment is the explicit same-id refinement path and does not rely on unread existing invariant fields.
