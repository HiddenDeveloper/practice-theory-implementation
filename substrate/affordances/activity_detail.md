---
id: activity_detail
name: Activity detail only after current list
materials:
- garmin_list_activities
- garmin_get_activity
---
Friction 1172 confirms the `activities_management` coverage miss remains live after the activity-detail warning itself was present: target enactment 175fd770-3f41-49cd-8ecb-2e23871fcd59 still opened with `activity_detail` / `garmin_get_activity` and no `recent_activity` / `garmin_list_activities` row. Treat this affordance selection as the interruption point. If the current enactment has not already listed recent activities, do not use `garmin_get_activity` as a first probe for rhythm, what-was-done, week-pattern, activity mix, gaps, streaks, cadence, route, GPS-shape, IWT, visualization, or broad context; the only valid next move is `recent_activity` / `garmin_list_activities`, or a concrete list/auth/data/material blocker that explicitly confines the response to one supplied isolated activity id/date.
