---
id: eval_stock_investor
name: Stock Investor — objective delivery
practice_id: stock_investor
objective_ref: te_stock_investor
derived_from: stock_investor@hand-authored-phase1
window: 8
signals:
- id: reads_state_and_market_before_deciding
  kind: affordance_coverage
  required_materials:
  - fund_read_state
  - market_fetch_snapshot
  detail: >-
    Each pass should read the reconstructed fund state and a live market
    snapshot before any decision. A pass that decides without them is acting
    without the evidence the practice's no-lookahead and read-state-first rules
    require.
- id: decisions_produce_outcomes
  kind: outcome_presence
  outcome_materials:
  - brokerage_submit_buy_order
  - brokerage_submit_sell_order
  max_consecutive_without: 6
  detail: >-
    The objective is to build and steward a fund, not only to observe it. A
    long run of passes that record only hold/watch with no order may be
    disciplined patience or may be a stall — a run beyond the threshold is worth
    a judge's attention, not an automatic fault.
- id: not_repeating_without_progress
  kind: shape_repetition
  max_identical: 4
  detail: >-
    Identical enactment shape repeated many passes running suggests the practice
    is going through the motions rather than advancing its analysis.
- id: disclosed_gaps_are_resolving
  kind: recurring_summary_marker
  markers:
  - measurement gap
  - drift
  - without matching filled
  - carried forward
  max_consecutive: 5
  detail: >-
    A gap the practice honestly discloses every pass is a gap it never closes.
    Faithful re-disclosure reads as compliance but is unresolved work.
---
This evaluation measures whether the Stock Investor practice is *delivering its
objective* — disciplined, evidence-grounded stewardship of a fund — rather than
merely completing mechanically clean passes. It traces to `te_stock_investor`:
the practice exists to form theses, read live markets, decide, act, value, and
review with auditable evidence, and to measure fund value without pretending
short-term value alone proves good practice.

The signals are deliberately generic in kind (coverage, outcome presence,
repetition, recurring self-disclosure) with stock-specific parameters; the
engine that computes them knows nothing about funds. A concern raised here is
not a verdict — it is a measurement handed to the Judge, who decides whether it
is real quality friction (a stall) or acceptable variation (patient holding in a
regime that warrants it).
