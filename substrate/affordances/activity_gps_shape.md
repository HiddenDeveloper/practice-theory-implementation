---
id: activity_gps_shape
name: Activity GPS shape
materials:
- garmin_render_activity_gps_shape
---
Render a Garmin Connect activity's GPS route on an actual map when Garmin exposes coordinates. By default the material draws the route over OpenStreetMap tiles, which means the map view makes external tile requests for the route area; pass show_tiles=false or map_style=shape for a route-only shape that avoids external tile requests. Use an explicit Garmin-native activity id when available, or provide a date range so the material can select the newest activity with GPS route points. An optional activity_type narrows the scan and accepts the same names and aliases as the activity-type dashboard (for example bike for cycling). The returned payload is suitable for the existing show_visualization MCP App surface.

For `activities_management`, this is downstream of the activity-record entry gate. Do not use `activity_gps_shape` as the first Garmin activity row for broad or ambiguous activity/rhythm, what-was-done, week-pattern, completed-activity mix, gaps, streaks, cadence, route, GPS-shape, IWT, or visualization work. The current enactment should first show `recent_activity` reaching `garmin_list_activities`, unless the response is explicitly confined to one supplied isolated activity id/date or a concrete list/auth/data/material blocker is recorded and the answer is limited to that narrower evidence.
