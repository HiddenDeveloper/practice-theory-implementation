---
id: daily_summary_requires_prior_recent_activity
name: Daily summary requires prior recent activity list
status: active
trigger: garmin_get_daily_summary
mode: detect
friction_kind: activity_record_grounding_missing
forbid_when:
  not:
    step_exists:
      material_name: garmin_list_activities
message: '`garmin_get_daily_summary` appeared before any current-enactment `garmin_list_activities`
  grounding step; daily wellness context cannot substitute for the recent activity
  record when the work concerns activity rhythm or what was done.'
---
Deterministic guard for the `activities_management` coverage contract repeatedly surfaced by Frictions 656, 661, 671, and 675: when an enactment reaches `garmin_get_daily_summary`, the trail must already contain `garmin_list_activities` as the activity-record grounding step. This encodes only the mechanically checkable part of the rule: direct daily summary before list is detected; judgement about isolated daily-snapshot exceptions or explicit list/auth/data/material blockers remains with the practice evaluation and Judge.
