---
id: read_user_email
name: Read the user's email
materials:
- gmail_user_search_threads
- gmail_user_get_thread
- gmail_user_list_drafts
---
For `morning_briefing`, this is the first recurring source-baseline row, not an optional correspondence read. Before any configured-site-list read, browser/site check, live market snapshot, source interpretation, briefing assembly, final answer, or closure in a morning briefing pass, invoke this affordance with `gmail_user_search_threads` to read unread mail, or record a concrete Gmail auth, access, account, data, query, or material blocker. If a pass has already touched `read_morning_site_list`, `capture_morning_site_check`, `read_live_market_snapshot`, assembly, summary, or final-answer surfaces while unread Gmail is absent, the pass is interrupted: the immediate next visible move must be this unread-mail row or its concrete blocker. A successful configured-site-list read, browser check, invalid-URL result, remembered context, or no-unread-mail assumption does not substitute for this row.
