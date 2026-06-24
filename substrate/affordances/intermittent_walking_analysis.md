---
id: intermittent_walking_analysis
name: Intermittent walking analysis
materials:
- garmin_list_activities
- garmin_get_activity
- garmin_get_user_stats
preconditions:
- id: requires_garmin_list_activities_before_garmin_get_activity
  name: requires garmin list activities before garmin get activity
  trigger: garmin_get_activity
  friction_kind: quality_affordance_coverage
  message: activities_management used activity detail before the current activity
    list was visible; invoke recent_activity / garmin_list_activities before adjacent
    activity-detail work.
  forbid_when:
    not:
      step_exists:
        material_name: garmin_list_activities
  content: 'Migrated 2026-06-24T23:04:28+00:00 from 11 invariant(s): activities_activity_detail_requires_prior_list,
    activities_activity_detail_requires_recent_list, activities_detail_requires_prior_activity_list….'
---
Analyse Garmin Connect walking/IWT sessions from Garmin-native activities and metric samples — fast/slow interval recognition, time-in-fast vs time-in-slow, weekly fast minutes, and progression over recent weeks. Do not use Strava as the source for this practice.
