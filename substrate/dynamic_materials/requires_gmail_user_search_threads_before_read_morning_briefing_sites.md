---
name: requires_gmail_user_search_threads_before_read_morning_briefing_sites
input_schema: {}
implementation:
  kind: enactment_check
  trigger: read_morning_briefing_sites
  friction_kind: quality_affordance_coverage
  message: Morning briefing site-list reads without an earlier unread Gmail search
    leave the recurring source baseline incomplete for quality coverage.
  forbid_when:
    not:
      step_exists:
        material_name: gmail_user_search_threads
---
Migrated 2026-06-24T23:04:28+00:00 from 2 invariant(s): friction_893_morning_briefing_gmail_before_site_list_quality, morning_briefing_gmail_before_site_list.
