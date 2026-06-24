---
id: activities_daily_summary_requires_recent_list
name: Daily summary requires current activity list
status: tombstoned
trigger: garmin_get_daily_summary
mode: detect
friction_kind: quality_affordance_coverage_gap
forbid_when:
  not:
    step_exists:
      material_name: garmin_list_activities
message: activities_management invoked garmin_get_daily_summary before garmin_list_activities;
  recover by listing recent activities or record a concrete list/auth/data/material
  blocker before activity-rhythm synthesis.
tombstoned_at: '2026-06-24T23:04:28+00:00'
tombstone_reason: migrated to an affordance precondition (phase 3)
---
Friction 872 confirmed repeated activities_management passes used daily-summary surfaces without the required current activity-list grounding. When garmin_get_daily_summary appears without an earlier garmin_list_activities row in the same enactment, raise an auto-resolved quality_affordance_coverage_gap so the missing entry row is detected deterministically rather than by another manual quality-window review.
