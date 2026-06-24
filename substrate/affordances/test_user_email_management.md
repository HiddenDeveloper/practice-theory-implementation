---
id: test_user_email_management
name: Test user email management
materials:
- gmail_test_search_threads
- gmail_test_get_thread
- gmail_test_list_drafts
- gmail_test_create_draft
- gmail_test_update_draft
- gmail_test_delete_draft
- gmail_test_send_draft
- gmail_user_search_threads
- gmail_user_get_thread
- gmail_user_list_drafts
preconditions:
- id: guard_gmail_test_search_threads__quality_affordance_coverage
  name: guard gmail test search threads  quality affordance coverage
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
  content: 'Migrated 2026-06-24T23:04:28+00:00 from 1 invariant(s): correspondent_live_search_before_test_search_requires_thread_retrieval_955.'
---
Exercise the Gmail material surface against the test mailbox before using production correspondence. The test mailbox can search, read, draft, delete, and send; the user mailbox is read-only here for round-trip verification.
