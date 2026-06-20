---
id: daily_summary
name: Daily summary, gated by recent list
materials:
- garmin_list_activities
- garmin_get_daily_summary
---
Use this for Garmin daily wellness context only after the recent activity record is in hand when the answer may describe activity rhythm, weekly pattern, completed-activity mix, gaps, streaks, cadence, or "what was done." Material-choice gate: when invoking this affordance in `activities_management`, choose `garmin_list_activities` first unless the answer is explicitly confined to one daily wellness snapshot or a concrete list/auth/data/material gap prevents the list read and will be named as limiting the answer. Choose `garmin_get_daily_summary` only after that current-enactment list step is visible, or only for the daily-snapshot exception. This affordance reaches both `garmin_list_activities` and `garmin_get_daily_summary` so a practitioner who entered through daily summary can perform the required activity-record grounding without changing surfaces. A direct `garmin_get_daily_summary` read without a prior or same-affordance `garmin_list_activities` step remains unfinished grounding for `reads_activity_record_before_describing_rhythm`; after any stale daily-summary material failure, recover to the projected `garmin_list_activities` material before synthesizing broader activity rhythm.
