---
name: fund_record_review
input_schema:
  type: object
  properties:
    fund_id:
      type: string
    review_id:
      type: string
    as_of:
      type: string
    period:
      type: string
    performance_summary:
      type: string
    practice_scores:
      type: object
      properties:
        strategy_adherence:
          type: number
        evidence_quality:
          type: number
        risk_control:
          type: number
        thesis_maintenance:
          type: number
        no_lookahead_discipline:
          type: number
        auditability:
          type: number
    practice_notes:
      type: string
    decision_quality_findings:
      type: array
      items:
        type: string
    next_actions:
      type: array
      items:
        type: string
  required:
  - fund_id
  - review_id
  - as_of
  - period
  - performance_summary
  - practice_scores
  - practice_notes
implementation:
  kind: echo
---
Record a periodic fund review that grades both performance and investor-practice quality: strategy adherence, evidence quality, risk control, thesis maintenance, and next actions.
