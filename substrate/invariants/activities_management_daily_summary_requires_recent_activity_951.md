---
id: activities_management_daily_summary_requires_recent_activity_951
name: Activities management daily summary requires recent activity list
status: tombstoned
trigger: garmin_get_daily_summary
mode: detect
friction_kind: quality_affordance_coverage
forbid_when:
  not:
    step_exists:
      material_name: garmin_list_activities
message: In activities_management, garmin_get_daily_summary must not be used as the
  first evidence row for activity/rhythm, week-pattern, activity mix, gaps, streaks,
  cadence, or what-was-done work; invoke garmin_list_activities first or name a concrete
  list/auth/data/material blocker.
tombstoned_at: '2026-06-24T23:04:28+00:00'
tombstone_reason: migrated to an affordance precondition (phase 3)
---
Friction 951 confirmed that activities_management still begins some activity/rhythm-adjacent passes from daily_summary / garmin_get_daily_summary or stale daily-summary paths and then closes without the current activity list. This invariant makes the valid daily-summary ordering contract deterministic: garmin_get_daily_summary may not precede the activity-list grounding when the enactment is using Garmin evidence for activity-rhythm or what-was-done work.
