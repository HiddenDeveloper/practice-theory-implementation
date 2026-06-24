---
id: daily_summary
name: Daily summary only after current list
materials:
- garmin_list_activities
- garmin_get_daily_summary
---
Friction 1108 confirms the `activities_management` entry-gate failure is still live at the daily-summary surface: recent evaluated passes again reached `daily_summary` / `garmin_get_daily_summary` or stale summary-material attempts without `recent_activity` / `garmin_list_activities`, while a nearby contrast pass showed the list path was reachable. Treat this affordance as interrupted whenever it would be the first Garmin activity row for activity/rhythm, what-was-done, week-pattern, completed-activity mix, gaps, streaks, cadence, route, GPS-shape, IWT, visualization, or other broad activity context. The only valid next move is `recent_activity` reaching `garmin_list_activities`, or a concrete list/auth/data/material blocker plus a response explicitly confined to one daily wellness snapshot or the isolated evidence already read. A stale summary-material error such as an unreached Garmin daily-summary alias is not a substitute for the list row; after such an error, recover to `recent_activity` / `garmin_list_activities` before any broader synthesis, verification, final answer, or closure.
