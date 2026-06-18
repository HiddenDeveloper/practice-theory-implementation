---
name: fund_record_trade_decision
input_schema:
  type: object
  properties:
    fund_id:
      type: string
    decision_id:
      type: string
    as_of:
      type: string
    symbol:
      type: string
    action:
      type: string
      enum:
      - buy
      - sell
      - hold
      - trim
      - add
      - reject
      - watch
    quantity:
      type: number
    price:
      type: number
    currency:
      type: string
    expected_cash_after:
      type: number
    expected_position_pct_after:
      type: number
    mandate_check:
      type: string
    thesis_basis:
      type: string
    risk_basis:
      type: string
    market_regime:
      type: string
    stock_type:
      type: string
    stock_type_fit:
      type: string
    source_citations:
      type: array
      items:
        type: string
  required:
  - fund_id
  - decision_id
  - as_of
  - symbol
  - action
  - mandate_check
  - thesis_basis
  - risk_basis
  - market_regime
  - stock_type_fit
implementation:
  kind: echo
---
Record a fund decision to buy, sell, hold, trim, add, reject, or watch. The record includes intended action, price basis, position-sizing effect, cited thesis basis, and whether the decision respects the fund mandate.
