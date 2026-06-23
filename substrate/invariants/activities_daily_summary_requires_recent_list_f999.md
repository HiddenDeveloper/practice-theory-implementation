---
id: activities_daily_summary_requires_recent_list_f999
name: Activities daily summary requires recent list grounding for Friction 999
status: active
trigger: garmin_get_daily_summary
mode: detect
friction_kind: practice_quality_affordance_coverage
forbid_when:
  not:
    step_exists:
      material_name: garmin_list_activities
message: activities_management invoked daily summary before recent_activity / garmin_list_activities;
  activity/rhythm or what-was-done work must expose garmin_list_activities first or
  stop at an explicit daily-snapshot/list-blocker limit.
---
Recovery after duplicate id activities_daily_summary_requires_recent_list: this persisted detector covers Friction 999's daily-summary branch without relying on unread existing invariant fields. For activities_management, a same-enactment daily summary read is not an acceptable substitute for the activity record when the work may characterize activity/rhythm, week pattern, completed-activity mix, gaps, streaks, cadence, route, GPS-shape, IWT, visualization, or what was done. When garmin_get_daily_summary appears, the earlier trail must already contain garmin_list_activities; otherwise the pass is interrupted and should recover by reading recent_activity / garmin_list_activities or by recording a concrete daily-snapshot/list-blocker limit before broader activity synthesis.
