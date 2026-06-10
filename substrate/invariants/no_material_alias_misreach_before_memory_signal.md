---
id: no_material_alias_misreach_before_memory_signal
name: No stale material aliases before memory signal dispatch
status: active
trigger: remsleep_dispatch_memory_signal
mode: detect
friction_kind: material_alias_misreach
forbid_when:
  any_earlier_step_result_contains: not reached for by affordance
message: 'A Memory Recall enactment dispatched a memory signal after an earlier step
  recorded a material-name validation failure: the invoked material was not reached
  by the affordance. Use the active projection''s reached material names before dispatching
  the signal.'
---
When a Memory Recall enactment reaches `remsleep_dispatch_memory_signal`, forbid closure if any earlier step result contains `not reached for by affordance`. That validation error means the enactment first invoked an affordance with a stale or mismatched material name, even if it later corrected the call. The invariant raises and auto-resolves `material_alias_misreach` deterministically for that closure surface so the Judge does not need to rediscover the alias-misreach pattern by hand.
