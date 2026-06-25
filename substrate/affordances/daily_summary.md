---
id: daily_summary
name: Daily summary only after current list
materials:
- garmin_list_activities
- garmin_get_daily_summary
check_materials:
- requires_garmin_list_activities_before_garmin_get_daily_summary
---
Read a daily wellness summary (`garmin_get_daily_summary`) — a downstream supplement, not an entry point. If the current-enactment activity list is absent, the next move must be `recent_activity` / `garmin_list_activities`, or a concrete list/auth/data/material blocker; any answer from this affordance alone must be confined to the isolated daily snapshot and must not synthesize broader activity rhythm or week pattern.
