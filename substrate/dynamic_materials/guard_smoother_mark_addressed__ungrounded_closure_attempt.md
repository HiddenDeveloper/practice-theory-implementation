---
name: guard_smoother_mark_addressed__ungrounded_closure_attempt
input_schema: {}
implementation:
  kind: enactment_check
  trigger: smoother_mark_addressed
  friction_kind: ungrounded_closure_attempt
  message: A Smoother enactment invoked mark_friction_addressed after an earlier targeted
    read_pending_friction call failed or returned an empty pending result, including
    the empty-basis/addressing variant where the terminal mark has no retrieved Friction
    content or observation_data as its basis; the concern still applies when that
    terminal mark itself fails because the Friction id is absent, no longer pending,
    or already addressed, leaving the failed closure attempt unresolved unless a later
    step records a disposition.
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
---
Migrated 2026-06-24T23:04:28+00:00 from 1 invariant(s): no_close_after_failed_targeted_friction_read.
