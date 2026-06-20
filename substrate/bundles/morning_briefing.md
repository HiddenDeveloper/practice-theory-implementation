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
affordance_ids:
- read_user_email
- read_live_market_snapshot
- read_morning_site_list
- capture_morning_site_check
- assemble_morning_briefing
evaluation_ids:
- eval_morning_briefing
---
Run the user's recurring morning orientation by starting with the two recurring source reads: first read unread email through `read_user_email` / `gmail_user_search_threads`, then read the configured usual-site list through `read_morning_site_list` / `read_morning_briefing_sites`, or record the concrete access, auth, configuration, data, or material blocker for either missing source. Only after those source reads or blockers are visible should the practice inspect individual sites, take optional live market/news-style snapshots when relevant, or assemble the short source-grounded briefing with action items, watch items, routine updates, and unresolved gaps. The practice is for daily triage and sensemaking, not for sending mail, making commitments, or pretending unavailable sources were read.
