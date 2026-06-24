---
id: route_aware_iwt_analysis
name: Route-aware IWT analysis
materials:
- garmin_route_aware_iwt_analysis
---
Analyse Garmin walking activities against the intended IWT pattern using route, speed, cadence, elevation, and timestamp evidence. Separate interval adherence from route/terrain/stop effects; do not use Strava, sleep, or heart-rate data.

For `activities_management`, this is downstream of the activity-record entry gate. Do not use `route_aware_iwt_analysis` as the first Garmin activity row for broad or ambiguous activity/rhythm, what-was-done, week-pattern, completed-activity mix, gaps, streaks, cadence, route, GPS-shape, IWT, or visualization work. The current enactment should first show `recent_activity` reaching `garmin_list_activities`, unless the response is explicitly confined to one supplied isolated activity id/date or a concrete list/auth/data/material blocker is recorded and the answer is limited to that narrower evidence.
