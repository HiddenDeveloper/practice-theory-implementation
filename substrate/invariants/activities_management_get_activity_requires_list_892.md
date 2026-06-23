---
id: activities_management_get_activity_requires_list_892
name: 'Activities management: activity detail requires current list'
status: active
trigger: garmin_get_activity
mode: detect
friction_kind: quality_affordance_coverage
forbid_when:
  not:
    step_exists:
      material_name: garmin_list_activities
message: In activities_management, garmin_get_activity was used before the current
  activity list. Invoke garmin_list_activities first, or record a concrete list/auth/data/material
  blocker and keep the answer limited to an isolated supplied activity id/date.
---
Deterministic guard for Friction 892: activity-detail material use in activities_management must be preceded by garmin_list_activities so rhythm, weekly-pattern, activity-mix, gap, streak, cadence, or what-was-done work is grounded in the current activity record. The invariant only checks the determinate missing-list condition; judgement about genuine isolated-id/date exceptions remains with the practitioner/evaluator.
