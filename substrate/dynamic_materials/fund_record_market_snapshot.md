---
name: fund_record_market_snapshot
input_schema:
  type: object
  properties:
    fund_id:
      type: string
    as_of:
      type: string
    symbols:
      type: array
      items:
        type: string
    benchmark_symbol:
      type: string
    price_points:
      type: array
      items:
        type: object
        properties:
          symbol:
            type: string
          price:
            type: number
          currency:
            type: string
          as_of:
            type: string
          source:
            type: string
          citation:
            type: string
        required:
        - symbol
        - price
        - as_of
        - source
    filings_or_news:
      type: array
      items:
        type: object
        properties:
          title:
            type: string
          publisher:
            type: string
          published_at:
            type: string
          citation:
            type: string
          summary:
            type: string
    market_regime:
      type: string
    regime_evidence:
      type: array
      items:
        type: string
    stock_type_implications:
      type: array
      items:
        type: object
        properties:
          stock_type:
            type: string
          implication:
            type: string
          evidence:
            type: string
    notes:
      type: string
  required:
  - fund_id
  - as_of
  - symbols
implementation:
  kind: echo
---
Record market information used by a fund decision, including symbols, prices, source names, URLs or citations, and as-of timestamps. The practitioner remains responsible for obtaining real data from available sources and preserving the no-lookahead boundary.
