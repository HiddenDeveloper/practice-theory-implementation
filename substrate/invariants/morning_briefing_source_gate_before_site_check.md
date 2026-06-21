---
id: morning_briefing_source_gate_before_site_check
name: Morning briefing source gate before site check
status: active
trigger: morning_briefing_browser_site_check
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
message: Morning briefing browser site checks require earlier unread Gmail search
  and configured morning site-list reads, or the practice has skipped its required
  recurring source-gathering gate.
---
For `morning_briefing`, the one-off browser site-check material `morning_briefing_browser_site_check` may only run after the enactment has already recorded both recurring source-gathering reads named by the quality signal: `gmail_user_search_threads` for unread mail and `read_morning_briefing_sites` for the configured recurring site list. Friction 827 showed this same determinable source-gate miss was still being hand-emitted as `quality_affordance_coverage` for browser/site-work-first paths. This invariant keeps the existing material-presence predicate and retargets the routed Friction kind to the quality signal the Judge is actually finding, so browser site checks without the recurring source baseline are detected deterministically.
