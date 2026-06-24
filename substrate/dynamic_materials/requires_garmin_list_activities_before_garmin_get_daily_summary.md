---
name: requires_garmin_list_activities_before_garmin_get_daily_summary
input_schema: {}
implementation:
  kind: enactment_check
  trigger: garmin_get_daily_summary
  friction_kind: quality_affordance_coverage
  message: activities_management used daily summary before the current activity list
    was visible; invoke recent_activity / garmin_list_activities before adjacent daily-summary
    work.
  forbid_when:
    not:
      step_exists:
        material_name: garmin_list_activities
---
Migrated 2026-06-24T23:04:28+00:00 from 10 invariant(s): activities_daily_summary_requires_prior_activity_list, activities_daily_summary_requires_prior_list, activities_daily_summary_requires_recent_list….
