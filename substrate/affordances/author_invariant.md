---
id: author_invariant
name: Author a governed invariant
materials:
- pm_create_invariant
---
Author a deterministic invariant when you find a determinable contract the Judge has been policing by hand. The invariant names a `trigger` material; whenever a closed enactment contains that step, the routing layer evaluates `forbid_when` against the enactment's earlier steps and, on violation, raises and auto-resolves the named `friction_kind` with no LLM. `forbid_when` is a declarative predicate built from `any_earlier_step_result_contains`, `step_exists` ({affordance_id?, material_name? glob, result_contains?}), `arg_present`, `arg_nonempty`, and `all`/`any`/`not`. Author only what is genuinely determinable from the recorded steps; leave to judgement what needs judgement.
