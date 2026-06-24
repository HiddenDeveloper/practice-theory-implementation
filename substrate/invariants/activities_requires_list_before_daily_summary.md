---
id: activities_requires_list_before_daily_summary
name: Activities daily summary requires current activity list first
status: tombstoned
trigger: garmin_get_daily_summary
mode: detect
friction_kind: practice_quality_affordance_coverage
forbid_when:
  not:
    step_exists:
      material_name: garmin_list_activities
message: activities_management used daily summary before the current activity list
  was visible; invoke recent_activity / garmin_list_activities before adjacent daily-summary
  work.
tombstoned_at: '2026-06-24T23:04:28+00:00'
tombstone_reason: migrated to an affordance precondition (phase 3)
---
For activities_management quality, a closed enactment that reaches `garmin_get_daily_summary` without any earlier `garmin_list_activities` step deterministically violates the activity-record entry gate measured by `reads_activity_record_before_describing_rhythm`. This invariant covers the daily-summary half of Friction 741's repeated hand-judged pattern; judgement remains responsible for scope exceptions and broader synthesis quality.
