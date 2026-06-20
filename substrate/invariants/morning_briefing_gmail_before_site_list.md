---
id: morning_briefing_gmail_before_site_list
name: Morning briefing Gmail before site list
status: active
trigger: read_morning_briefing_sites
mode: detect
friction_kind: practice_quality_affordance_coverage
forbid_when:
  not:
    step_exists:
      material_name: gmail_user_search_threads
message: Morning briefing site-list reads must come after the unread Gmail search,
  or the practice has skipped the required unread-mail grounding at the start of the
  briefing.
---
For `morning_briefing`, the configured recurring site-list read `read_morning_briefing_sites` is not the first source-gathering move. It may only occur after the enactment has already recorded `gmail_user_search_threads` for unread mail. This governed invariant makes deterministic the start-of-pass order already stated in `rule_morning_briefing_unread_first` and directly addresses Friction 526's repeated finding that unread email was not read in any evaluated morning briefing pass. It checks only the material-presence order; judgement about Gmail access gaps, account coverage, and the quality of the returned mail remains with the practice and Judge.
