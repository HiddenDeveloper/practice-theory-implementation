---
id: friction_754_morning_briefing_source_reads_before_assembly
name: Morning briefing assembly requires recurring source reads
status: active
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
message: Morning briefing assembly is forbidden until the current enactment has read
  unread email with gmail_user_search_threads and the configured recurring site list
  with read_morning_briefing_sites, or the practitioner has used the practice surface
  to record a concrete source blocker before assembly.
---
Friction 754 confirmed the Morning Briefing source-read omissions are a recurring quality concern across the evaluated window. This invariant makes the determinable assembly contract automatic: before `morning_briefing_assemble_report`, earlier steps must include both `gmail_user_search_threads` for unread mail and `read_morning_briefing_sites` for the configured usual-site list. If either is absent, the pass remains in source grounding and must not assemble as though the recurring source ledger is complete.
