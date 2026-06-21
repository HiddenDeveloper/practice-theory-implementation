---
id: activities_list_before_activity_detail
name: Activities Management lists activities before activity detail
status: active
trigger: garmin_get_activity
mode: detect
friction_kind: quality_affordance_coverage_gap
forbid_when:
  not:
    step_exists:
      material_name: garmin_list_activities
message: activities_management activity-detail work reached garmin_get_activity before
  any current-enactment garmin_list_activities row; recover by making recent_activity
  / garmin_list_activities the next visible move or record a concrete list blocker
  before synthesis.
---
For activities-management activity-detail passes, a garmin_get_activity row without any earlier garmin_list_activities row is the deterministic bypass the Judge has repeatedly re-found by hand in Frictions 824, 825, 833, 837, 841, 845, 850, and 855. This invariant detects that ordering miss at the adjacent detail material instead of waiting for another quality-evaluation Friction.
