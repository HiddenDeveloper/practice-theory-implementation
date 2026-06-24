---
id: no_unreached_garmin_daily_summary_material
name: No unreached Garmin daily-summary material
status: tombstoned
trigger: garmin_daily_summary
mode: detect
friction_kind: invalid_material_reach
forbid_when:
  step_exists:
    material_name: garmin_daily_summary
    result_contains: not reached for by affordance
message: An activities enactment invoked the stale garmin_daily_summary material;
  daily_summary reaches garmin_get_daily_summary, so this is an invalid material reach
  rather than a completed daily-summary read.
tombstoned_at: '2026-06-24T23:04:28+00:00'
tombstone_reason: 'dead: trigger material is a stale alias no affordance reaches (phase
  3)'
---
When an enactment contains a garmin_daily_summary step whose result says the material is not reached for by the affordance, raise and auto-resolve invalid_material_reach deterministically. The valid daily_summary material is garmin_get_daily_summary; garmin_daily_summary is a stale/unregistered material name, so the failed reach should not require a Judge to rediscover it by hand. This complements the existing activity-record grounding invariants for garmin_get_activity and garmin_get_daily_summary plus the stale garmin_get_activity_detail invariant, covering the stale daily-summary failure named in Friction 688.
