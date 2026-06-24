---
id: no_finding_outcome
name: Record a no-finding outcome
materials:
- judge_record_no_finding
preconditions:
- id: guard_judge_record_no_finding__invalid_material_invocation
  name: guard judge record no finding  invalid material invocation
  trigger: judge_record_no_finding
  friction_kind: invalid_material_invocation
  message: A Judge enactment reached judge_record_no_finding after directly invoking
    the stale judge_no_finding_outcome material name; use the material name exposed
    by the projection, judge_record_no_finding.
  forbid_when:
    step_exists:
      material_name: judge_no_finding_outcome
      result_contains: not reached for by affordance
  content: 'Migrated 2026-06-24T23:04:28+00:00 from 1 invariant(s): no_invalid_material_invocation_before_no_finding.'
---
Record an explicit Judge no-finding outcome after judgement-oriented reads when no Friction is warranted. Invoke this affordance with the reached material `judge_record_no_finding`; `no_finding_outcome` is the affordance id, not a valid material name. Use this instead of emit_friction for ordinary no-finding closure, and include the inspected target enactment id, the read/list basis, and the reason no Friction was emitted so the trail distinguishes a completed no-finding judgement from an enactment that stopped after inspection.
