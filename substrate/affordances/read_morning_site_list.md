---
id: read_morning_site_list
name: Read morning site list
materials:
- read_morning_briefing_sites
check_materials:
- requires_gmail_user_search_threads_before_read_morning_briefing_sites
---
Read the configured recurring morning-briefing site list (`read_morning_briefing_sites`) — the configured-site-list source gate, paired with unread Gmail. In a `morning_briefing` pass this is not the first source move: first use `read_user_email` reaching `gmail_user_search_threads` for unread mail, or record a concrete Gmail access/auth/data/material blocker. If a pass reaches this affordance first, backfill `read_user_email` / `gmail_user_search_threads` before any site interpretation, browser check, live snapshot, grouping, assembly, handoff, final answer, or closure. If the site list itself cannot be read, record the concrete configuration/access/data/material blocker — do not substitute an ad hoc browser check or generic web summary for the configured recurring site list.
