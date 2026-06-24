---
id: activity_detail_requires_recent_activity_list
name: Activity detail requires current activity list
status: tombstoned
trigger: garmin_get_activity
mode: detect
friction_kind: quality_affordance_coverage
forbid_when:
  not:
    step_exists:
      material_name: garmin_list_activities
message: In activities_management-style activity/rhythm work, garmin_get_activity
  must not appear before a current garmin_list_activities row unless the answer is
  explicitly isolated to one supplied activity. Backfill recent_activity / garmin_list_activities
  or record a concrete list/auth/data/material blocker before using activity detail
  for broader activity context.
tombstoned_at: '2026-06-24T23:04:28+00:00'
tombstone_reason: migrated to an affordance precondition (phase 3)
---
Deterministic guard for the recurring reads_activity_record_before_describing_rhythm miss: when activity detail is reached, the trail must already expose garmin_list_activities, because remembered ids, stale alias recovery, prior trail context, or daily-summary context do not ground a broad activity/rhythm answer.
