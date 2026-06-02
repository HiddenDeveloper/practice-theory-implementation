---
id: update_canonical_field
name: Update a canonical landing-node field
materials:
- update_canonical_field
---
Update a field on a canonical landing node itself — not a satellite. The engagement projection reads the landing nodes, so this is how a source-backed drift correction actually reaches the situated frame. `op='append'` adds to a list-valued field (e.g. active_projects, recent_decisions, next_actions, open_threads, blockers, public_handles), deduped; `op='replace'` sets a scalar field (e.g. summary, current_focus). Cite the evidence in `sources`. For genuinely contentious, conflicting, or identity-sensitive rewordings (e.g. CanonicalProfile name/public_handles), stage a candidate for review instead of writing directly.
