---
id: author_affordance
name: Author an affordance
materials:
- pm_create_affordance
---
Add a new affordance to the affordances pool, referencing one or more existing materials. This is Practice Management substrate stewardship: before invoking `pm_create_affordance`, first use `read_pool` / `pm_read_pool` for `affordances` and for `materials` when the new affordance relies on existing material names. If that pool read is absent and cannot be produced, stop with the concrete missing-pool-read blocker instead of authoring from reload context, remembered ids, or bundle prose.

Friction 1021 confirms the remaining miss can enter through reload before creating an affordance: target enactment `8367059f-db1e-4e9e-b5fc-5528b101e612` reached `pm_reload_seed_substrate`, then `pm_create_affordance`, then `pm_amend_bundle` without the required `pm_read_pool`. Treat reload-first context as interrupted, not as grounding. If `pm_reload_seed_substrate` or `pm_check_documentation_impact` has appeared before this affordance and the relied-on `affordances`/`materials` pool row is absent, the only valid next Practice Management move is the exact `pm_read_pool` row or a concrete missing-pool-read blocker; do not invoke `pm_create_affordance`, proceed to bundle wiring, verify, reload again, or close from reload/documentation context alone.
