---
id: activities_daily_summary_requires_prior_list
name: Daily summary requires prior activity list
status: tombstoned
trigger: garmin_get_daily_summary
mode: detect
friction_kind: practice_quality_affordance_coverage
forbid_when:
  not:
    step_exists:
      material_name: garmin_list_activities
message: activities_management reached daily summary before the current Garmin activity
  list. Invoke recent_activity / garmin_list_activities first, or record a concrete
  list/auth/data/material blocker before continuing.
tombstoned_at: '2026-06-24T23:04:28+00:00'
tombstone_reason: migrated to an affordance precondition (phase 3)
---
For activities_management, `garmin_get_daily_summary` is adjacent wellness context rather than the activity record. It is deterministically ungrounded for activity/rhythm or what-was-done work when the same enactment has no earlier `garmin_list_activities` step. This invariant turns the repeatedly judged first-work-product contract from Frictions 912, 915, 922, 925, and 931 into a governed check for the daily-summary branch.
