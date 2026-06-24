---
id: daily_summary
name: Daily summary only after current list
materials:
- garmin_list_activities
- garmin_get_daily_summary
preconditions:
- id: requires_garmin_list_activities_before_garmin_get_daily_summary
  name: requires garmin list activities before garmin get daily summary
  trigger: garmin_get_daily_summary
  friction_kind: quality_affordance_coverage
  message: activities_management used daily summary before the current activity list
    was visible; invoke recent_activity / garmin_list_activities before adjacent daily-summary
    work.
  forbid_when:
    not:
      step_exists:
        material_name: garmin_list_activities
  content: 'Migrated 2026-06-24T23:04:28+00:00 from 10 invariant(s): activities_daily_summary_requires_prior_activity_list,
    activities_daily_summary_requires_prior_list, activities_daily_summary_requires_recent_list….'
---
Friction 1172 confirms `daily_summary` is being used as an adjacent Garmin entry point in the same `activities_management` coverage failure: evaluated passes reached `garmin_get_daily_summary` or stale daily-summary material attempts without first grounding in `recent_activity` / `garmin_list_activities`. Treat this affordance as downstream for activity/rhythm, what-was-done, week-pattern, completed-activity mix, gaps, streaks, cadence, route, GPS-shape, IWT, visualization, or broad activity context. If the list row is absent, the next visible move must be `recent_activity` / `garmin_list_activities`, or a concrete list/auth/data/material blocker; any answer from this affordance alone must be explicitly confined to the isolated daily snapshot and must not synthesize broader activity rhythm or week pattern.
