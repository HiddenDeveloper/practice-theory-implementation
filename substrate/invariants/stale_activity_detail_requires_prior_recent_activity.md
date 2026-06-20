---
id: stale_activity_detail_requires_prior_recent_activity
name: Stale activity-detail reach requires prior recent activity list
status: active
trigger: garmin_get_activity_detail
mode: detect
friction_kind: quality_affordance_coverage
forbid_when:
  not:
    step_exists:
      material_name: garmin_list_activities
message: '`garmin_get_activity_detail` appeared without any current-enactment `garmin_list_activities`
  grounding step; stale activity-detail recovery does not substitute for the recent
  activity record before rhythm or what-was-done work.'
---
Deterministic guard for the stale activity-detail branch of the `activities_management` quality coverage contract named by Frictions 716 and 726. Existing guards cover valid `garmin_get_activity` detail reads and invalid stale-material reaches separately; this guard covers the mechanically checkable coverage fact when a stale `garmin_get_activity_detail` attempt occurs before any `garmin_list_activities` activity-record grounding and routes it as `quality_affordance_coverage`. Judgement about isolated-record exceptions or explicit list/auth/data/material blockers remains with practice evaluation and the Judge.
