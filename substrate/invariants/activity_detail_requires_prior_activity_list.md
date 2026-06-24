---
id: activity_detail_requires_prior_activity_list
name: Activity detail requires prior activity list
status: tombstoned
trigger: garmin_get_activity
mode: detect
friction_kind: quality_affordance_coverage
forbid_when:
  not:
    step_exists:
      material_name: garmin_list_activities
message: activities_management invoked activity detail before the current-enactment
  activity list; run recent_activity / garmin_list_activities first or record a concrete
  list blocker before detail-based activity rhythm work.
tombstoned_at: '2026-06-24T23:04:28+00:00'
tombstone_reason: migrated to an affordance precondition (phase 3)
---
In activities_management, a `garmin_get_activity` step is not an acceptable first Garmin activity row for activity/rhythm-adjacent work. The trail must already contain `garmin_list_activities`, otherwise this deterministically raises the same coverage concern the Judge has repeatedly found by hand.
