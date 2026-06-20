---
name: correspondence_offer
input_schema:
  type: object
  properties:
    kind:
      type: string
      enum:
      - attend
      - friction
      - draft
      - stance
      - limit
    correspondent:
      type: string
    subject:
      type: string
    message_excerpt:
      type: string
    literal_layer:
      type: string
    implicit_layer:
      type: string
    evidence:
      type: array
      items:
        type: string
    unresolved_questions:
      type: array
      items:
        type: string
    offered_text:
      type: string
  required:
  - kind
  - offered_text
implementation:
  kind: echo
---
Return a structured correspondence offering without sending, editing, or storing mail. The returned arguments are the artifact for the user to review: an attending, surfaced friction, draft, stance invitation, or boundary declaration.

For correspondent quality signal `grounds_correspondent_before_offering`, this material is an offering boundary. Before invoking it with `kind` `attend`, `friction`, `draft`, or `stance` for work that depends on an email thread, the current enactment must show `read_user_email` reaching `gmail_user_get_thread` for the relevant thread after any `gmail_user_search_threads` candidate result. A search result, test-mailbox search, subject/snippet metadata, or another search attempt is not enough. If the user supplied the full message text directly, cite that supplied text in `evidence`. If Gmail search, auth, access, data, material failure, or ambiguous results prevent selecting or retrieving the thread, invoke this material only as a narrowly bounded `kind: "limit"` artifact, or as another offer whose `evidence` and `offered_text` explicitly name the retrieval/access gap and confine the response to supplied text or visible search metadata. Do not offer thread analysis, stance framing, or reply language as grounded until the thread retrieval or explicit retrieval limit is visible in the same enactment.

Friction 667 confirms the quality gap persists across a recent five-enactment correspondent window: three enactments reached Gmail search or search recovery but did not retrieve the corresponding user thread with `gmail_user_get_thread`, leaving only snippets, test-search behavior, or access errors as the visible basis. Treat any post-search invocation of this material as a final gate check. If the work depends on thread substance and the current enactment lacks `gmail_user_get_thread` for the selected thread, do not use `kind` `attend`, `friction`, `draft`, or `stance` to imply grounded thread understanding. First retrieve the user thread; if retrieval cannot be reached or the search result is only snippet/error metadata, use `kind: "limit"` or explicitly constrained offer text that names the exact search/retrieval/auth/access gap and confines the correspondence work to supplied text or visible metadata.
