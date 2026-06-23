---
id: activity_detail
name: Activity detail only after current list
materials:
- garmin_list_activities
- garmin_get_activity
---
Friction 1029 confirms the `activities_management` gate is still being missed from this adjacent surface after prior rule and bundle wording: four of five evaluated passes reached direct activity detail, daily summary, or stale adjacent Garmin material attempts without `recent_activity` / `garmin_list_activities`, including target `175fd770-3f41-49cd-8ecb-2e23871fcd59` using `garmin_get_activity`, while comparator `359ef81c-27c6-4c5c-94fa-b740f4e93635` showed the list row was reachable. Treat this affordance's material list as ordered for broad or ambiguous activity/rhythm work: invoke `garmin_list_activities` first in the current enactment, then use `garmin_get_activity` only as a downstream detail read selected from or checked against that current list. If `garmin_get_activity` or a stale detail alias appears before the list row, the pass is interrupted; the only valid continuation is `garmin_list_activities` or a concrete list/auth/data/material blocker that confines the response to one supplied isolated activity id/date. Do not move to daily summary, route/GPS/IWT/visualization, synthesis, final answer, verification, or closure from detail evidence alone.
