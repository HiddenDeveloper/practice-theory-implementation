---
id: list_recent_enactments
name: List recent enactments
materials:
- judge_list_recent_enactments
---
Return a discovery window of recent enactments, optionally filtered by bundle id. The underlying trail read takes a global opened_at-ordered recent window first and then applies the bundle filter; dispatch/inbox routing is closed_at-based, so absence from this listing is a discoverability/index signal rather than proof that a known dispatched enactment or its steps do not exist. When judging a dispatched target id, pair this with direct read_enactment_steps and preserve any list-versus-direct mismatch in observation_data.
