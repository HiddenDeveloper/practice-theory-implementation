---
name: guard_morning_briefing_assemble_report__practice_quality_affordance_coverage
input_schema: {}
implementation:
  kind: enactment_check
  trigger: morning_briefing_assemble_report
  friction_kind: practice_quality_affordance_coverage
  message: Morning briefing assembly requires earlier unread Gmail search and configured
    morning site-list reads, or the practice has skipped its required source-gathering
    gate.
  forbid_when:
    any:
    - not:
        step_exists:
          material_name: gmail_user_search_threads
    - not:
        step_exists:
          material_name: read_morning_briefing_sites
---
Migrated 2026-06-24T23:04:28+00:00 from 3 invariant(s): friction_754_morning_briefing_source_reads_before_assembly, morning_briefing_requires_source_reads_before_assembly, morning_briefing_source_gate_before_assembly.
