---
id: no_judge_emit_friction_enactment_id_schema_mismatch
name: No enactment_id schema mismatch before Judge friction closure
status: tombstoned
trigger: judge_emit_friction
mode: detect
friction_kind: argument_schema_mismatch
forbid_when:
  any_earlier_step_result_contains: unexpected keyword argument 'enactment_id'
message: A Judge enactment reached judge_emit_friction after an earlier failed call
  used the stale enactment_id argument. Use target_enactment_id for the closure surface;
  this is an argument schema mismatch on the Judge friction-emission material.
tombstoned_at: '2026-06-24T23:04:28+00:00'
tombstone_reason: migrated to an affordance precondition (phase 3)
---
When a Judge enactment reaches `judge_emit_friction`, forbid closure if any earlier step result contains `unexpected keyword argument 'enactment_id'`. That error means the closure surface was first invoked with the stale `enactment_id` argument before the corrected `target_enactment_id` call. The invariant raises and auto-resolves `argument_schema_mismatch` deterministically for that schema boundary so the Judge does not need to rediscover the same failed closure attempt by hand.
