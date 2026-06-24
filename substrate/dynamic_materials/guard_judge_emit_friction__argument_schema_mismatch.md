---
name: guard_judge_emit_friction__argument_schema_mismatch
input_schema: {}
implementation:
  kind: enactment_check
  trigger: judge_emit_friction
  friction_kind: argument_schema_mismatch
  message: A Judge enactment reached judge_emit_friction after an earlier failed call
    used the stale enactment_id argument. Use target_enactment_id for the closure
    surface; this is an argument schema mismatch on the Judge friction-emission material.
  forbid_when:
    any_earlier_step_result_contains: unexpected keyword argument 'enactment_id'
---
Migrated 2026-06-24T23:04:28+00:00 from 1 invariant(s): no_judge_emit_friction_enactment_id_schema_mismatch.
