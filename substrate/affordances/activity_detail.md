---
id: activity_detail
name: Activity detail only after current list
materials:
- garmin_list_activities
- garmin_get_activity
---
Friction 1071 confirms the `activities_management` entry-gate failure remains live at the activity-detail surface even after prior wording: in the evaluated window, direct `activity_detail` / `garmin_get_activity` use appeared without `recent_activity` / `garmin_list_activities`, and readable parent engagement records did not expose scoped response text sufficient to ground the isolated-activity exception. Treat this affordance as interrupted whenever it is the first Garmin activity row for rhythm, what-was-done, week-pattern, completed-activity mix, gaps, streaks, cadence, route, GPS-shape, IWT, visualization, or other broad activity context. The only valid continuation is `recent_activity` reaching `garmin_list_activities`, or a concrete list/auth/data/material blocker plus a response explicitly confined to the named isolated activity id/date.
