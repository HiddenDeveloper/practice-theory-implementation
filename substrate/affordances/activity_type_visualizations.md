---
id: activity_type_visualizations
name: Activity type visualizations
materials:
- garmin_render_activity_type_visualization
---
Render MCP App dashboards for Garmin activities by supported activity type: Walking, Cycling, Strength Training, Pilates, and Yoga. Use activity_type to focus one type, or omit it for an all-types dashboard. Each section shows recent sessions, total duration and distance where relevant, the latest activity, and a GPS route preview when Garmin exposes route points.

For `activities_management`, this is downstream of the activity-record entry gate. Do not use `activity_type_visualizations` as the first Garmin activity row for broad or ambiguous activity/rhythm, what-was-done, week-pattern, completed-activity mix, gaps, streaks, cadence, route, GPS-shape, IWT, or visualization work. The current enactment should first show `recent_activity` reaching `garmin_list_activities`, unless the response is explicitly confined to one supplied isolated activity id/date or a concrete list/auth/data/material blocker is recorded and the answer is limited to that narrower evidence.
