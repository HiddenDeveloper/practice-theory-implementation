---
id: capture_morning_site_check
name: Check a morning site
materials:
- morning_briefing_browser_site_check
check_materials:
- guard_morning_briefing_browser_site_check__practice_quality_affordance_coverage
---
Check one recurring morning site through Cognabot's browser JIT proxy, preserving URL/name, observed time, headline candidates, source notes, snapshot text, and any access gap. Use this for URL-backed site checks in the morning briefing; if the JIT proxy or browser service is unavailable, report the returned access gap instead of substituting a generic web summary.

In `morning_briefing` this site-check is downstream of the two recurring source reads. Before invoking `morning_briefing_browser_site_check`, the enactment should already show `read_user_email` reaching `gmail_user_search_threads` for unread mail and `read_morning_site_list` reaching `read_morning_briefing_sites` for the configured sites — or record the concrete Gmail/site-list access, auth, data, config, or material blocker that prevents one. If this affordance is reached before both source rows are visible, the pass is interrupted: the next move must be the missing source read or a concrete blocker for it, not another check, snapshot, assembly, synthesis, or closure. One source row, a browser check, or supplied context does not substitute for either gate.
