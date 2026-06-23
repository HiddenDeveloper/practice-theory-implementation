---
id: daily_summary
name: Daily summary only after current list
materials:
- garmin_list_activities
- garmin_get_daily_summary
---
Friction 987 confirms direct daily-summary or adjacent Garmin starts are still bypassing the activity-record gate in `activities_management`: in the evaluated window, daily-summary surfaces appeared without a same-enactment `recent_activity` / `garmin_list_activities` row, while comparator `359ef81c-27c6-4c5c-94fa-b740f4e93635` showed the list path was reachable. For any rhythm, week-pattern, completed-activity mix, gaps, streaks, cadence, route, GPS-shape, IWT, visualization, or what-was-done answer, a daily-summary-first start is an interrupted state: the immediate next visible move must be `garmin_list_activities` through `recent_activity` or this affordance, or a concrete list/auth/data/material blocker that keeps the answer limited to a daily wellness snapshot. Do not continue to activity detail, another adjacent Garmin surface, synthesis, final answer, or closure from daily summary alone.
