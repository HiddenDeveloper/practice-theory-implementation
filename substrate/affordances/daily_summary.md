---
id: daily_summary
name: Daily summary, gated by recent list
materials:
- garmin_list_activities
- garmin_get_daily_summary
---
Use this for Garmin daily wellness context only after the recent activity record is in hand when the answer may describe activity rhythm, weekly pattern, completed-activity mix, gaps, streaks, cadence, or "what was done." This affordance now reaches `garmin_list_activities` before `garmin_get_daily_summary` so a practitioner who enters through daily summary can perform the required current-enactment activity-record grounding without changing surfaces. The only exceptions are a response explicitly confined to one daily wellness snapshot, or a named list/auth/data/material gap that limits the answer. A direct `garmin_get_daily_summary` read without a prior or same-affordance `garmin_list_activities` step remains unfinished grounding for `reads_activity_record_before_describing_rhythm`; after any stale daily-summary material failure, recover to the projected `garmin_list_activities` material before synthesizing broader activity rhythm.
