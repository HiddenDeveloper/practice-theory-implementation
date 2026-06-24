---
id: activity_detail
name: Activity detail only after current list
materials:
- garmin_list_activities
- garmin_get_activity
---
Friction 1064 confirms `activities_management` still drifts at the activity-detail entry point: in the latest evaluated window, direct `garmin_get_activity` and stale detail-material attempts appeared without the current `recent_activity` / `garmin_list_activities` row, while a nearby pass showed the list path was reachable. Treat this affordance as downstream evidence for broad activity, rhythm, week-pattern, completed-activity mix, gaps, streaks, cadence, route, GPS-shape, IWT, visualization, or what-was-done work. The first selected Garmin move for that work must be `recent_activity` reaching `garmin_list_activities`; if this affordance or a stale detail alias has already appeared first, the practice is interrupted and the only valid continuation is `garmin_list_activities` or a concrete list/auth/data/material blocker that explicitly confines the answer to the supplied isolated activity id/date.
