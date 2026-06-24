---
id: morning_briefing
name: Morning Briefing
mode: somatic
engagement: false
teleo_affective_ids:
- te_morning_briefing
understanding_ids:
- und_morning_briefing
rules_ids:
- rule_morning_briefing_unread_first
- rule_morning_briefing_source_time
- rule_morning_briefing_site_access_gap
- rule_morning_briefing_no_source_read_is_unfinished
- rule_morning_briefing_read_sources_first
- rule_morning_briefing_source_baseline
affordance_ids:
- read_user_email
- read_live_market_snapshot
- read_morning_site_list
- capture_morning_site_check
- assemble_morning_briefing
evaluation_ids:
- eval_morning_briefing
---
Run the user's recurring morning orientation by starting with the two recurring source reads as the first visible briefing work products: first `read_user_email` / `gmail_user_search_threads` for unread mail, then `read_morning_site_list` / `read_morning_briefing_sites` for the configured usual-site list, or record the concrete Gmail/site-list auth, access, configuration, data, or material blocker for either missing source. Friction 1156 confirms the prior wording was not enough: in the evaluated three-enactment window, unread Gmail was absent every time and two passes reached site-check activity without the recurring-site-list read. Treat any site check, live market snapshot, assembly, synthesis, final answer, or other briefing work before both recurring source rows as an interrupted start. The immediate next visible morning-briefing move must be the missing source read or a concrete blocker for that exact source; do not continue from site-check context, one successful source row, remembered sources, supplied context, or prior trail memory while either recurring source remains unread and unblocked.
