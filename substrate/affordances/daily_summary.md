---
id: daily_summary
name: Daily summary only after current list
materials:
- garmin_list_activities
- garmin_get_daily_summary
---
Friction 1064 confirms `activities_management` still drifts at the daily-summary entry point: in the latest evaluated window, direct daily-summary reads and stale summary-material attempts appeared without the current `recent_activity` / `garmin_list_activities` row, while a nearby pass showed the list path was reachable. Treat this affordance as downstream evidence for broad activity, rhythm, week-pattern, completed-activity mix, gaps, streaks, cadence, route, GPS-shape, IWT, visualization, or what-was-done work. The first selected Garmin move for that work must be `recent_activity` reaching `garmin_list_activities`; if this affordance or a stale summary alias has already appeared first, the practice is interrupted and the only valid continuation is `garmin_list_activities` or a concrete list/auth/data/material blocker that explicitly confines the answer to one daily wellness snapshot or the isolated evidence already read.
