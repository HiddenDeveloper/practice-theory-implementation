---
id: daily_summary_requires_recent_activity_list_for_activity_rhythm
name: Daily summary requires activity list for rhythm work
status: tombstoned
trigger: garmin_get_daily_summary
mode: detect
friction_kind: quality_affordance_coverage
forbid_when:
  not:
    step_exists:
      material_name: garmin_list_activities
message: For activities_management activity/rhythm, week-pattern, activity mix, gaps,
  streaks, cadence, or what-was-done work, garmin_get_daily_summary must not appear
  before garmin_list_activities unless the answer is explicitly confined to one daily
  wellness snapshot. Backfill recent_activity / garmin_list_activities or record a
  concrete list/auth/data/material blocker before broader synthesis.
tombstoned_at: '2026-06-24T23:04:28+00:00'
tombstone_reason: migrated to an affordance precondition (phase 3)
---
Deterministic guard for the recurring reads_activity_record_before_describing_rhythm miss on daily-summary starts: daily summary is not a substitute for the current activity list when the pass may characterize activity rhythm or what was done.
