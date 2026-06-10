---
id: no_judge_emit_friction_enactment_id_schema_mismatch
name: No enactment_id schema mismatch before Judge friction closure
status: active
trigger: judge_emit_friction
mode: detect
friction_kind: closure_schema_mismatch
forbid_when:
  any_earlier_step_result_contains: unexpected keyword argument 'enactment_id'
message: A Judge enactment reached judge_emit_friction after an earlier failed call
  used the stale enactment_id argument. Use target_enactment_id for the closure surface.
---
When a Judge enactment reaches `judge_emit_friction`, forbid closure if any earlier step result contains `unexpected keyword argument 'enactment_id'`. That error means the closure surface was first invoked with the stale `enactment_id` argument before the corrected `target_enactment_id` call. The invariant raises and auto-resolves `closure_schema_mismatch` deterministically for that schema boundary so the Judge does not need to rediscover the same failed closure attempt by hand.
