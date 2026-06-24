---
name: guard_smoother_mark_addressed__non_persisted_amendment_marked_addressed
input_schema: {}
implementation:
  kind: enactment_check
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
---
Migrated 2026-06-24T23:04:28+00:00 from 1 invariant(s): no_close_on_unpersisted_amendment.
