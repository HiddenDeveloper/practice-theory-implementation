---
id: mark_friction_addressed
name: Mark Friction addressed
materials:
- smoother_mark_addressed
preconditions:
- id: guard_smoother_mark_addressed__unavailable_affordance_invocation
  name: guard smoother mark addressed  unavailable affordance invocation
  trigger: smoother_mark_addressed
  friction_kind: unavailable_affordance_invocation
  message: 'A Smoother enactment marked Friction addressed after an earlier step recorded
    KeyError: no affordance in practice ''smoother'', meaning it reached outside the
    affordances projected by the active Smoother bundle.'
  forbid_when:
    all:
    - any_earlier_step_result_contains: 'KeyError: no affordance'
    - any_earlier_step_result_contains: in practice 'smoother'
  content: 'Migrated 2026-06-24T23:04:28+00:00 from 1 invariant(s): no_unprojected_smoother_affordance_invocation.'
- id: guard_smoother_mark_addressed__non_persisted_amendment_marked_addressed
  name: guard smoother mark addressed  non persisted amendment marked addressed
  trigger: smoother_mark_addressed
  friction_kind: non_persisted_amendment_marked_addressed
  message: This enactment marked a Friction addressed after an amendment reported
    persisted=false, and no earlier persisted amendment surface was visible before
    the addressed mark; the closure appears to rest only on a change that did not
    save.
  forbid_when:
    all:
    - any_earlier_step_result_contains: '"persisted": false'
    - not:
        any:
        - any_earlier_step_result_contains: '"persisted": true'
        - any_earlier_step_result_contains: '"affordance"'
        - any_earlier_step_result_contains: '"bundle"'
        - any_earlier_step_result_contains: '"pool"'
        - any_earlier_step_result_contains: '"invariant"'
  content: 'Migrated 2026-06-24T23:04:28+00:00 from 1 invariant(s): no_close_on_unpersisted_amendment.'
- id: guard_smoother_mark_addressed__ungrounded_closure_attempt
  name: guard smoother mark addressed  ungrounded closure attempt
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
  content: 'Migrated 2026-06-24T23:04:28+00:00 from 1 invariant(s): no_close_after_failed_targeted_friction_read.'
---
Mark a Friction observation as addressed by this Smoother enactment. For dispatched Smoother work, invoke this only after the same enactment has recorded a targeted read of that friction_id, so the readable trail exposes the Friction content and observation_data as the resolution basis; a truncated batch read is not enough. The mark must also carry a concise rationale: after a substrate amendment, name the persisted amended id or surface; when no mutation is made, name the explicit no-mutation, already-addressed, absent/no-longer-pending, failed-persistence, or blocker basis. Do not use this affordance for inspection-only closure with no visible judgement basis. (The specific case of closing after an amendment that reported persisted=false is now enforced deterministically by the governed invariant `no_close_on_unpersisted_amendment` — detected and resolved without a Judge dispatch — so this prose need not be policed by hand.)
