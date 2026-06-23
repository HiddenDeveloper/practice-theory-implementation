---
id: morning_briefing_requires_source_reads_before_assembly
name: Morning briefing assembly requires recurring source reads
status: active
trigger: morning_briefing_assemble_report
mode: detect
friction_kind: quality_affordance_coverage
forbid_when:
  any:
  - not:
      step_exists:
        material_name: gmail_user_search_threads
  - not:
      step_exists:
        material_name: read_morning_briefing_sites
message: morning_briefing assembly must be preceded in the same enactment by unread
  Gmail (`gmail_user_search_threads`) and configured usual-site-list (`read_morning_briefing_sites`)
  source reads; assemble only after both source rows are visible, or stop before assembly
  with the concrete missing-source blocker.
---
Deterministic guard for the recurring `reads_morning_sources_before_assembling` quality concern: when `morning_briefing_assemble_report` appears, the trail must already contain both required source-read material rows. This turns the repeated hand-judged source-read omission into an automatic substrate contract for the assembly boundary.
