---
id: amend_bundle
name: Amend a bundle
materials:
- pm_amend_bundle
---
Change which pool ids an existing bundle selects. This is Practice Management substrate stewardship: before invoking `pm_amend_bundle`, first use `read_pool` / `pm_read_pool` for every pool whose ids or current content the bundle amendment relies on, such as `affordances`, `materials`, `rules`, `understanding`, or `teleo_affective`. If a write or bundle wiring step has already occurred without that read, stop with the concrete missing-pool-read blocker instead of continuing from persistence, reload context, remembered ids, or bundle prose.

Friction 1122 confirms the remaining Practice Management quality lapse can occur as bundle wiring after ungrounded affordance authoring: target enactment `8367059f-db1e-4e9e-b5fc-5528b101e612` moved from `pm_reload_seed_substrate` into `pm_create_affordance` and then `pm_amend_bundle` without any `pm_read_pool`, while comparison cases showed the pool-read path was reachable. For future `amend_bundle` use, treat a prior reload, documentation-impact check, `pm_create_*`, or `pm_amend_*` in the same stewardship path as an interruption point when the exact relied-on pools have not already been read. The immediate next visible move must be `pm_read_pool` for every pool supplying the ids or current content being wired, including `affordances` and `materials` when wiring a newly authored affordance; if the ungrounded write has already occurred, stop with a concrete missing-pool-read blocker instead of wiring the bundle, verifying, reloading, checking documentation, closing, or explaining from the ungrounded write result.
