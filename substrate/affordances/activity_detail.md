---
id: activity_detail
name: Activity detail, gated by recent list
materials:
- garmin_list_activities
- garmin_get_activity
---
Use this for a selected Garmin activity only after the recent activity record is in hand. Material-choice gate: when invoking this affordance in `activities_management`, choose `garmin_list_activities` first unless the answer is explicitly confined to one supplied isolated activity id/date or a concrete list/auth/data/material gap prevents the list read and will be named as limiting the answer. Choose `garmin_get_activity` only after that current-enactment list step is visible, or only for the isolated-record exception. This affordance reaches both `garmin_list_activities` and `garmin_get_activity` so a practitioner who entered through detail can perform the required activity-record grounding without changing surfaces. A direct `garmin_get_activity` read without a prior or same-affordance `garmin_list_activities` step remains unfinished grounding for `reads_activity_record_before_describing_rhythm`; after any stale detail-material failure, recover to the projected `garmin_list_activities` material before synthesizing activity rhythm, weekly pattern, completed-activity mix, gaps, streaks, cadence, or "what was done".
