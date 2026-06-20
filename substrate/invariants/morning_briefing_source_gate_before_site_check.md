---
id: morning_briefing_source_gate_before_site_check
name: Morning briefing source gate before site check
status: active
trigger: morning_briefing_browser_site_check
mode: detect
friction_kind: practice_quality_affordance_coverage
forbid_when:
  any:
  - not:
      step_exists:
        material_name: gmail_user_search_threads
  - not:
      step_exists:
        material_name: read_morning_briefing_sites
message: Morning briefing browser site checks require earlier unread Gmail search
  and configured morning site-list reads, or the practice has skipped its required
  recurring source-gathering gate.
---
For `morning_briefing`, the one-off browser site-check material `morning_briefing_browser_site_check` may only run after the enactment has already recorded both recurring source-gathering reads named by the practice-quality signal: `gmail_user_search_threads` for unread mail and `read_morning_briefing_sites` for the configured recurring site list. Friction 608 showed the remaining coverage failure was not only final assembly: two of the evaluated runs reached browser site checking while both recurring source reads were absent, and the third read the configured site list without unread Gmail. This invariant makes deterministic the source-gate-before-site-work contract already stated in `rule_morning_briefing_unread_first` and the `assemble_morning_briefing` affordance. It checks only material-presence facts before browser site checking; judgement about Gmail access blockers, site-list configuration gaps, source contents, and briefing quality remains with the practice and Judge.
