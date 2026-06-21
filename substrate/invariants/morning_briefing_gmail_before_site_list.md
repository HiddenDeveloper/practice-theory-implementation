---
id: morning_briefing_gmail_before_site_list
name: Morning briefing Gmail before site list
status: active
trigger: read_morning_briefing_sites
mode: detect
friction_kind: quality_affordance_coverage
forbid_when:
  not:
    step_exists:
      material_name: gmail_user_search_threads
message: Morning briefing site-list reads must come after the unread Gmail search,
  or the practice has skipped the required unread-mail grounding at the start of the
  briefing.
---
For `morning_briefing`, the configured recurring site-list read `read_morning_briefing_sites` is not the first source-gathering move. It may only occur after the enactment has already recorded `gmail_user_search_threads` for unread mail. Friction 827 showed this same determinable source-order miss was still being hand-emitted as `quality_affordance_coverage` when a briefing read the site list without unread Gmail. This invariant keeps the existing material-presence predicate and retargets the routed Friction kind to the quality signal the Judge is actually finding, so site-list-only starts are detected deterministically instead of rediscovered by hand.
