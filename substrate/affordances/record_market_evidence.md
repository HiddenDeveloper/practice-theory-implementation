---
id: record_market_evidence
name: Record market evidence
materials:
- fund_record_market_snapshot
---
Persist the real prices, filings, news, benchmark values, source citations, as-of timestamps, and market-regime interpretation used for a fund decision. Prefer evidence returned by `read_live_market_snapshot`; if any evidence is gathered elsewhere, name the source and timestamp. Use this to preserve the no-lookahead boundary before forming or changing a thesis.
