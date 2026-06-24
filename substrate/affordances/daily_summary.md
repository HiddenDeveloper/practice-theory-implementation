---
id: daily_summary
name: Daily summary only after current list
materials:
- garmin_list_activities
- garmin_get_daily_summary
---
Friction 1137 confirms the `activities_management` entry-gate failure remains live at the daily-summary surface: recent evaluated passes reached `daily_summary` / `garmin_get_daily_summary` or stale daily-summary material aliases without first showing `recent_activity` / `garmin_list_activities`, while a contrast pass showed the list path was reachable. Treat this affordance as downstream of the current activity list for any activity/rhythm, what-was-done, week-pattern, completed-activity mix, gaps, streaks, cadence, route, GPS-shape, IWT, visualization, or broad activity-context answer. If `daily_summary` would be the first Garmin row, the next visible move must be `recent_activity` reaching `garmin_list_activities`, or a concrete list/auth/data/material blocker that confines the response to a daily wellness snapshot and does not synthesize activity rhythm from the summary alone. A stale daily-summary material error is not recovery; after that error, recover to the projected `daily_summary` material only for an explicitly daily-snapshot answer, or to `recent_activity` / `garmin_list_activities` before broader activity synthesis.
