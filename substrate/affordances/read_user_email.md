---
id: read_user_email
name: Read the user's email
materials:
- gmail_user_search_threads
- gmail_user_get_thread
- gmail_user_list_drafts
---
Friction 768 confirms the remaining `grounds_correspondent_before_offering` miss is the concrete live-thread-id case: when `gmail_user_search_threads` returns a specific user Gmail thread id, the next correspondent grounding move must be `gmail_user_get_thread` for that live user thread before any closure, thread analysis, reply wording, stance invitation, draft, or correspondence offer. `gmail_test_search_threads` may be useful as diagnostic context, but it is never the grounding substitute for the user's thread body. Access-bound search failures remain retrieval-limit cases to name explicitly; a successful live search with a reachable thread id is unfinished until the live thread body is read or a concrete retrieval blocker is declared.

Friction 792 confirms a `morning_briefing` quality stall: recent passes repeatedly skipped the unread-mail source read, and often the usual-site list, even though those reads are the briefing's starting basis. In `morning_briefing`, treat this affordance reaching `gmail_user_search_threads` for unread mail as the first visible source-read move before browser site checks, live market snapshots, synthesis, or `assemble_morning_briefing`. If Gmail cannot be reached, record the concrete auth, access, data, configuration, or material blocker and limit the briefing accordingly. After the unread-mail read or blocker is visible, the next source-grounding move is `read_morning_site_list` / `read_morning_briefing_sites` for the configured usual sites, or its concrete blocker; browser checks and final prose do not substitute for either recurring source read.
