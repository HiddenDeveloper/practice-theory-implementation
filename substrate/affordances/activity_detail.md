---
id: activity_detail
name: Activity detail only after current list
materials:
- garmin_list_activities
- garmin_get_activity
---
Friction 850 confirms the detail-first bypass is still a practice-quality stall: recent `activities_management` enactments again used `activity_detail` or stale detail-material attempts without first or immediately recovering to `garmin_list_activities`. Treat this affordance as unfinished whenever it appears before the current-enactment activity list for any broad or ambiguous activity-rhythm, week-pattern, completed-activity mix, gap, streak, cadence, or "what was done" pass. If `garmin_get_activity` or a stale detail material has already been attempted first, the next visible move must be `garmin_list_activities` through this affordance or `recent_activity`, or a concrete list/auth/data/material blocker; do not synthesize, final-answer, or continue to another Garmin surface from detail-only evidence.
