---
id: daily_summary
name: Daily summary only after current list
materials:
- garmin_list_activities
- garmin_get_daily_summary
---
For `activities_management`, this affordance is also downstream of the current activity-list gate when the work may answer activity/rhythm, what-was-done, week pattern, completed-activity mix, gaps, streaks, cadence, route, GPS-shape, IWT, visualization, or any broad activity context. Friction 1168 confirms four of five evaluated passes still reached adjacent activity detail or daily-summary surfaces, including stale daily/detail material attempts, without first invoking `recent_activity` / `garmin_list_activities`; a comparison pass showed the list path was reachable. Do not use `daily_summary` / `garmin_get_daily_summary` or a stale daily-summary alias as the first Garmin evidence row for those broader activity questions. The immediate next visible move must be `recent_activity` reaching `garmin_list_activities`, or a concrete list/auth/data/material blocker that explicitly confines the response to one daily wellness snapshot or one supplied isolated activity/date.
