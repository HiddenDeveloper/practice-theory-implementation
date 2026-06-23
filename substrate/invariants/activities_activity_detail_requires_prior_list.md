---
id: activities_activity_detail_requires_prior_list
name: Activity detail requires prior activity list
status: active
trigger: garmin_get_activity
mode: detect
friction_kind: practice_quality_affordance_coverage
forbid_when:
  not:
    step_exists:
      material_name: garmin_list_activities
message: activities_management reached activity detail before the current Garmin activity
  list. Invoke recent_activity / garmin_list_activities first, or record a concrete
  list/auth/data/material blocker before continuing.
---
For activities_management, `garmin_get_activity` is an adjacent detail surface. It is deterministically ungrounded when the same enactment has no earlier `garmin_list_activities` step. This invariant turns the repeatedly judged first-work-product contract from Frictions 912, 915, 922, 925, and 931 into a governed check for the activity-detail branch.
