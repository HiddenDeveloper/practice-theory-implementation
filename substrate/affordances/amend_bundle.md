---
id: amend_bundle
name: Amend a bundle
materials:
- pm_amend_bundle
---
Change which pool ids an existing bundle selects. This is Practice Management substrate stewardship: before invoking `pm_amend_bundle`, first use `read_pool` / `pm_read_pool` for every pool whose ids or current content the bundle amendment relies on, such as `affordances`, `materials`, `rules`, `understanding`, or `teleo_affective`. If a write or bundle wiring step has already occurred without that read, stop with the concrete missing-pool-read blocker instead of continuing from persistence, reload context, remembered ids, or bundle prose.
