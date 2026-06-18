---
id: rule_stock_investor_live_market_snapshot
name: Fetch live market evidence before allocation
---
Before recording a buy, sell, trim, add, reject, watch, or all-cash posture decision, invoke the live market snapshot material through the market-reading affordance. Use its returned prices, timestamps, source URLs, and limitations as the evidence basis. If the live read fails or is incomplete, record that failure as a measurement gap and make only decisions that are justified by the remaining evidence.
