---
id: stock_investor_follow_up_requires_market_snapshot
name: Stock investor follow-up disposition requires live market snapshot
status: tombstoned
trigger: fund_record_follow_up_register
mode: detect
friction_kind: practice_quality_affordance_coverage
forbid_when:
  all:
  - step_exists:
      material_name: fund_read_state
  - not:
      step_exists:
        material_name: market_fetch_snapshot
message: stock_investor recorded a fund follow-up disposition after reading fund state
  without a same-enactment live market snapshot; invoke read_live_market_snapshot
  / market_fetch_snapshot before exposure-preserving decisions or record the snapshot
  failure as the measurement gap.
tombstoned_at: '2026-06-24T23:04:28+00:00'
tombstone_reason: migrated to an affordance precondition (phase 3)
---
For stock_investor quality signal `reads_state_and_market_before_deciding`, a closed enactment that records `fund_record_follow_up_register` after `fund_read_state` but without any same-enactment `market_fetch_snapshot` deterministically violates the live-market evidence gate. Friction 849 confirmed this was still being re-found by hand in target enactment `ed3fef8f-b42b-4039-a175-085bba23502d`, where the pass read fund state and recorded a follow-up disposition without the market snapshot row, and in a nearby pass that recorded a trade decision and follow-up without the snapshot. This invariant covers the mechanically checkable material-coverage branch; judgement remains responsible for assessing snapshot content quality, genuine access blockers, and whether non-decision fund maintenance is outside the decision/disposition path.
