---
name: requires_garmin_list_activities_before_garmin_get_activity
input_schema: {}
implementation:
  kind: enactment_check
  trigger: garmin_get_activity
  friction_kind: quality_affordance_coverage
  message: activities_management used activity detail before the current activity
    list was visible; invoke recent_activity / garmin_list_activities before adjacent
    activity-detail work.
  forbid_when:
    not:
      step_exists:
        material_name: garmin_list_activities
---
Migrated 2026-06-24T23:04:28+00:00 from 11 invariant(s): activities_activity_detail_requires_prior_list, activities_activity_detail_requires_recent_list, activities_detail_requires_prior_activity_list….
