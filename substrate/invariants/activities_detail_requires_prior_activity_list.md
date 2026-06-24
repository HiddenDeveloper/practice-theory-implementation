---
id: activities_detail_requires_prior_activity_list
name: Activities detail requires prior activity list
status: tombstoned
trigger: garmin_get_activity
mode: detect
friction_kind: quality_affordance_coverage
forbid_when:
  not:
    step_exists:
      material_name: garmin_list_activities
message: activities_management used activity detail before the current activity list;
  recover with recent_activity / garmin_list_activities before rhythm, cadence, gaps,
  streaks, completed-activity mix, or what-was-done synthesis.
tombstoned_at: '2026-06-24T23:04:28+00:00'
tombstone_reason: migrated to an affordance precondition (phase 3)
---
For activities_management, a closed enactment that reaches garmin_get_activity without any earlier garmin_list_activities row violates the deterministic portion of the recent-activity grounding contract surfaced by Friction 863. This invariant covers the valid detail material path; isolated-record judgement and stale-material redirects remain governed by the practice prose and evaluation layer.
