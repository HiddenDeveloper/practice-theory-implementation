---
id: assemble_morning_briefing
name: Assemble the morning briefing
materials:
- morning_briefing_assemble_report
---
Friction 810 confirms the source-read gate is still being missed across the evaluated `morning_briefing` window: unread email was never read or concretely blocked, and two runs also missed the configured morning-site-list read before site-check style work. Treat invocation of `assemble_morning_briefing` while either required source row is absent as an interrupted briefing, not a valid closing artifact. The immediate next visible move must be `read_user_email` reaching `gmail_user_search_threads` for unread mail, `read_morning_site_list` reaching `read_morning_briefing_sites` for the configured recurring sites, or a concrete Gmail/site-list auth, access, configuration, data, or material blocker that limits the briefing's source-grounding claim. Do not assemble, summarize, final-answer, or treat browser site checks, invalid-URL results, live market snapshots, supplied context, or prose gaps as substitutes while either recurring source read remains absent and unblocked.
