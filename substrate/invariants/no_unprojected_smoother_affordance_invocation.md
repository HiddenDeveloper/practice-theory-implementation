---
id: no_unprojected_smoother_affordance_invocation
name: No unprojected affordance invocation in Smoother closures
status: active
trigger: smoother_mark_addressed
mode: detect
friction_kind: unavailable_affordance_invocation
forbid_when:
  all:
  - any_earlier_step_result_contains: 'KeyError: no affordance'
  - any_earlier_step_result_contains: in practice 'smoother'
message: 'A Smoother enactment marked Friction addressed after an earlier step recorded
  KeyError: no affordance in practice ''smoother'', meaning it reached outside the
  affordances projected by the active Smoother bundle.'
---
When a Smoother closure is triggered by smoother_mark_addressed, forbid the closure if any earlier step result shows `KeyError: no affordance` for practice `smoother`. This captures the determinable part of unavailable_affordance_invocation: the active projection already listed the Smoother affordances, and a material invocation outside that projection is mechanically visible in the recorded step result. The invariant raises and resolves that concern deterministically so future Smoother runs are audited without requiring the Judge to rediscover the same unavailable-affordance pattern by hand.
