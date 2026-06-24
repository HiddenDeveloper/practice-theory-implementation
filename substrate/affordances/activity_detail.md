---
id: activity_detail
name: Activity detail only after current list
materials:
- garmin_list_activities
- garmin_get_activity
---
Friction 1108 confirms the `activities_management` entry-gate failure is still live at the activity-detail surface: recent evaluated passes again reached `activity_detail` / `garmin_get_activity` or stale detail-material attempts without `recent_activity` / `garmin_list_activities`, while a nearby contrast pass showed the list path was reachable. Treat this affordance as interrupted whenever it would be the first Garmin activity row for activity/rhythm, what-was-done, week-pattern, completed-activity mix, gaps, streaks, cadence, route, GPS-shape, IWT, visualization, or other broad activity context. The only valid next move is `recent_activity` reaching `garmin_list_activities`, or a concrete list/auth/data/material blocker plus a response explicitly confined to the named isolated activity id/date. A stale detail-material error such as an unreached Garmin detail alias is not a substitute for the list row; after such an error, recover to `recent_activity` / `garmin_list_activities` before any broader synthesis, verification, final answer, or closure.
