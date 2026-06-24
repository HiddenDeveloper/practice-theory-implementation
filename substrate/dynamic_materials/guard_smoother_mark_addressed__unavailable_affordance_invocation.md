---
name: guard_smoother_mark_addressed__unavailable_affordance_invocation
input_schema: {}
implementation:
  kind: enactment_check
  trigger: smoother_mark_addressed
  friction_kind: unavailable_affordance_invocation
  message: 'A Smoother enactment marked Friction addressed after an earlier step recorded
    KeyError: no affordance in practice ''smoother'', meaning it reached outside the
    affordances projected by the active Smoother bundle.'
  forbid_when:
    all:
    - any_earlier_step_result_contains: 'KeyError: no affordance'
    - any_earlier_step_result_contains: in practice 'smoother'
---
Migrated 2026-06-24T23:04:28+00:00 from 1 invariant(s): no_unprojected_smoother_affordance_invocation.
