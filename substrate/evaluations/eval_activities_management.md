---
id: eval_activities_management
name: Activities Management - objective delivery
practice_id: activities_management
objective_ref: te_activities_management
derived_from: activities_management@practice_missing_evaluation_454
window: 8
signals:
- id: reads_activity_record_before_describing_rhythm
  kind: affordance_coverage
  required_materials:
  - garmin_list_activities
  detail: Each pass should ground the user's activity rhythm in Garmin activity records
    before describing what has been done or what pattern is forming. A pass that never
    reads recent activities is not measuring the practice's observer/recorder objective.
- id: uses_detail_or_daily_context
  kind: outcome_presence
  outcome_materials:
  - garmin_get_activity
  - garmin_get_daily_summary
  - garmin_get_user_stats
  - garmin_route_aware_iwt_analysis
  max_consecutive_without: 4
  detail: The practice should periodically deepen the activity record with an activity
    detail, daily wellness context, user stats, or route-aware IWT analysis rather
    than only listing activities. A long run without any of these may mean the practice
    is not helping the user see what the body and rhythm are showing.
- id: not_repeating_same_activity_glance
  kind: shape_repetition
  max_identical: 4
  detail: Identical enactment shape repeated many passes running suggests the practice
    is going through a rote activity glance rather than observing the activity record
    and emerging rhythm.
- id: unresolved_gaps_do_not_persist
  kind: recurring_summary_marker
  markers:
  - auth gap
  - missing garmin field
  - data gap
  - not exposed
  - unavailable
  max_consecutive: 5
  detail: Repeated disclosure of the same unavailable Garmin data can be honest, but
    after several consecutive passes it becomes an unresolved visibility gap worth
    Judge attention.
---

