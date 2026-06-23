---
id: activity_detail
name: Activity detail only after current list
materials:
- garmin_list_activities
- garmin_get_activity
---
Friction 954 confirms the evaluated miss remains live on the target `activities_management` path: enactment `175fd770-3f41-49cd-8ecb-2e23871fcd59` invoked `activity_detail` / `garmin_get_activity` without a same-enactment `recent_activity` / `garmin_list_activities` row, while a nearby contrast pass showed the list surface was reachable. Treat this affordance's first decision point as the gate itself, not as a recovery note after detail has been read. For any activity/rhythm, week-pattern, completed-activity mix, gaps, streaks, cadence, or what-was-done pass, do not invoke `garmin_get_activity` from a remembered id, stale alias recovery, prior trail context, or daily-summary context until the current enactment has first invoked `garmin_list_activities` through `recent_activity` or this affordance. If `activity_detail` has already appeared first, the next visible move must be the list row or a concrete list/auth/data/material blocker; do not synthesize or close a broad activity answer from the isolated detail row. Only a response explicitly confined to one supplied activity id/date may stay detail-only.
