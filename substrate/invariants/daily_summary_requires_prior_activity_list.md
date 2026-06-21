---
id: daily_summary_requires_prior_activity_list
name: Daily summary requires prior activity list
status: active
trigger: garmin_get_daily_summary
mode: detect
friction_kind: quality_affordance_coverage
forbid_when:
  not:
    step_exists:
      material_name: garmin_list_activities
message: activities_management invoked daily summary before the current-enactment
  activity list; run recent_activity / garmin_list_activities first or record a concrete
  list blocker before daily-summary-supported activity rhythm work.
---
In activities_management, a `garmin_get_daily_summary` step is not an acceptable substitute for the current activity record when the pass may describe activity rhythm, weekly pattern, completed-activity mix, gaps, streaks, cadence, or what was done. The trail must already contain `garmin_list_activities`, otherwise this deterministically raises the same coverage concern the Judge has repeatedly found by hand.
