---
id: record_trade_decision
name: Record trade decision
materials:
- fund_record_trade_decision
---
Record a buy, sell, hold, trim, add, reject, watch, or intentional cash decision with price basis, sizing impact, mandate check, thesis basis, risk basis, market-regime fit, and stock-type fit.

For `stock_investor`, this is a decision-bearing surface even when the action is a hold, blocker-state disposition, no-action posture, construction deferral, or intentional cash stance. If the same enactment has read fund state or the follow-up register, do not invoke `fund_record_trade_decision` until `read_live_market_snapshot` / `market_fetch_snapshot` has also appeared in that enactment, or until a concrete live-market snapshot failure/incompleteness has been recorded as the measurement gap constraining the decision. Friction 858 confirms that relying on unchanged blocker state, same-day context, prior market evidence, or the absence of a new order does not satisfy the required market-evidence row before recording the decision.
