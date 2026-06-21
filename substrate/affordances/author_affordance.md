---
id: author_affordance
name: Author an affordance
materials:
- pm_create_affordance
---
Add a new affordance to the affordances pool, referencing one or more existing materials. This is Practice Management substrate stewardship: before invoking `pm_create_affordance`, first use `read_pool` / `pm_read_pool` for `affordances` and for `materials` when the new affordance relies on existing material names. If that pool read is absent and cannot be produced, stop with the concrete missing-pool-read blocker instead of authoring from reload context, remembered ids, or bundle prose.
