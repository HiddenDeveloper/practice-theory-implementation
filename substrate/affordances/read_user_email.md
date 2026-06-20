---
id: read_user_email
name: Read the user's email
materials:
- gmail_user_search_threads
- gmail_user_get_thread
- gmail_user_list_drafts
---
Search and read the user's Gmail threads and drafts for grounding. This is the correspondence record: use it to verify relationship context, factual claims, pending drafts, and thread state before attending or drafting. In correspondent work, `gmail_user_search_threads` is only an index into possible correspondence, not the correspondence evidence itself: when it returns a candidate user-mail thread for the message or request being handled, the immediate next grounding move is `gmail_user_get_thread` for the relevant thread in the same enactment before any `correspondence_offer`, stance invitation, draft language, draft creation, thread analysis, or final reply wording. If search or retrieval fails because of auth, refresh-token, access, data, or material failure, name that retrieval/access gap through `declare_correspondence_limit` or a narrowly limited `correspondence_offer` and confine the response to supplied message text or visible search metadata. Do not substitute test-mailbox search, another search attempt, or an ungrounded stance invitation for user-thread retrieval; the post-search trail should show either `gmail_user_get_thread` for the selected thread or an explicit retrieval/access limit.

In the `morning_briefing` practice, this affordance is the required unread-mail source gate, not optional context. The first source move of a morning briefing pass should be `read_user_email` reaching `gmail_user_search_threads` for unread mail. If the pass has already touched `read_morning_site_list`, `capture_morning_site_check`, a live snapshot, supplied context, or briefing assembly without this unread-mail read visible, stop the drift and backfill `gmail_user_search_threads` before any further interpretation or final briefing. If Gmail cannot be read, record the concrete auth, access, data, or material blocker in the briefing; do not treat the inbox as empty or let site-only evidence stand in for unread mail.
