---
id: activity_detail
name: Activity detail only after current list
materials:
- garmin_list_activities
- garmin_get_activity
---
Friction 987 confirms the `reads_activity_record_before_describing_rhythm` miss is still occurring in `activities_management`: target enactment `175fd770-3f41-49cd-8ecb-2e23871fcd59` reached `activity_detail` / `garmin_get_activity` without a same-enactment `recent_activity` / `garmin_list_activities` row, while comparator `359ef81c-27c6-4c5c-94fa-b740f4e93635` showed the list path was reachable. Treat a detail-first start for activity rhythm, week pattern, completed-activity mix, gaps, streaks, cadence, route, GPS-shape, IWT, visualization, or what-was-done work as interrupted at this affordance: the immediate next visible move must be `garmin_list_activities` through `recent_activity` or this affordance, or a concrete list/auth/data/material blocker that confines the answer to the isolated supplied activity id/date. Do not continue to another adjacent Garmin surface, synthesis, final answer, or closure from `garmin_get_activity` alone.
