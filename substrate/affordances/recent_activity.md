---
id: recent_activity
name: 'First Garmin move: recent activity record'
materials:
- garmin_list_activities
---
Start here for Garmin activity context. This is the mandatory entry gate for `activities_management`: invoke `garmin_list_activities` before any answer that describes or probes activity rhythm, weekly pattern, completed-activity mix, gaps, streaks, cadence, or "what was done," and before using `activity_detail`, `daily_summary`, route, GPS-shape, IWT-analysis, or visualization for a broad or ambiguous activity question. The only exceptions are a response explicitly confined to one supplied isolated activity id/date or one daily wellness snapshot, or a named auth/data/material gap that prevents the list read and limits the answer accordingly.

Adjacent surfaces are supplements, not alternate entry points. If a pass has already touched `activity_detail`, `daily_summary`, route/GPS/IWT/visualization, or a stale Garmin alias before this list read, it is interrupted: the next visible move must be this `garmin_list_activities` read before any rhythm, week-pattern, or "what was done" synthesis — unless the answer is strictly confined to that isolated record, or a concrete list/auth/data/material blocker is named.
