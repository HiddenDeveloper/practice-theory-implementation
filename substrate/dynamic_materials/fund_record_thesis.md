---
name: fund_record_thesis
input_schema:
  type: object
  properties:
    fund_id:
      type: string
    symbol:
      type: string
    as_of:
      type: string
    status:
      type: string
      enum:
      - candidate
      - holding
      - rejected
      - watchlist
      - closed
    facts:
      type: array
      items:
        type: string
    assumptions:
      type: array
      items:
        type: string
    valuation_view:
      type: string
    business_quality_view:
      type: string
    risk_view:
      type: string
    stock_type:
      type: string
    market_regime_fit:
      type: string
    stock_type_behavior:
      type: string
    missing_evidence:
      type: array
      items:
        type: string
    falsification_triggers:
      type: array
      items:
        type: string
    source_citations:
      type: array
      items:
        type: string
  required:
  - fund_id
  - symbol
  - as_of
  - status
  - facts
  - assumptions
  - risk_view
implementation:
  kind: echo
---
Record or update an investment thesis for a candidate or holding. Separate facts, assumptions, valuation view, risks, missing evidence, and falsification triggers so future reviews can judge whether the thesis drifted.
