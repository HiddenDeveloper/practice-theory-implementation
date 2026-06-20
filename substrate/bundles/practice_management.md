---
id: practice_management
name: Practice Management
mode: somatic
engagement: false
teleo_affective_ids:
- te_practice_management
understanding_ids:
- und_practice_management
- und_substrate_authoring
rules_ids:
- rule_pm_substrate_stewardship_starts_with_pool_read
- rule_pm_preview_before_apply
- rule_substrate_no_id_collision
- rule_substrate_amend_additively
- rule_pm_check_git_and_code_alignment
- rule_pm_update_affected_documentation
- rule_material_judgement_is_evaluable
- rule_adapt_after_failed_invocation
- rule_pm_read_pool_before_authoring
- rule_pm_invariants_do_not_substitute_for_pool_read
- rule_pm_pool_read_first_or_stop
affordance_ids:
- read_pool
- author_pool_element
- amend_pool_element
- author_affordance
- amend_affordance
- author_material
- amend_material
- author_bundle
- amend_bundle
- author_evaluation
- amend_evaluation
- reload_seed_substrate
- check_documentation_impact
evaluation_ids:
- eval_practice_management
---
Author and amend the substrate at runtime — pool elements, affordances, materials, evaluations, invariants, and bundles — on the user's behalf. Begin substrate stewardship by invoking `read_pool` / `pm_read_pool` for the pool surface the work will rely on; this is the entry gate before reload, documentation-impact checks, authoring, amendment, evaluation or invariant changes, and bundle wiring. If the intended surface cannot be identified or read, stop with that surface gap instead of proceeding from reload, documentation, memory, or a successful write.
