---
id: activity_detail
name: Activity detail only after current list
materials:
- garmin_list_activities
- garmin_get_activity
---
Friction 918 confirms the evaluated miss persists specifically on `activity_detail` / `garmin_get_activity`: the target pass used detail without a same-enactment `garmin_list_activities` row. For `activities_management`, treat `garmin_get_activity` as unavailable for rhythm, week-pattern, completed-activity mix, gaps, streaks, cadence, or what-was-done work until the current enactment has first invoked `garmin_list_activities` through `recent_activity` or this affordance. If detail has already happened first, stop the detail path; the only continuation is the list row or a concrete list/auth/data/material blocker, and any answer must remain confined to one supplied isolated activity id/date until that grounding exists.
