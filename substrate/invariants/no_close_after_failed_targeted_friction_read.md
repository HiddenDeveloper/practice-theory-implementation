---
id: no_close_after_failed_targeted_friction_read
name: No closure after failed or empty targeted Friction read
status: active
trigger: smoother_mark_addressed
mode: detect
friction_kind: ungrounded_closure_attempt
forbid_when:
  any:
  - all:
    - any_earlier_step_result_contains: unexpected keyword argument 'friction_id'
    - not:
        step_exists:
          affordance_id: read_pending_friction
          result_contains: '"id"'
  - all:
    - any_earlier_step_result_contains: '[]'
    - step_exists:
        affordance_id: read_pending_friction
        result_contains: '[]'
    - not:
        step_exists:
          affordance_id: read_pending_friction
          result_contains: '"id"'
message: A Smoother enactment invoked mark_friction_addressed after an earlier targeted
  read_pending_friction call failed or returned no pending Friction, and no successful
  pending-Friction record was visible before the closure attempt.
---
When a Smoother closure is triggered by smoother_mark_addressed, forbid the closure if an earlier targeted read_pending_friction call either failed with the historical unexpected-keyword TypeError or returned an empty pending result, and the enactment has no successful read_pending_friction result exposing a Friction id. This captures the determinable part of ungrounded_closure_attempt: an absent, failed, or empty targeted Friction read is not a grounded pending-Friction basis for an addressed mark or closure attempt. The invariant intentionally stays at the recorded-step level available to the predicate language; same-id matching remains a judgement concern unless the predicate language later gains argument comparison.
