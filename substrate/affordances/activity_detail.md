---
id: activity_detail
name: Activity detail only after current list
materials:
- garmin_list_activities
- garmin_get_activity
---
Friction 1154 confirms the `activities_management` quality signal `reads_activity_record_before_describing_rhythm` is still failing in the fresh five-enactment window: the target enactment `175fd770-3f41-49cd-8ecb-2e23871fcd59` invoked `activity_detail` / `garmin_get_activity` without first invoking `recent_activity` / `garmin_list_activities`, and another miss reached a stale detail-material alias instead of recovering to the list. Treat this affordance as a blocked downstream surface whenever the current enactment has not yet shown `recent_activity` reaching `garmin_list_activities` and the work may describe activity rhythm, what was done, week pattern, completed-activity mix, gaps, streaks, cadence, route, GPS-shape, IWT, visualization, or any broad activity context. The next visible move must be `recent_activity` / `garmin_list_activities`, or a concrete list/auth/data/material blocker that explicitly confines the response to one supplied isolated activity id/date. A successful `garmin_get_activity` row and a failed stale detail-material row are both insufficient as grounding for broader synthesis until the list row or blocker is visible.
