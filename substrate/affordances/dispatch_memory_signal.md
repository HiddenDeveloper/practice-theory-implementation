---
id: dispatch_memory_signal
name: Dispatch memory signal
materials:
- remsleep_dispatch_memory_signal
preconditions:
- id: guard_remsleep_dispatch_memory_signal__invalid_material_invocation
  name: guard remsleep dispatch memory signal  invalid material invocation
  trigger: remsleep_dispatch_memory_signal
  friction_kind: invalid_material_invocation
  message: 'A Memory Recall enactment dispatched a memory signal after an earlier
    step recorded an invalid material invocation: the requested material was not reached
    by that affordance. Use the active projection''s listed material names, not the
    affordance id, before dispatching the signal.'
  forbid_when:
    any_earlier_step_result_contains: not reached for by affordance
  content: 'Migrated 2026-06-24T23:04:28+00:00 from 1 invariant(s): no_material_alias_misreach_before_memory_signal.'
---
Emit a bounded, source-backed memory_signal for Memory Consolidation to inspect. Invoke the reached material `remsleep_dispatch_memory_signal` with the material schema's top-level fields: required `content`; optional `kind` (use this for the signal type such as `coverage_gap`), `source_ids`, `evidence`, `suggested_anchor`, and `confidence`. Do not wrap the payload in `memory_signal`, `signal`, or top-level `signal_type`; those wrappers are not accepted by the material. This is Recall's handoff; it is not a canonical memory write.
