---
id: activities_management
name: Activities Management
mode: somatic
engagement: false
teleo_affective_ids:
- te_activities_management
understanding_ids:
- und_activities_management
rules_ids:
- rule_cite_source
- rule_no_intent_inference
- rule_no_coaching
- rule_no_external_exposure
- rule_activities_read_record_before_rhythm
affordance_ids:
- recent_activity
- activity_detail
- daily_summary
- intermittent_walking_analysis
- route_aware_iwt_analysis
- activity_gps_shape
- activity_type_visualizations
evaluation_ids:
- eval_activities_management
---
Keep an honest, useful view of the user's physical activities - what's been done, what the body is showing, what the rhythm looks like. For any activity/rhythm, week-pattern, completed-activity mix, gaps, streaks, cadence, or "what was done" pass, make `recent_activity` / `garmin_list_activities` the entry grounding move before activity detail, daily summary, route, GPS-shape, IWT-analysis, or visualization surfaces; those adjacent surfaces deepen the record only after the current activity list is in hand, unless the answer is explicitly limited to one isolated activity or daily snapshot and names that limit. Friction 666 confirms that direct detail reads, direct daily-summary reads, and failed stale Garmin material attempts are still being treated as if they were enough grounding; they are redirect points instead. After any such adjacent or failed Garmin step, immediately recover to the projected surface if needed and invoke `recent_activity` / `garmin_list_activities` before synthesis, unless the response names the isolated-activity/daily-snapshot or list/auth/data/material-gap limit and stays within it.
