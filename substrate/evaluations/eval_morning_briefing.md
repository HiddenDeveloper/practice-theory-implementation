---
id: eval_morning_briefing
name: Morning Briefing - objective delivery
practice_id: morning_briefing
objective_ref: te_morning_briefing
derived_from: te_morning_briefing; und_morning_briefing
window: 8
signals:
- id: reads_morning_sources_before_assembling
  kind: affordance_coverage
  required_materials:
  - gmail_user_search_threads
  - read_morning_briefing_sites
  detail: Each pass should ground the daily orientation in unread email and the configured
    recurring site list before assembling the briefing. A briefing that reads neither
    source is not measuring the practice's objective of gathering and sorting recurring
    signals.
- id: captures_or_names_site_checks
  kind: outcome_presence
  outcome_materials:
  - morning_briefing_browser_site_check
  - morning_briefing_assemble_report
  max_consecutive_without: 3
  detail: The practice should either capture URL-backed site checks through the browser
    proxy or preserve named site/source gaps in the assembled report. Several passes
    without site-check evidence or a final assembled report suggest the ritual is
    not producing its bounded orientation artifact.
- id: not_repeating_same_briefing_shape
  kind: shape_repetition
  max_identical: 4
  detail: Identical enactment shape repeated across many morning passes suggests the
    routine is rote rather than reading the day's actual mail, sites, snapshots, and
    gaps.
- id: recurring_access_gaps_do_not_persist_unexamined
  kind: recurring_summary_marker
  markers:
  - access gap
  - site list unknown
  - browser unavailable
  - jit proxy unavailable
  - gmail gap
  - could not inspect
  - unavailable
  max_consecutive: 5
  detail: Repeatedly naming the same unavailable source can be honest, but after several
    consecutive passes it becomes an unresolved visibility gap that should be judged
    rather than silently normalized.
---

