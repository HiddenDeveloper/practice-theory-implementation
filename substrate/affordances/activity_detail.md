---
id: activity_detail
name: Activity detail, gated by recent list
materials:
- garmin_list_activities
- garmin_get_activity
---
Use this for a selected Garmin activity only after the recent activity record is in hand. Material-choice gate: when invoking this affordance in `activities_management`, choose `garmin_list_activities` first unless the answer is explicitly confined to one supplied isolated activity id/date or a concrete list/auth/data/material gap prevents the list read and will be named as limiting the answer. Choose `garmin_get_activity` only after that current-enactment list step is visible, or only for the isolated-record exception. This affordance reaches both `garmin_list_activities` and `garmin_get_activity` so a practitioner who entered through detail can perform the required activity-record grounding without changing surfaces. A direct `garmin_get_activity` read without a prior or same-affordance `garmin_list_activities` step remains unfinished grounding for `reads_activity_record_before_describing_rhythm`; after any stale detail-material failure, recover to the projected `garmin_list_activities` material before synthesizing activity rhythm, weekly pattern, completed-activity mix, gaps, streaks, cadence, or "what was done".

Friction 700 confirms this adjacent-detail path is still being chosen as a one-step substitute for the activity record list. In `activities_management`, do not invoke `garmin_get_activity` as the first material for any broad or ambiguous activity/rhythm, week-pattern, completed-activity mix, gap, streak, cadence, or "what was done" pass. The first material-choice should be `garmin_list_activities`; if a detail read has already happened first, the immediate next material-choice must be `garmin_list_activities` before another adjacent Garmin read, synthesis, or final answer, unless the pass is explicitly confined to the supplied isolated activity id/date or names a concrete list/auth/data/material blocker.
