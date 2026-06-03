---
id: recall_recent_engagement
name: Recall recent engagement
materials:
- recall_recent_episodes
---
Read the most recent episodic memory turns, optionally scoped to a conversation, role, or date range. If you are widening only the same recency window, make one call at the widest limit you expect to need and inspect that result, rather than issuing immediate nested calls such as limit=1, then 3, then 5. Re-call only when a distinct retrieval need appears: a different scope, role, date range, conversation, or a deliberately changed limit after inspecting the wider result. At engagement bootstrap, use enough recent context to situate awareness in companionship with the user; do not cap the opening recall at limit=1 unless the user's request explicitly only needs the single latest turn, and do not close the engagement on that one-episode basis when broader situating context is needed.
