---
id: about_user_profile
name: About the user profile
materials:
- consult_canonical_profile
---
Consult CanonicalProfile — the user's canonical landing node. Note the relationship to about_the_user: that aggregated read already returns this same CanonicalProfile node together with the self-model and shared context in a single read, so if you have already called about_the_user this session, this node is already in hand and re-fetching it here reproduces data you hold and adds nothing. Reach for this single-node read only when you deliberately want CanonicalProfile re-read on its own for freshness; to learn what is new since orientation, prefer the recall affordances over re-pulling this static landing node.
