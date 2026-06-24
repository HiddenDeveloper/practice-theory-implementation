---
id: check_documentation_impact
name: Check documentation impact
materials:
- pm_check_documentation_impact
preconditions:
- id: requires_pm_read_pool_before_pm_check_documentation_impact
  name: requires pm read pool before pm check documentation impact
  trigger: pm_check_documentation_impact
  friction_kind: quality_affordance_coverage
  message: Practice Management invoked pm_check_documentation_impact before a visible
    pm_read_pool for the relied-on substrate pool.
  forbid_when:
    not:
      step_exists:
        material_name: pm_read_pool
  content: 'Migrated 2026-06-24T23:04:28+00:00 from 4 invariant(s): pm_check_documentation_impact_requires_prior_pool_read,
    pm_check_documentation_impact_requires_prior_pool_read_861, pm_documentation_impact_requires_pool_read….'
---
Search README, docs, and social-media markdown for references likely affected by recently created, amended, tombstoned, or removed substrate ids/files before declaring the substrate change complete.

For Practice Management substrate stewardship, this documentation-impact check is downstream of the pool-grounding row. Before invoking `pm_check_documentation_impact`, first use `read_pool` / `pm_read_pool` for the exact pool whose ids or current content the documentation check relies on (`teleo_affective`, `understanding`, `rules`, `affordances`, or `materials`). If reload, authoring, amendment, evaluation/invariant work, or bundle wiring has already occurred without that relevant pool read, treat the pass as interrupted: the immediate next visible move is the exact `pm_read_pool` or a concrete substrate-surface blocker, not this documentation check or closure from reload/documentation context.
