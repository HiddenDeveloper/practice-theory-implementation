---
id: daily_summary
name: Daily summary only after current list
materials:
- garmin_list_activities
- garmin_get_daily_summary
---
Friction 1071 confirms the `activities_management` entry-gate failure remains live at the daily-summary surface even after prior wording: in the evaluated window, direct `daily_summary` / `garmin_get_daily_summary` use and stale summary-material attempts appeared without `recent_activity` / `garmin_list_activities`, and readable parent engagement records did not expose scoped response text sufficient to ground the daily-snapshot exception. Treat this affordance as interrupted whenever it is the first Garmin activity row for rhythm, what-was-done, week-pattern, completed-activity mix, gaps, streaks, cadence, route, GPS-shape, IWT, visualization, or other broad activity context. The only valid continuation is `recent_activity` reaching `garmin_list_activities`, or a concrete list/auth/data/material blocker plus a response explicitly confined to one daily wellness snapshot or the isolated evidence already read.
