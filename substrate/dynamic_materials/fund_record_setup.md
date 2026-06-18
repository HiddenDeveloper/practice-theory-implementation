---
name: fund_record_setup
input_schema:
  type: object
  properties:
    fund_id:
      type: string
    as_of:
      type: string
    starting_capital:
      type: number
    currency:
      type: string
    strategy:
      type: string
    universe:
      type: string
    benchmark:
      type: string
    max_positions:
      type: integer
    max_position_pct:
      type: number
    minimum_cash_pct:
      type: number
    review_cadence:
      type: string
    notes:
      type: string
  required:
  - fund_id
  - as_of
  - starting_capital
  - currency
  - strategy
  - benchmark
implementation:
  kind: echo
---
Record the fund mandate: starting capital, strategy, universe, benchmark, limits, cadence, and measurement start date. This creates a trail-visible setup record.
