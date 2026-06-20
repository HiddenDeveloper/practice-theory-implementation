---
id: activities_requires_list_before_activity_detail
name: Activities detail requires current activity list first
status: active
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
---
For activities_management quality, a closed enactment that reaches `garmin_get_activity` without any earlier `garmin_list_activities` step deterministically violates the activity-record entry gate measured by `reads_activity_record_before_describing_rhythm`. This invariant covers the detail-read half of Friction 741's repeated hand-judged pattern; judgement remains responsible for scope exceptions and broader synthesis quality.
