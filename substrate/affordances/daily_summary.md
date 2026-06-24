---
id: daily_summary
name: Daily summary only after current list
materials:
- garmin_list_activities
- garmin_get_daily_summary
---
Friction 1061 confirms the same `activities_management` quality miss remains live from the daily-summary side: in the evaluated window, direct daily-summary reads and stale daily-summary material attempts appeared without the current `recent_activity` / `garmin_list_activities` grounding row, while a neighboring pass showed the list path was reachable. For this affordance, a stale daily-summary material error is not a terminal stop and daily summary is not an acceptable opening Garmin move for broad activity, rhythm, week-pattern, completed-activity mix, gaps, streaks, cadence, route, GPS-shape, IWT, visualization, or what-was-done work. If `garmin_get_daily_summary`, `garmin_daily_summary`, or another stale summary alias appears before `garmin_list_activities`, the immediate next visible Garmin move must be `recent_activity` reaching `garmin_list_activities`, or a concrete list/auth/data/material blocker that explicitly confines the response to one daily wellness snapshot or the isolated evidence already read.
