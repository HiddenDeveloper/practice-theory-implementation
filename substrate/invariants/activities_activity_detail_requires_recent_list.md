---
id: activities_activity_detail_requires_recent_list
name: Activities detail requires recent list grounding
status: tombstoned
trigger: garmin_get_activity
mode: detect
friction_kind: practice_quality_affordance_coverage
forbid_when:
  not:
    step_exists:
      material_name: garmin_list_activities
message: activities_management invoked activity detail before recent_activity / garmin_list_activities;
  broad activity/rhythm work must expose garmin_list_activities first or stop at an
  explicit narrow-record/list-blocker limit.
tombstoned_at: '2026-06-24T23:04:28+00:00'
tombstone_reason: migrated to an affordance precondition (phase 3)
---
For activities_management, a same-enactment activity detail read is not an acceptable first grounding move for activity/rhythm, week-pattern, completed-activity mix, gaps, streaks, cadence, route, GPS-shape, IWT, visualization, or what-was-done work. When garmin_get_activity appears, the earlier trail must already contain garmin_list_activities; otherwise the pass is interrupted and should recover by reading recent_activity / garmin_list_activities or by recording a concrete narrow isolated-record/list-blocker limit before broader synthesis.
