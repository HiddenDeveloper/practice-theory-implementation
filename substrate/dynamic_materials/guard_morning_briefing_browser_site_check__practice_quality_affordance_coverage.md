---
name: guard_morning_briefing_browser_site_check__practice_quality_affordance_coverage
input_schema: {}
implementation:
  kind: enactment_check
  trigger: morning_briefing_browser_site_check
  friction_kind: practice_quality_affordance_coverage
  message: Morning briefing browser site checks require earlier unread Gmail and configured
    site-list reads, or direct checks are substituting for the required source-gathering
    gate.
  forbid_when:
    any:
    - not:
        step_exists:
          material_name: gmail_user_search_threads
    - not:
        step_exists:
          material_name: read_morning_briefing_sites
---
Migrated 2026-06-24T23:04:28+00:00 from 2 invariant(s): morning_briefing_source_gate_before_site_check, morning_briefing_sources_before_site_check.
