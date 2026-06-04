---
id: list_recent_enactments
name: List recent enactments
materials:
- judge_list_recent_enactments
---
Return a discovery window of recent enactments, optionally filtered by bundle id. When a bundle id is supplied, the underlying trail read applies that bundle filter before the opened_at limit, so the result is a bounded bundle-local recent window rather than a global window narrowed afterward. Dispatch/inbox routing is closed_at-based, so absence from this opened_at listing is still not proof that a known dispatched enactment or its steps do not exist; when a target id is known from dispatch, direct reads remain the grounding path. When judging a dispatched target id, pair this with direct read_enactment_steps and preserve any list-versus-direct mismatch in observation_data.
