---
id: activities_stale_daily_summary_requires_recent_list_f999
name: Stale daily summary alias requires recent list grounding
status: tombstoned
trigger: garmin_daily_summary
mode: detect
friction_kind: practice_quality_affordance_coverage
forbid_when:
  not:
    step_exists:
      material_name: garmin_list_activities
message: activities_management attempted stale daily-summary material before recent_activity
  / garmin_list_activities; recover through garmin_list_activities or stop at a concrete
  material/list blocker.
tombstoned_at: '2026-06-24T23:04:28+00:00'
tombstone_reason: 'dead: trigger material is a stale alias no affordance reaches (phase
  3)'
---
Friction 999 counted stale daily-summary material attempts as the same activity-record gate miss. When garmin_daily_summary appears in an activities_management trail, the earlier trail must already contain garmin_list_activities; otherwise the pass is interrupted and should recover through recent_activity / garmin_list_activities or name a concrete stale-material/list blocker before any broader activity/rhythm synthesis.
