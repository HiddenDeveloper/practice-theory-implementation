---
id: daily_summary
name: Daily summary only after current list
materials:
- garmin_list_activities
- garmin_get_daily_summary
---
Friction 868 confirms direct daily-summary starts are still being treated as usable evidence for activity/rhythm-adjacent work: recent evaluated passes invoked `daily_summary` / `garmin_get_daily_summary` or stale daily-summary material names without any current-enactment `garmin_list_activities` row. In `activities_management`, before using this affordance to support any activity/rhythm, week-pattern, completed-activity mix, gap, streak, cadence, or "what was done" answer, first invoke `garmin_list_activities` through this affordance or `recent_activity`; if daily summary or a stale daily-summary material has already been attempted first, the immediate next move is that list read or a concrete list/auth/data/material blocker. Only a response explicitly confined to one daily wellness snapshot may remain daily-summary-only.

Friction 878 confirms this is still a live quality concern in a later evaluated window: `daily_summary` / `garmin_get_daily_summary` appeared or was attempted before the recent activity list while a nearby passing trace showed `garmin_list_activities` was reachable. Treat any daily-summary-first or stale-daily-summary-material start in `activities_management` as interrupted for activity/rhythm, week-pattern, completed-activity mix, gap, streak, cadence, or "what was done" work; the next visible move must be `recent_activity` or this affordance reaching `garmin_list_activities`, or a concrete list/auth/data/material blocker. Do not continue to synthesis, another adjacent Garmin surface, or final answer from daily-summary-only evidence unless the answer remains explicitly limited to one daily wellness snapshot.
