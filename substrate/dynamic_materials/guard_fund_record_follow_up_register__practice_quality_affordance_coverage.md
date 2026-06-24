---
name: guard_fund_record_follow_up_register__practice_quality_affordance_coverage
input_schema: {}
implementation:
  kind: enactment_check
  trigger: fund_record_follow_up_register
  friction_kind: practice_quality_affordance_coverage
  message: stock_investor recorded a fund follow-up disposition after reading fund
    state without a same-enactment live market snapshot; invoke read_live_market_snapshot
    / market_fetch_snapshot before exposure-preserving decisions or record the snapshot
    failure as the measurement gap.
  forbid_when:
    all:
    - step_exists:
        material_name: fund_read_state
    - not:
        step_exists:
          material_name: market_fetch_snapshot
---
Migrated 2026-06-24T23:04:28+00:00 from 1 invariant(s): stock_investor_follow_up_requires_market_snapshot.
