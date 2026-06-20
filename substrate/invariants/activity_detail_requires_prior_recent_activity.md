---
id: activity_detail_requires_prior_recent_activity
name: Activity detail requires prior recent activity list
status: active
trigger: garmin_get_activity
mode: detect
friction_kind: quality_affordance_coverage
forbid_when:
  not:
    step_exists:
      material_name: garmin_list_activities
message: '`garmin_get_activity` appeared before any current-enactment `garmin_list_activities`
  grounding step; activity detail is a supplement, not the entry record for recent
  activity rhythm or what was done.'
---
Deterministic guard for the `activities_management` quality coverage contract repeatedly surfaced by Frictions 656, 661, 671, 675, and 726: when an enactment reaches `garmin_get_activity`, the trail must already contain `garmin_list_activities` as the activity-record grounding step. This encodes only the mechanically checkable part of the rule: direct detail before list is detected and routed as `quality_affordance_coverage`; judgement about isolated-record exceptions or explicit list/auth/data/material blockers remains with the practice evaluation and Judge.
