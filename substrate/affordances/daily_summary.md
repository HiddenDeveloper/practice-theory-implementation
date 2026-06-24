---
id: daily_summary
name: Daily summary only after current list
materials:
- garmin_list_activities
- garmin_get_daily_summary
check_materials:
- requires_garmin_list_activities_before_garmin_get_daily_summary
---
Friction 1172 confirms `daily_summary` is being used as an adjacent Garmin entry point in the same `activities_management` coverage failure: evaluated passes reached `garmin_get_daily_summary` or stale daily-summary material attempts without first grounding in `recent_activity` / `garmin_list_activities`. Treat this affordance as downstream for activity/rhythm, what-was-done, week-pattern, completed-activity mix, gaps, streaks, cadence, route, GPS-shape, IWT, visualization, or broad activity context. If the list row is absent, the next visible move must be `recent_activity` / `garmin_list_activities`, or a concrete list/auth/data/material blocker; any answer from this affordance alone must be explicitly confined to the isolated daily snapshot and must not synthesize broader activity rhythm or week pattern.
