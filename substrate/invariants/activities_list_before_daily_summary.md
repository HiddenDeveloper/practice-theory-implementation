---
id: activities_list_before_daily_summary
name: Activities Management lists activities before daily summary
status: active
trigger: garmin_get_daily_summary
mode: detect
friction_kind: quality_affordance_coverage_gap
forbid_when:
  not:
    step_exists:
      material_name: garmin_list_activities
message: activities_management daily-summary work reached garmin_get_daily_summary
  before any current-enactment garmin_list_activities row; recover by making recent_activity
  / garmin_list_activities the next visible move or record a concrete list blocker
  before synthesis.
---
For activities-management daily-summary passes that feed activity/rhythm or what-was-done synthesis, a garmin_get_daily_summary row without any earlier garmin_list_activities row is the deterministic bypass the Judge has repeatedly re-found by hand in Frictions 824, 825, 833, 837, 841, 845, 850, and 855. This invariant detects that adjacent daily-summary ordering miss instead of waiting for another quality-evaluation Friction.
