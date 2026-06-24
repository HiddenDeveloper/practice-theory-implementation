---
id: pm_pool_read_before_amend_bundle
name: Require pool read before amending bundle wiring
status: tombstoned
trigger: pm_amend_bundle
mode: detect
friction_kind: pm_pool_read_gate_missing
forbid_when:
  not:
    step_exists:
      material_name: pm_read_pool
message: Practice Management amended bundle wiring without a same-enactment pm_read_pool
  grounding step before the write.
tombstoned_at: '2026-06-24T23:04:28+00:00'
tombstone_reason: migrated to an affordance precondition (phase 3)
---
When a Practice Management enactment reaches `pm_amend_bundle`, the earlier trail must contain `pm_read_pool` for the pool ids or current content the bundle amendment relies on. This invariant covers the determinate bundle-wiring part of Friction 702: bundle selection changes cannot proceed from reload, remembered context, or bundle-description text alone.
