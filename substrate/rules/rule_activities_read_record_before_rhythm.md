---
id: rule_activities_read_record_before_rhythm
name: List recent activities before activity rhythm or adjacent Garmin reads
---
Friction 798 confirms that the failure persists specifically across adjacent Garmin surfaces: four of five recent `activities_management` passes reached `activity_detail`, `daily_summary`, or stale Garmin material attempts without first invoking `recent_activity` / `garmin_list_activities`. Treat any such adjacent Garmin row before the list read as positive evidence that the activity-rhythm pass has not yet begun from the current activity record. The correction is not to continue interpreting the adjacent result narrowly; the immediate next move must be `recent_activity` / `garmin_list_activities`, or a concrete list/auth/data/material blocker, before any description of what was done, rhythm, completed-record mix, gaps, streaks, cadence, recovery context, route/GPS/IWT context, visualization, or final answer.
