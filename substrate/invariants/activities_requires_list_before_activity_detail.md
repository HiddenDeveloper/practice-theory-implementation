---
id: activities_requires_list_before_activity_detail
name: Activities detail requires current activity list first
status: tombstoned
trigger: garmin_get_activity
mode: detect
friction_kind: practice_quality_affordance_coverage
forbid_when:
  not:
    step_exists:
      material_name: garmin_list_activities
message: activities_management used activity detail before the current activity list
  was visible; invoke recent_activity / garmin_list_activities before adjacent activity-detail
  work.
tombstoned_at: '2026-06-24T23:04:28+00:00'
tombstone_reason: migrated to an affordance precondition (phase 3)
---
For activities_management quality, a closed enactment that reaches `garmin_get_activity` without any `garmin_list_activities` step deterministically violates the activity-record entry gate measured by `reads_activity_record_before_describing_rhythm`. This invariant covers the detail-read half of Friction 741's repeated hand-judged pattern.

Friction 829 confirms the same practice-quality coverage failure remained live in target enactment `175fd770-3f41-49cd-8ecb-2e23871fcd59`, where `activity_detail` / `garmin_get_activity` appeared without `garmin_list_activities`, and in a nearby evaluated window where adjacent Garmin detail, daily-summary, and stale-material starts repeatedly missed the activity-list row. Keep the mechanically checkable no-list detail case routed as `practice_quality_affordance_coverage` so future passes do not require the Judge to rediscover this exact `garmin_get_activity` branch by hand; judgement remains responsible for scope exceptions, blockers, and broader synthesis quality.
