---
id: capture_morning_site_check
name: Check a morning site
materials:
- morning_briefing_browser_site_check
---
Check one recurring morning site through Cognabot's browser JIT proxy, preserving URL/name, observed time, headline candidates, source notes, snapshot text, and any access gap. Use this for URL-backed site checks in the morning briefing; if the JIT proxy or browser service is unavailable, report the returned access gap instead of substituting a generic web summary.

In the `morning_briefing` practice, this site-check affordance is downstream of the two recurring source reads. Before invoking `morning_briefing_browser_site_check`, the current enactment should already show `read_user_email` reaching `gmail_user_search_threads` for unread mail and `read_morning_site_list` reaching `read_morning_briefing_sites` for the configured recurring sites, or should record the concrete Gmail/site-list access, auth, data, configuration, or material blocker that prevents one of those reads. If a pass reaches this affordance first, or reaches it after only the configured site-list read without the unread Gmail row, treat that as unfinished grounding: backfill the missing unread-mail and configured-site-list reads before interpreting the site, running another check, taking a live snapshot, or assembling the briefing. A browser check, invalid-URL result, supplied context, site-list-only path, or single-site observation does not substitute for either recurring-source gate.
