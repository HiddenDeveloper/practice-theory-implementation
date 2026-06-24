---
id: amend_pool_element
name: Amend a pool element
materials:
- pm_amend_element
preconditions:
- id: requires_pm_read_pool_before_pm_amend_element
  name: requires pm read pool before pm amend element
  trigger: pm_amend_element
  friction_kind: quality_affordance_coverage
  message: Practice Management invoked pm_amend_element without an earlier pm_read_pool
    grounding step in the same enactment.
  forbid_when:
    not:
      step_exists:
        material_name: pm_read_pool
  content: 'Migrated 2026-06-24T23:04:28+00:00 from 1 invariant(s): pm_amend_element_requires_prior_pool_read_953.'
---
Refine an existing teleo-affective, understanding, or rules element.
