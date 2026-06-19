---
id: eval_practice_management
name: Practice Management - objective delivery
practice_id: practice_management
objective_ref: te_practice_management
derived_from: practice_management@practice_missing_evaluation_458
window: 8
signals:
- id: uses_substrate_authoring_surface
  kind: affordance_coverage
  required_materials:
  - pm_read_pool
  detail: Practice Management should inspect the current substrate before authoring
    or amending it, so the user's requested change is grounded in the shared substrate
    rather than guessed from memory.
- id: produces_persisted_substrate_change
  kind: outcome_presence
  outcome_materials:
  - pm_create_element
  - pm_amend_element
  - pm_create_affordance
  - pm_amend_affordance
  - pm_create_material
  - pm_amend_material
  - pm_create_bundle
  - pm_amend_bundle
  - pm_create_evaluation
  - pm_amend_evaluation
  - pm_create_invariant
  - pm_amend_invariant
  - pm_tombstone_invariant
  max_consecutive_without: 4
  detail: The practice's objective is to author and amend substrate at runtime on
    the user's behalf; several consecutive enactments with no persisted authoring
    material suggest it is not delivering that objective.
- id: not_repeating_same_management_shape
  kind: shape_repetition
  max_identical: 4
  detail: Identical Practice Management enactment shapes repeated many passes running
    suggest rote authoring behavior rather than deliberate substrate stewardship.
---

