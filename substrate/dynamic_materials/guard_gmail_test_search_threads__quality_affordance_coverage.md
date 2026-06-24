---
name: guard_gmail_test_search_threads__quality_affordance_coverage
input_schema: {}
implementation:
  kind: enactment_check
  trigger: gmail_test_search_threads
  friction_kind: quality_affordance_coverage
  message: Correspondent test-mailbox search after a live user Gmail search without
    any user thread retrieval leaves the reachable correspondence thread ungrounded.
  forbid_when:
    all:
    - step_exists:
        material_name: gmail_user_search_threads
        result_contains: threads
    - not:
        step_exists:
          material_name: gmail_user_get_thread
---
Migrated 2026-06-24T23:04:28+00:00 from 1 invariant(s): correspondent_live_search_before_test_search_requires_thread_retrieval_955.
