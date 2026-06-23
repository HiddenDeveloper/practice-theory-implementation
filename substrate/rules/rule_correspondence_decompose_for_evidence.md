---
id: rule_correspondence_decompose_for_evidence
name: Decompose for evidence
---
Friction 1039 confirms the same `grounds_correspondent_before_offering` quality concern on target enactment `408e9d39-f733-4d66-b00e-5100f1ad3036`: a reachable live Gmail thread id (`19e96aa1f9d1a621`) was found, but the pass stopped at live and test search snippets instead of retrieving the selected live thread with `read_user_email` / `gmail_user_get_thread`. For future correspondent passes, once a live Gmail search returns a thread id that could ground the correspondence, the next grounding move must retrieve that live thread or record the exact retrieval blocker. A test-mailbox search result, snippet-only search metadata, or authorization-error context from neighboring cases must not be treated as a substitute for live-thread retrieval; any response before retrieval must be explicitly limited to supplied text, visible search metadata, or the named access limit.
