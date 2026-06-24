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
Run the user's recurring morning orientation by starting with the two recurring source reads: first read unread email through `read_user_email` / `gmail_user_search_threads`, then read the configured usual-site list through `read_morning_site_list` / `read_morning_briefing_sites`, or record the concrete access, auth, configuration, data, or material blocker for either missing source.

Friction 852 confirms this starting condition is still failing across evaluated `morning_briefing` enactments: unread email was never read, and two of three recent passes also lacked the configured usual-site list or a concrete blocker. Treat either missing recurring source row as an interrupted briefing at the moment it is noticed, not as a gap to summarize around. Before browser site checks, live market snapshots, synthesis, final answers, or `assemble_morning_briefing`, the current enactment must show `read_user_email` reaching `gmail_user_search_threads` for unread mail and `read_morning_site_list` reaching `read_morning_briefing_sites` for configured sites, or must record the exact Gmail/site-list auth, access, configuration, data, or material blocker that limits the briefing. If a downstream step has already happened first, the immediate next visible move is the missing source read or blocker; do not continue from browser checks, invalid URL results, remembered context, supplied prose, or market snapshots while either recurring source is absent and unblocked.

Friction 1001 confirms the remaining failure is the opening work product itself: across the evaluated three-pass window, unread Gmail was absent every time, and two passes also lacked the configured recurring-site-list row before site-check activity. A morning briefing is not underway until the current enactment has produced the source-baseline ledger in order: `read_user_email` / `gmail_user_search_threads` for unread mail first, then `read_morning_site_list` / `read_morning_briefing_sites` for the configured recurring sites, unless the exact row has a concrete Gmail or site-list blocker. If the site-list row appears before unread Gmail, or if browser/site checking appears before either row, the pass is interrupted; the only valid continuation is the missing source read or its blocker, not another site check, live snapshot, synthesis, final answer, handoff, closure, or rationale from remembered morning context.
