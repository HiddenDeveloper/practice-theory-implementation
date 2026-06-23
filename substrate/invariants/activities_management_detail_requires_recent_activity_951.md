---
id: activities_management_detail_requires_recent_activity_951
name: Activities management detail requires recent activity list
status: active
trigger: garmin_get_activity
mode: detect
friction_kind: quality_affordance_coverage
forbid_when:
  not:
    step_exists:
      material_name: garmin_list_activities
message: In activities_management, garmin_get_activity must not be used as the first
  Garmin activity-context move for rhythm, week-pattern, completed-activity mix, gaps,
  streaks, cadence, or what-was-done work; invoke garmin_list_activities first or
  name a concrete list/auth/data/material blocker.
---
Friction 951 confirmed that activities_management continues to bypass the required current activity list by entering activity_detail / garmin_get_activity first. This invariant makes the determinable ordering contract visible: any enactment that reaches garmin_get_activity without an earlier garmin_list_activities row is treated as quality_affordance_coverage unless the practitioner has stayed inside a separately grounded isolated-record exception in practice prose.
