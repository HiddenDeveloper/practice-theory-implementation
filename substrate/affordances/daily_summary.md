---
id: daily_summary
name: Daily summary only after current list
materials:
- garmin_list_activities
- garmin_get_daily_summary
---
Friction 1029 confirms the `activities_management` gate is still being missed from adjacent daily-summary/detail paths after prior rule and bundle wording: four of five evaluated passes reached direct activity detail, daily summary, or stale adjacent Garmin material attempts without `recent_activity` / `garmin_list_activities`, while comparator `359ef81c-27c6-4c5c-94fa-b740f4e93635` showed the list row was reachable. Treat this affordance's material list as ordered for broad or ambiguous activity/rhythm, week-pattern, completed-activity mix, gaps, streaks, cadence, route, GPS-shape, IWT, visualization, or what-was-done work: invoke `garmin_list_activities` first in the current enactment, then use `garmin_get_daily_summary` only as a downstream daily wellness supplement. If `garmin_get_daily_summary`, `garmin_daily_summary`, or another stale summary alias appears before the list row, the pass is interrupted; the only valid continuation is `garmin_list_activities` or a concrete list/auth/data/material blocker that confines the response to a daily wellness snapshot. Do not move to activity detail, route/GPS/IWT/visualization, synthesis, final answer, verification, or closure from daily-summary evidence alone.
