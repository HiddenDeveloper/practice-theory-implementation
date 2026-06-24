---
name: judge_record_no_finding
input_schema:
  type: object
  properties:
    target_enactment_id:
      type: string
    basis:
      type: object
    reason:
      type: string
    target_subject:
      type: object
      properties:
        kind:
          type: string
          enum:
          - enactment
          - practice_quality_window
        practice_id:
          type: string
        evaluated_enactment_ids:
          type: array
          items:
            type: string
  required:
  - target_enactment_id
  - basis
  - reason
implementation:
  kind: echo
---
Record that a Judge inspected a target and found no Friction warranted. This is a judgement outcome, not a Friction observation: include the inspected target enactment id, the read/list step ids or returned basis used for the judgement, and the reason no Friction was emitted. When the basis is a practice-quality review over a practice bundle/window, do not put the bundle or practice id in `target_enactment_id`; keep `target_enactment_id` to an actual enactment id that the no-finding is closing over, and put the practice id, evaluated enactment ids, and review/window basis in the structured `basis` and optional `target_subject` fields. When the reason discusses a failed invocation, corrected invocation, or unused alternative, name the affordance_id, material_name, and step id exactly as recorded in the structured basis; do not substitute an affordance such as emit_friction, no_finding_outcome, or any other surface that is not actually present in the target steps. When the Judge has a dispatched or otherwise known target enactment id, the no-finding outcome's target_enactment_id must remain that same controlling comparison subject used for list_recent_enactments and read_enactment_steps; do not close no-finding for a different recent enactment id surfaced during discovery unless an explicit redirection basis was recorded before the direct read and bundle comparison.
