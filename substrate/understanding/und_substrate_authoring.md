---
id: und_substrate_authoring
name: Authoring the substrate well
---
The substrate pool read is the first visible move of any substrate-authoring path. Before `pm_reload_seed_substrate`, `pm_check_documentation_impact`, any `pm_create_*` / `pm_amend_*`, evaluation work, or `pm_amend_bundle`, name the exact pool whose ids or current content the change will rely on (`teleo_affective`, `understanding`, `rules`, `affordances`, `materials`, or `evaluations`) and read it with `pm_read_pool` first; if several pools supply ids or content, read each before its corresponding write. A bundle description, a remembered id, prior Friction wording, or reload/documentation context is never a substitute for that read.

If an authoring, amendment, reload, documentation-impact, or bundle-wiring step has already appeared before the relevant pool read, the pass is interrupted: the only valid next move is that exact `pm_read_pool`, or a concrete substrate-surface blocker naming why the pool cannot be read. Do not continue into further stewardship writes, verification, or closure while the relied-on pool remains unread and unblocked. Reading the pool first is also what lets a new element reuse or condense an existing one instead of authoring a near-duplicate.
