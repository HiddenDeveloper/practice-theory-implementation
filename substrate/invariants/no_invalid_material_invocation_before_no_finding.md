---
id: no_invalid_material_invocation_before_no_finding
name: No invalid material invocation before no-finding closure
status: tombstoned
trigger: judge_record_no_finding
mode: detect
friction_kind: invalid_material_invocation
forbid_when:
  step_exists:
    material_name: judge_no_finding_outcome
    result_contains: not reached for by affordance
message: A Judge enactment reached judge_record_no_finding after directly invoking
  the stale judge_no_finding_outcome material name; use the material name exposed
  by the projection, judge_record_no_finding.
tombstoned_at: '2026-06-24T23:04:28+00:00'
tombstone_reason: migrated to an affordance precondition (phase 3)
---
When a Judge enactment reaches `judge_record_no_finding`, forbid closure only if the same enactment contains a direct failed invocation step whose material name is `judge_no_finding_outcome` and whose result says `not reached for by affordance`. This preserves deterministic detection of the stale no-finding alias while avoiding false positives from `read_enactment_steps` or other inspection results that merely quote invalid-material evidence from another enactment.
