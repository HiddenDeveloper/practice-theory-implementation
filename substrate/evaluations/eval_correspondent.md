---
id: eval_correspondent
name: Correspondent - objective delivery
practice_id: correspondent
objective_ref: te_correspondence_offer_not_commit
derived_from: correspondent@friction-456
window: 8
signals:
- id: grounds_correspondent_before_offering
  kind: affordance_coverage
  required_materials:
  - gmail_user_search_threads
  - gmail_user_get_thread
  detail: Correspondent should ground the person, thread, and relationship context
    before offering reply language, friction, stance, or limits. Without thread search
    and retrieval, the practice cannot show that its offering is anchored in reachable
    correspondence rather than guessed intimacy.
- id: produces_reviewable_correspondence_artifacts
  kind: outcome_presence
  outcome_materials:
  - correspondence_offer
  - gmail_user_create_draft
  - gmail_user_update_draft
  max_consecutive_without: 6
  detail: The practice exists to offer reviewable correspondence artifacts without
    committing on the user's behalf. A long run without an attending, surfaced friction,
    draft, stance invitation, limit, or Gmail draft artifact may be a stall for the
    Judge to inspect.
- id: not_repeating_correspondence_shape_without_progress
  kind: shape_repetition
  max_identical: 4
  detail: Identical correspondence enactment shapes repeated across many passes suggest
    the practitioner may be cycling through the same moves rather than attending to
    the live correspondent, relationship, and user's choice boundary.
- id: correspondence_gaps_do_not_persist_unresolved
  kind: recurring_summary_marker
  markers:
  - missing thread
  - gmail access gap
  - ungrounded
  - awaiting user stance
  - cannot verify
  - review needed
  max_consecutive: 5
  detail: Repeated disclosure of the same correspondence evidence, access, grounding,
    or awaiting-stance gap is useful only if the gap remains visible and eventually
    resolves; repeated markers beyond the threshold merit judgement.
---

