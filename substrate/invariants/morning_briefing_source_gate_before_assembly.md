---
id: morning_briefing_source_gate_before_assembly
name: Morning briefing source gate before assembly
status: tombstoned
trigger: morning_briefing_assemble_report
mode: detect
friction_kind: practice_quality_affordance_coverage
forbid_when:
  any:
  - not:
      step_exists:
        material_name: gmail_user_search_threads
  - not:
      step_exists:
        material_name: read_morning_briefing_sites
message: Morning briefing assembly requires earlier unread Gmail search and configured
  morning site-list reads, or the practice has skipped its required source-gathering
  gate.
tombstoned_at: '2026-06-24T23:04:28+00:00'
tombstone_reason: migrated to an affordance precondition (phase 3)
---
For `morning_briefing`, the final assembly material `morning_briefing_assemble_report` may only close a briefing after the enactment has already recorded the two source-gathering reads named by the practice-quality signal: `gmail_user_search_threads` for unread mail and `read_morning_briefing_sites` for the configured recurring site list. This governed invariant makes deterministic the contract already stated in `rule_morning_briefing_unread_first`, which the Judge re-found by hand in Friction 514 after the evaluated runs repeatedly assembled or approached briefings without one or both required source reads. The immediately prior author_invariant call failed only because it supplied unsupported mode `somatic`; the tool reported that only `detect` is valid, so this retry changes only the mode field and leaves the chosen contract, trigger, friction kind, and predicate unchanged. The invariant deliberately checks only material-presence facts; judgement about source content, access gaps, and briefing quality remains with the practice and Judge.
