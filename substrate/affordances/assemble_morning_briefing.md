---
id: assemble_morning_briefing
name: Assemble the morning briefing
materials:
- morning_briefing_assemble_report
---
Record the final morning briefing from gathered evidence: unread email triage, recurring-site observations, optional live snapshot observations, important items, follow-ups, and named gaps. Use this as the closing artifact after source reads and site-check captures, not as a substitute for reading sources.

For the quality signal `reads_morning_sources_before_assembling`, final assembly is gated by two current-enactment source reads: `read_user_email` reaching `gmail_user_search_threads` for unread mail, and `read_morning_site_list` reaching `read_morning_briefing_sites` for the configured recurring sites. Before invoking `morning_briefing_assemble_report`, check that both reads have occurred in the current enactment; if either is absent, perform the missing read first. If Gmail or the site-list read cannot be reached or returns an auth, data, configuration, or material gap, name that gap in the briefing and limit the source-grounding claim accordingly. Browser checks through `capture_morning_site_check` / `morning_briefing_browser_site_check`, live market snapshots, supplied context, or final report prose do not satisfy the unread-mail or configured-site-list reads by themselves.
