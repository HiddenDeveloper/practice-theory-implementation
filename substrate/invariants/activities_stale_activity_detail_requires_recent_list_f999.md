---
id: activities_stale_activity_detail_requires_recent_list_f999
name: Stale activity detail alias requires recent list grounding
status: active
trigger: garmin_get_activity_detail
mode: detect
friction_kind: practice_quality_affordance_coverage
forbid_when:
  not:
    step_exists:
      material_name: garmin_list_activities
message: activities_management attempted stale activity-detail material before recent_activity
  / garmin_list_activities; recover through garmin_list_activities or stop at a concrete
  material/list blocker.
---
Friction 999 counted stale activity-detail material attempts as the same activity-record gate miss. When garmin_get_activity_detail appears in an activities_management trail, the earlier trail must already contain garmin_list_activities; otherwise the pass is interrupted and should recover through recent_activity / garmin_list_activities or name a concrete stale-material/list blocker before any broader activity/rhythm synthesis.
