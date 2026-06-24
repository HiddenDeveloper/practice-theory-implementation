---
id: activity_detail
name: Activity detail only after current list
materials:
- garmin_list_activities
- garmin_get_activity
---
Friction 1061 confirms the same `activities_management` quality miss remains live from the detail side: in the evaluated window, direct `garmin_get_activity` and stale detail material attempts appeared without the current `recent_activity` / `garmin_list_activities` grounding row, even though a neighboring pass showed the list path was reachable. For this affordance, a stale detail-material error is not a terminal stop and direct detail is not an acceptable opening move for broad activity, rhythm, week-pattern, completed-activity mix, gaps, streaks, cadence, route, GPS-shape, IWT, visualization, or what-was-done work. If `garmin_get_activity` or a stale detail alias appears before `garmin_list_activities`, the immediate next visible Garmin move must be `recent_activity` reaching `garmin_list_activities`, or a concrete list/auth/data/material blocker that explicitly confines the response to the supplied isolated activity id/date.
