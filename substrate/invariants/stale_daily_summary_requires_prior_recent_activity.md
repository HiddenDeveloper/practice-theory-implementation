---
id: stale_daily_summary_requires_prior_recent_activity
name: Stale daily-summary reach requires prior recent activity list
status: active
trigger: garmin_daily_summary
mode: detect
friction_kind: practice_quality_affordance_coverage
forbid_when:
  not:
    step_exists:
      material_name: garmin_list_activities
message: '`garmin_daily_summary` appeared without any current-enactment `garmin_list_activities`
  grounding step; stale daily-summary recovery does not substitute for the recent
  activity record before rhythm or what-was-done work.'
---
Deterministic guard for the stale daily-summary branch of the `activities_management` practice-quality coverage contract named by Frictions 716, 726, and 733. Existing guards cover valid `garmin_get_daily_summary` reads and invalid stale-material reaches separately; this guard covers the mechanically checkable coverage fact when a stale `garmin_daily_summary` attempt occurs before any `garmin_list_activities` activity-record grounding and routes it as `practice_quality_affordance_coverage`. Judgement about isolated daily-snapshot exceptions or explicit list/auth/data/material blockers remains with practice evaluation and the Judge.
