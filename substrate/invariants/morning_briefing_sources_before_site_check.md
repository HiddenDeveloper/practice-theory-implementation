---
id: morning_briefing_sources_before_site_check
name: Morning briefing sources before site check
status: active
trigger: morning_briefing_browser_site_check
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
message: Morning briefing browser site checks require earlier unread Gmail and configured
  site-list reads, or direct checks are substituting for the required source-gathering
  gate.
---
For `morning_briefing`, a direct browser site check through `morning_briefing_browser_site_check` may only occur after the two required source-gathering reads named by the quality signal: `gmail_user_search_threads` for unread mail and `read_morning_briefing_sites` for the configured recurring site list. This governed invariant addresses Friction 526's evidence that two recent passes used browser site checks while missing both required source reads, letting one-off checks substitute for the practice's configured source grounding. It leaves judgement about access gaps, site content, and final briefing quality to the practice and Judge; it only detects the determinable material-presence gate before site-check work begins.
