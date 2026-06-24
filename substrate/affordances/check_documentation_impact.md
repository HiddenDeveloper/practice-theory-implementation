---
id: check_documentation_impact
name: Check documentation impact
materials:
- pm_check_documentation_impact
check_materials:
- requires_pm_read_pool_before_pm_check_documentation_impact
---
Search README, docs, and social-media markdown for references likely affected by recently created, amended, tombstoned, or removed substrate ids/files before declaring the substrate change complete.

For Practice Management substrate stewardship, this documentation-impact check is downstream of the pool-grounding row. Before invoking `pm_check_documentation_impact`, first use `read_pool` / `pm_read_pool` for the exact pool whose ids or current content the documentation check relies on (`teleo_affective`, `understanding`, `rules`, `affordances`, or `materials`). If reload, authoring, amendment, evaluation/invariant work, or bundle wiring has already occurred without that relevant pool read, treat the pass as interrupted: the immediate next visible move is the exact `pm_read_pool` or a concrete substrate-surface blocker, not this documentation check or closure from reload/documentation context.
