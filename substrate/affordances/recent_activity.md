---
id: recent_activity
name: Recent activity
materials:
- garmin_list_activities
---
Look at Garmin Connect activities over a recent window or explicit date range. Invoke the reached material `garmin_list_activities`; `garmin` is a stale material alias and is not valid for this affordance. Treat returned rows as device-tracked Garmin records and cite their source; if the live material reports an auth or data gap, name that gap rather than substituting mock data.
