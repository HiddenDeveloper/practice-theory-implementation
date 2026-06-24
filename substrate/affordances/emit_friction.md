---
id: emit_friction
name: Emit a Friction observation
materials:
- judge_emit_friction
preconditions:
- id: guard_judge_emit_friction__argument_schema_mismatch
  name: guard judge emit friction  argument schema mismatch
  trigger: judge_emit_friction
  friction_kind: argument_schema_mismatch
  message: A Judge enactment reached judge_emit_friction after an earlier failed call
    used the stale enactment_id argument. Use target_enactment_id for the closure
    surface; this is an argument schema mismatch on the Judge friction-emission material.
  forbid_when:
    any_earlier_step_result_contains: unexpected keyword argument 'enactment_id'
  content: 'Migrated 2026-06-24T23:04:28+00:00 from 1 invariant(s): no_judge_emit_friction_enactment_id_schema_mismatch.'
---
Record a Friction observation against an enactment, with a kind, a freeform content description, and optional structured evidence. Observation only; no remedies. When the Judge has completed judgement-oriented reads but cannot record a warranted no-finding because no dedicated no-finding surface is projected, use this same observation surface as the active fallback closure surface to record that missing closure surface narrowly, e.g. kind `no_finding_surface_missing`, with the inspected target id and read/list basis in observation_data instead of ending silently. That fallback emission is the required recorded judgement outcome for the Judge enactment in this surface-limited case, so the trail can distinguish a completed no-finding attempt from an enactment that stopped after inspection; it is not a no-finding verdict about the inspected target.
