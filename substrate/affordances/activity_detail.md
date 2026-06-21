---
id: activity_detail
name: Activity detail only after current list
materials:
- garmin_list_activities
- garmin_get_activity
---
Friction 868 confirms direct detail starts are still being treated as usable evidence for activity/rhythm-adjacent work: a recent evaluated pass invoked `activity_detail` / `garmin_get_activity` without any current-enactment `garmin_list_activities` row. In `activities_management`, before using this affordance to support any activity/rhythm, week-pattern, completed-activity mix, gap, streak, cadence, or "what was done" answer, first invoke `garmin_list_activities` through this affordance or `recent_activity`; if detail has already been read first, the immediate next move is that list read or a concrete list/auth/data/material blocker. Only a response explicitly confined to one supplied isolated activity id/date may remain detail-only.

Friction 878 confirms this is still a live quality concern in a later evaluated window: `activity_detail` / `garmin_get_activity` appeared before the recent activity list while a nearby passing trace showed `garmin_list_activities` was reachable. Treat any activity-detail-first start in `activities_management` as interrupted for activity/rhythm, week-pattern, completed-activity mix, gap, streak, cadence, or "what was done" work; the next visible move must be `recent_activity` or this affordance reaching `garmin_list_activities`, or a concrete list/auth/data/material blocker. Do not continue to synthesis, another adjacent Garmin surface, or final answer from detail-only evidence unless the answer remains explicitly limited to one supplied isolated activity id/date.
