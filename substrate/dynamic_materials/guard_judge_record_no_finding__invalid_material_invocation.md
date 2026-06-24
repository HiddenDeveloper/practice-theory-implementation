---
name: guard_judge_record_no_finding__invalid_material_invocation
input_schema: {}
implementation:
  kind: enactment_check
  trigger: judge_record_no_finding
  friction_kind: invalid_material_invocation
  message: A Judge enactment reached judge_record_no_finding after directly invoking
    the stale judge_no_finding_outcome material name; use the material name exposed
    by the projection, judge_record_no_finding.
  forbid_when:
    step_exists:
      material_name: judge_no_finding_outcome
      result_contains: not reached for by affordance
---
Migrated 2026-06-24T23:04:28+00:00 from 1 invariant(s): no_invalid_material_invocation_before_no_finding.
