---
id: read_user_email
name: Read the user's email
materials:
- gmail_user_search_threads
- gmail_user_get_thread
- gmail_user_list_drafts
---
For `morning_briefing`, this is the mandatory opening source-baseline row, not an optional correspondence read. When a morning-briefing pass begins or touches any briefing surface, the next visible move must be this affordance reaching `gmail_user_search_threads` for unread mail, or a concrete Gmail auth/access/account/config/data/query/material blocker for that row. If any downstream briefing work (configured-site read, site check, market snapshot, interpretation, grouping, assembly, handoff, closure) has appeared while unread Gmail is absent and unblocked, the pass is interrupted: do not proceed until this unread-mail row or its blocker is visible.

For `correspondent`, this is the thread-grounding surface, not a search-snippet surface. Once a live user search (`gmail_user_search_threads`) returns a usable thread id, the next email-grounding move must be `read_user_email` reaching `gmail_user_get_thread` for that selected thread, or a concrete Gmail auth/config/access/data/ambiguous-selection/material blocker that confines the response to supplied text or visible search metadata. Do not detour into test-mailbox search, relationship recall, stance/draft/offering, verification, or final correspondence from snippets alone while the selected live thread remains unread and unblocked.
