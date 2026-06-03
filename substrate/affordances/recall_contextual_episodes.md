---
id: recall_contextual_episodes
name: Recall contextual episodes
materials:
- recall_contextual_episodes
---
Read episodic memory by structured filters such as canonical pillar, category, role, provider, conversation, date, or sequence range. The date and sequence filters are paired bounds: pass date_from AND date_to together (or sequence_from AND sequence_to) to sweep an entire window in one call, rather than walking a single bound backward across repeated probes. Prefer one bounded recall over the window of interest to many narrow ones; if a window returns little, widen the bounds or switch to a relevance-keyed recall (recall_relevant_episodes) instead of re-issuing the same filter with a marching cut-off.
