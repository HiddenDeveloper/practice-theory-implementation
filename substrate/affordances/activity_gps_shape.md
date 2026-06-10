---
id: activity_gps_shape
name: Activity GPS shape
materials:
- garmin_render_activity_gps_shape
---
Render a Garmin Connect activity's GPS route on an actual map when Garmin exposes coordinates. By default the material draws the route over OpenStreetMap tiles, which means the map view makes external tile requests for the route area; pass show_tiles=false or map_style=shape for a route-only shape that avoids external tile requests. Use an explicit Garmin-native activity id when available, or provide a date range so the material can select the newest activity with GPS route points. An optional activity_type narrows the scan and accepts the same names and aliases as the activity-type dashboard (for example bike for cycling). The returned payload is suitable for the existing show_visualization MCP App surface.
