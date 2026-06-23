---
id: assemble_morning_briefing
name: Assemble the morning briefing
materials:
- morning_briefing_assemble_report
---
Friction 964 confirms the `reads_morning_sources_before_assembling` quality concern remains live across the evaluated `morning_briefing` window: unread Gmail was not read in any of three passes, and two passes also lacked the configured recurring site-list read. Treat assembly as blocked until both recurring source rows are visible in the same enactment: `read_user_email` reaching `gmail_user_search_threads` for unread mail and `read_morning_site_list` reaching `read_morning_briefing_sites` for the configured usual-site list. If either row is absent, the next visible move must be the missing source read, or a concrete Gmail/site-list auth, access, configuration, data, or material blocker for that exact missing source; if both are absent, recover both before assembling. Do not assemble, summarize, final-answer, or treat browser site checks, invalid-URL results, live market snapshots, supplied context, prose gaps, or a single successful source read as substitutes for the other recurring source row.
