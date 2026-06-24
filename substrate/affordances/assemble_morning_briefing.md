---
id: assemble_morning_briefing
name: Assemble the morning briefing
materials:
- morning_briefing_assemble_report
check_materials:
- guard_morning_briefing_assemble_report__practice_quality_affordance_coverage
---
Friction 973 confirms `reads_morning_sources_before_assembling` remains a live `morning_briefing` quality failure after prior gate wording: across the evaluated three-enactment window, unread Gmail was absent every time, and two passes also lacked the configured usual-site-list read. Treat this affordance as a hard assembly boundary, not guidance to remember while drafting. Before invoking `morning_briefing_assemble_report`, the same enactment must already show both source rows: `read_user_email` reaching `gmail_user_search_threads` for unread mail, and `read_morning_site_list` reaching `read_morning_briefing_sites` for the configured recurring sites. If either row is missing, stop assembly; the only valid next move is the missing source read or a concrete Gmail/site-list auth, access, configuration, data, or material blocker for that exact source. Do not assemble, summarize, final-answer, or use browser site checks, invalid-URL results, live market snapshots, supplied context, prior trail memory, or one successful source row as a substitute for the other recurring source row.
