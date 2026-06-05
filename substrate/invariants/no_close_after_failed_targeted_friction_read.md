---
id: no_close_after_failed_targeted_friction_read
name: No closure after failed targeted Friction read
status: active
trigger: smoother_mark_addressed
mode: detect
friction_kind: ungrounded_closure
forbid_when:
  all:
  - any_earlier_step_result_contains: unexpected keyword argument 'friction_id'
  - not:
      step_exists:
        affordance_id: read_pending_friction
        result_contains: '"id"'
message: A Smoother enactment invoked mark_friction_addressed after a targeted read_pending_friction
  failure and no later successful pending-Friction record was visible before closure.
---
When a Smoother closure is triggered by smoother_mark_addressed, forbid the closure if an earlier targeted read_pending_friction call failed with the historical unexpected-keyword TypeError and the enactment has no earlier successful read_pending_friction result exposing a Friction id. This makes the determinable part of ungrounded_closure automatic: a failed targeted read remains a blocker unless a later successful targeted Friction record is visible before the addressed mark.
