---
name: guard_remsleep_dispatch_memory_signal__invalid_material_invocation
input_schema: {}
implementation:
  kind: enactment_check
  trigger: remsleep_dispatch_memory_signal
  friction_kind: invalid_material_invocation
  message: 'A Memory Recall enactment dispatched a memory signal after an earlier
    step recorded an invalid material invocation: the requested material was not reached
    by that affordance. Use the active projection''s listed material names, not the
    affordance id, before dispatching the signal.'
  forbid_when:
    any_earlier_step_result_contains: not reached for by affordance
---
Migrated 2026-06-24T23:04:28+00:00 from 1 invariant(s): no_material_alias_misreach_before_memory_signal.
