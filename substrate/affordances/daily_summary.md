---
id: daily_summary
name: Daily summary only after current list
materials:
- garmin_list_activities
- garmin_get_daily_summary
---
Friction 1154 confirms the `activities_management` quality signal `reads_activity_record_before_describing_rhythm` is still failing in the fresh five-enactment window: evaluated misses reached `daily_summary` / `garmin_get_daily_summary` or a stale daily-summary material alias without first invoking `recent_activity` / `garmin_list_activities`, while a nearby contrast pass showed the list path was reachable. Treat this affordance as a blocked downstream surface whenever the current enactment has not yet shown `recent_activity` reaching `garmin_list_activities` and the work may describe activity rhythm, what was done, week pattern, completed-activity mix, gaps, streaks, cadence, route, GPS-shape, IWT, visualization, or any broad activity context. The next visible move must be `recent_activity` / `garmin_list_activities`, or a concrete list/auth/data/material blocker that explicitly confines the response to one daily wellness snapshot or one isolated date. A successful `garmin_get_daily_summary` row and a failed stale daily-summary material row are both insufficient as grounding for broader activity synthesis until the list row or blocker is visible.
