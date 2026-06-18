---
name: fund_record_valuation
input_schema:
  type: object
  properties:
    fund_id:
      type: string
    as_of:
      type: string
    cash:
      type: number
    currency:
      type: string
    positions:
      type: array
      items:
        type: object
        properties:
          symbol:
            type: string
          quantity:
            type: number
          price:
            type: number
          market_value:
            type: number
          position_pct:
            type: number
          source:
            type: string
          price_as_of:
            type: string
        required:
        - symbol
        - quantity
        - price
        - market_value
        - price_as_of
    portfolio_value:
      type: number
    starting_capital:
      type: number
    absolute_return_pct:
      type: number
    benchmark_symbol:
      type: string
    benchmark_return_pct:
      type: number
    relative_return_pct:
      type: number
    drawdown_pct:
      type: number
    turnover_pct:
      type: number
    measurement_gaps:
      type: array
      items:
        type: string
  required:
  - fund_id
  - as_of
  - cash
  - currency
  - positions
  - portfolio_value
  - starting_capital
  - absolute_return_pct
  - benchmark_symbol
implementation:
  kind: echo
---
Record a fund valuation using real as-of prices and benchmark values. This is the fund-value measurement surface: absolute and benchmark-relative results are both captured with any gaps.
