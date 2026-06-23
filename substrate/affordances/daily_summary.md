---
id: daily_summary
name: Daily summary only after current list
materials:
- garmin_list_activities
- garmin_get_daily_summary
---
Friction 1017 confirms direct daily-summary and stale adjacent Garmin paths still bypass the current activity-list gate in `activities_management`: four of five evaluated enactments reached detail, daily-summary, or stale adjacent materials without `recent_activity` / `garmin_list_activities`, while comparator `359ef81c-27c6-4c5c-94fa-b740f4e93635` showed the list path was reachable. For any broad or ambiguous rhythm, week-pattern, completed-activity mix, gaps, streaks, cadence, route, GPS-shape, IWT, visualization, or what-was-done answer, this affordance is not an alternate entry point: if `garmin_get_daily_summary`, `garmin_daily_summary`, or another stale daily-summary alias appears before the current list row, the pass is interrupted and the immediate next visible move must be `recent_activity` reaching `garmin_list_activities`, or a concrete list/auth/data/material blocker that confines the answer to a daily wellness snapshot. Do not continue to activity detail, route/GPS/IWT/visualization, synthesis, final answer, or closure from daily-summary evidence alone.
