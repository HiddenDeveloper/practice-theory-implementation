---
id: activity_detail
name: Activity detail, gated by recent list
materials:
- garmin_list_activities
- garmin_get_activity
---
Use this for a selected Garmin activity only after the recent activity record is in hand. This affordance now reaches `garmin_list_activities` before `garmin_get_activity` so a practitioner who enters through detail can perform the required current-enactment activity-record grounding without changing surfaces. For `activities_management`, invoke `garmin_list_activities` here or through `recent_activity` before any activity detail is used for rhythm, weekly pattern, completed-activity mix, gaps, streaks, cadence, or "what was done" synthesis. The only exceptions are a response explicitly confined to one supplied isolated activity id/date, or a named list/auth/data/material gap that limits the answer. A direct `garmin_get_activity` read without a prior or same-affordance `garmin_list_activities` step remains unfinished grounding for `reads_activity_record_before_describing_rhythm`; after any stale detail-material failure, recover to the projected `garmin_list_activities` material before synthesizing broader activity rhythm.
