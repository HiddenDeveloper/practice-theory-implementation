---
id: daily_summary
name: Daily summary only after current list
materials:
- garmin_list_activities
- garmin_get_daily_summary
---
Friction 868 confirms direct daily-summary starts are still being treated as usable evidence for activity/rhythm-adjacent work: recent evaluated passes invoked `daily_summary` / `garmin_get_daily_summary` or stale daily-summary material names without any current-enactment `garmin_list_activities` row. In `activities_management`, before using this affordance to support any activity/rhythm, week-pattern, completed-activity mix, gap, streak, cadence, or "what was done" answer, first invoke `garmin_list_activities` through this affordance or `recent_activity`; if daily summary or a stale daily-summary material has already been attempted first, the immediate next move is that list read or a concrete list/auth/data/material blocker. Only a response explicitly confined to one daily wellness snapshot may remain daily-summary-only.
