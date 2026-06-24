---
id: capture_morning_site_check
name: Check a morning site
materials:
- morning_briefing_browser_site_check
preconditions:
- id: guard_morning_briefing_browser_site_check__practice_quality_affordance_coverage
  name: guard morning briefing browser site check  practice quality affordance coverage
  trigger: morning_briefing_browser_site_check
  friction_kind: practice_quality_affordance_coverage
  message: Morning briefing browser site checks require earlier unread Gmail and configured
    site-list reads, or direct checks are substituting for the required source-gathering
    gate.
  forbid_when:
    any:
    - not:
        step_exists:
          material_name: gmail_user_search_threads
    - not:
        step_exists:
          material_name: read_morning_briefing_sites
  content: 'Migrated 2026-06-24T23:04:28+00:00 from 2 invariant(s): morning_briefing_source_gate_before_site_check,
    morning_briefing_sources_before_site_check.'
---
Check one recurring morning site through Cognabot's browser JIT proxy, preserving URL/name, observed time, headline candidates, source notes, snapshot text, and any access gap. Use this for URL-backed site checks in the morning briefing; if the JIT proxy or browser service is unavailable, report the returned access gap instead of substituting a generic web summary.

In the `morning_briefing` practice, this site-check affordance is downstream of the two recurring source reads. Before invoking `morning_briefing_browser_site_check`, the current enactment should already show `read_user_email` reaching `gmail_user_search_threads` for unread mail and `read_morning_site_list` reaching `read_morning_briefing_sites` for the configured recurring sites, or should record the concrete Gmail/site-list access, auth, data, configuration, or material blocker that prevents one of those reads. If a pass reaches this affordance first, or reaches it after only the configured site-list read without the unread Gmail row, treat that as unfinished grounding: backfill the missing unread-mail and configured-site-list reads before interpreting the site, running another check, taking a live snapshot, or assembling the briefing. A browser check, invalid-URL result, supplied context, site-list-only path, or single-site observation does not substitute for either recurring-source gate.

Friction 1048 confirms this remains a genuine `morning_briefing` quality concern across the evaluated three-enactment window: unread Gmail was absent in all three passes, and two passes reached site-check activity without the configured recurring-site-list read or a concrete blocker. Treat this affordance as an interrupted path whenever either recurring source row is missing. The immediate next visible move must be the missing `read_user_email` / `gmail_user_search_threads` row, the missing `read_morning_site_list` / `read_morning_briefing_sites` row, or a concrete Gmail/site-list auth, access, configuration, data, or material blocker for the exact missing source. Do not continue to another site check, market snapshot, assembly, synthesis, final answer, verification, or closure from browser-check context while either recurring source remains unread and unblocked.

Friction 1166 confirms the same `reads_morning_sources_before_assembling` coverage failure remains after the intended source-read order was already visible in the bundle and adjacent affordance surfaces: unread Gmail was absent in every evaluated pass, and two passes reached site-check activity without either the Gmail unread-mail read or the configured morning site-list read. For future `morning_briefing` passes, treat any attempt to use this site-check affordance before both recurring source rows as the interruption point itself. The only valid continuation is the exact missing `read_user_email` / `gmail_user_search_threads` unread-mail row, the exact missing `read_morning_site_list` / `read_morning_briefing_sites` configured-site row, or a concrete blocker naming the unavailable source and limiting the briefing to visible evidence. Do not proceed from site-check context into another site check, market snapshot, synthesis, assembly, final answer, verification, or closure while either recurring source row remains unread and unblocked.

Friction 1180 confirms the source-read gate is still failing in recent `morning_briefing` enactments: unread Gmail was absent in all three evaluated passes, and two passes also lacked the configured recurring-site-list read while briefing or site-check work still occurred. Treat a single visible source row as incomplete, especially the site-list-only path from target enactment `fb0b94b8-eb4b-4b2a-aa77-1eed147f8e66`. When this affordance is reached without both `read_user_email` / `gmail_user_search_threads` for unread mail and `read_morning_site_list` / `read_morning_briefing_sites` for configured recurring sites already visible, the pass is interrupted; the immediate next visible move must be the exact missing source read or a concrete blocker for that source. Do not continue into site interpretation, another browser check, market snapshot, briefing assembly, synthesis, final answer, or verification from one source row, browser context, prior morning routine memory, or supplied context while either recurring source remains unread and unblocked.

Friction 1194 confirms the same source-read gap remains a live `morning_briefing` practice-quality failure: in the evaluated three-enactment window, unread Gmail was not read in any pass, and two passes moved into site-check work without the configured recurring-site-list row. Treat this affordance as an immediate stop condition whenever either source row is absent and unblocked. The only valid continuation is `read_user_email` / `gmail_user_search_threads` for unread mail, then `read_morning_site_list` / `read_morning_briefing_sites` for configured recurring sites, or a concrete blocker for the exact missing Gmail or site-list source; do not proceed to site interpretation, another site check, live market context, assembly, synthesis, final answer, verification, handoff, or closure from partial source coverage.
