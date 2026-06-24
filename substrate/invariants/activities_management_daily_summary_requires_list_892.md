---
id: activities_management_daily_summary_requires_list_892
name: 'Activities management: daily summary requires current list for activity rhythm'
status: tombstoned
trigger: garmin_get_daily_summary
mode: detect
friction_kind: quality_affordance_coverage
forbid_when:
  not:
    step_exists:
      material_name: garmin_list_activities
message: In activities_management, garmin_get_daily_summary was used before the current
  activity list for activity/rhythm work. Invoke garmin_list_activities first, or
  record a concrete list/auth/data/material blocker and keep any answer limited to
  a daily wellness snapshot.
tombstoned_at: '2026-06-24T23:04:28+00:00'
tombstone_reason: migrated to an affordance precondition (phase 3)
---
Deterministic guard for Friction 892: daily-summary material use in activities_management must not substitute for the current activity record when the work is about activity rhythm, weekly pattern, completed-activity mix, gaps, streaks, cadence, or what was done. The invariant checks the determinate missing-list condition before garmin_get_daily_summary; judgement about purely isolated daily wellness snapshots remains with the practitioner/evaluator.
