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
  required:
  - target_enactment_id
  - basis
  - reason
implementation:
  kind: echo
---
Record that a Judge inspected a target and found no Friction warranted. This is a judgement outcome, not a Friction observation: include the inspected target enactment id, the read/list step ids or returned basis used for the judgement, and the reason no Friction was emitted.
