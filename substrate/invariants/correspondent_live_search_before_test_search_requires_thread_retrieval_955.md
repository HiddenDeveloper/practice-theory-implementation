---
id: correspondent_live_search_before_test_search_requires_thread_retrieval_955
name: Correspondent live search before test search requires thread retrieval
status: tombstoned
trigger: gmail_test_search_threads
mode: detect
friction_kind: quality_affordance_coverage
forbid_when:
  all:
  - step_exists:
      material_name: gmail_user_search_threads
      result_contains: threads
  - not:
      step_exists:
        material_name: gmail_user_get_thread
message: Correspondent test-mailbox search after a live user Gmail search without
  any user thread retrieval leaves the reachable correspondence thread ungrounded.
tombstoned_at: '2026-06-24T23:04:28+00:00'
tombstone_reason: migrated to an affordance precondition (phase 3)
---
Friction 955 confirmed the Judge is still hand-finding `grounds_correspondent_before_offering` when a Correspondent pass successfully reaches live Gmail search with thread ids and then moves into `gmail_test_search_threads` without retrieving the reachable user thread. This invariant covers that determinate material-presence contract only: if test-mailbox search is used after live user search, the enactment must also contain `gmail_user_get_thread` for the user thread. It leaves judgement about auth/configuration failures, ambiguous selection, and correspondence quality to the practice and Judge.
