---
id: activity_detail
name: Activity detail only after current list
materials:
- garmin_list_activities
- garmin_get_activity
check_materials:
- requires_garmin_list_activities_before_garmin_get_activity
---
Read one activity's detail (`garmin_get_activity`) — a downstream read, not a first probe. If the current enactment has not already listed recent activities, do not use `garmin_get_activity` to answer rhythm, what-was-done, week-pattern, activity mix, gaps, streaks, cadence, route, GPS-shape, IWT, visualization, or broad activity context: the next move must be `recent_activity` / `garmin_list_activities`, or a concrete list/auth/data/material blocker that confines the response to one supplied isolated activity id/date.
