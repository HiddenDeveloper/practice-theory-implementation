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
check_materials:
- guard_gmail_test_search_threads__quality_affordance_coverage
---
Exercise the Gmail material surface against the test mailbox before using production correspondence. The test mailbox can search, read, draft, delete, and send; the user mailbox is read-only here for round-trip verification.
