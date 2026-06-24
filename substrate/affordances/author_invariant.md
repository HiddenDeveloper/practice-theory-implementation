---
id: author_invariant
name: Author a governed invariant
materials:
- pm_create_invariant
preconditions:
- id: requires_pm_read_pool_before_pm_create_invariant
  name: requires pm read pool before pm create invariant
  trigger: pm_create_invariant
  friction_kind: practice_quality_affordance_coverage
  message: Practice Management invoked pm_create_invariant without an earlier pm_read_pool
    grounding step in the same enactment.
  forbid_when:
    not:
      step_exists:
        material_name: pm_read_pool
  content: 'Migrated 2026-06-24T23:04:28+00:00 from 1 invariant(s): pm_create_invariant_requires_prior_pool_read_971.'
---
Author a deterministic invariant when you find a determinable contract the Judge has been policing by hand. The invariant names a `trigger` material; whenever a closed enactment contains that step, the routing layer evaluates `forbid_when` against the enactment's earlier steps and, on violation, raises and auto-resolves the named `friction_kind` with no LLM. `forbid_when` is a declarative predicate built from `any_earlier_step_result_contains`, `step_exists` ({affordance_id?, material_name? glob, result_contains?}), `arg_present`, `arg_nonempty`, and `all`/`any`/`not`. Author only what is genuinely determinable from the recorded steps; leave to judgement what needs judgement.

This is substrate authoring for both Practice Management and Smoother. Before invoking `pm_create_invariant`, first use `read_pool` / `pm_read_pool` for the exact ordinary substrate pool whose ids or current content supply the contract being made deterministic, such as `rules`, `understanding`, `teleo_affective`, `affordances`, or `materials`. For invariant authoring, that pool read grounds the rule, affordance, material, or practice surface being encoded; if the new invariant's id or overlap with existing invariants is also being relied on, expose a current invariant/catalog surface when one is available, or stop with a concrete invariant-surface blocker. If a Smoother pass has already moved from `read_pending_friction` or reload context into `pm_create_invariant` without the relied-on pool row, the pass is ungrounded: do not continue into another write, reload, bundle wiring, verification, or `mark_friction_addressed` from that authoring attempt.
