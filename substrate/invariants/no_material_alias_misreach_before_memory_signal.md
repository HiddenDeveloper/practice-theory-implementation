---
id: no_material_alias_misreach_before_memory_signal
name: No stale material aliases before memory signal dispatch
status: active
trigger: remsleep_dispatch_memory_signal
mode: detect
friction_kind: invalid_material_invocation
forbid_when:
  any_earlier_step_result_contains: not reached for by affordance
message: 'A Memory Recall enactment dispatched a memory signal after an earlier step
  recorded an invalid material invocation: the requested material was not reached
  by that affordance. Use the active projection''s listed material names, not the
  affordance id, before dispatching the signal.'
---
When a Memory Recall enactment reaches `remsleep_dispatch_memory_signal`, forbid closure if any earlier step result contains `not reached for by affordance`. That validation error means the enactment first invoked an affordance with an invalid or stale material name, including the determinable pattern where the material name mirrors the affordance id instead of one of the reached `remsleep_*` material names listed by the projection error. The invariant raises and auto-resolves `invalid_material_invocation` deterministically for that closure surface so the Judge does not need to rediscover the same invocation-contract drift by hand.
