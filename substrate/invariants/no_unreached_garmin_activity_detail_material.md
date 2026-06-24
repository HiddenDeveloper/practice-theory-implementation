---
id: no_unreached_garmin_activity_detail_material
name: No unreached Garmin activity-detail material
status: tombstoned
trigger: garmin_get_activity_detail
mode: detect
friction_kind: invalid_material_reach
forbid_when:
  step_exists:
    material_name: garmin_get_activity_detail
    result_contains: not reached for by affordance
message: An activities enactment invoked the stale garmin_get_activity_detail material;
  activity_detail reaches garmin_get_activity, so this is an invalid material reach
  rather than a completed activity-detail read.
tombstoned_at: '2026-06-24T23:04:28+00:00'
tombstone_reason: 'dead: trigger material is a stale alias no affordance reaches (phase
  3)'
---
When an enactment contains a garmin_get_activity_detail step whose result says the material is not reached for by the affordance, raise and auto-resolve invalid_material_reach deterministically. The valid activity_detail material is garmin_get_activity; garmin_get_activity_detail is a stale/unregistered material name, so the failed reach should not require a Judge to rediscover it by hand.
