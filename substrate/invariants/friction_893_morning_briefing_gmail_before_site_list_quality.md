---
id: friction_893_morning_briefing_gmail_before_site_list_quality
name: Morning briefing site list requires Gmail baseline for quality coverage
status: active
trigger: read_morning_briefing_sites
mode: detect
friction_kind: quality_affordance_coverage
forbid_when:
  not:
    step_exists:
      material_name: gmail_user_search_threads
message: Morning briefing site-list reads without an earlier unread Gmail search leave
  the recurring source baseline incomplete for quality coverage.
---
Friction 893 confirmed the Judge is still hand-finding `quality_affordance_coverage` when `morning_briefing` reaches the configured site-list material `read_morning_briefing_sites` while `gmail_user_search_threads` for unread mail is absent and unblocked. This invariant covers only that determinable material-presence contract: before a site-list row, the same enactment must already contain the unread Gmail search. It leaves judgement about Gmail blockers, source quality, and passes that never reach the site-list trigger to the practice and Judge.
