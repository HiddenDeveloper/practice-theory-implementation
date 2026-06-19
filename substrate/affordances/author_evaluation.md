---
id: author_evaluation
name: Author an evaluation spec
materials:
- pm_create_evaluation
---
Author a new evaluation spec for a practice — its declarative measure of whether it delivers its objective. Invoke with the reached material `pm_create_evaluation`. The spec is data, not code: `signals` is a list of generic signal kinds (`affordance_coverage`, `outcome_presence`, `shape_repetition`, `recurring_summary_marker`) parameterised for the practice, and `objective_ref` should name one of the practice bundle's teleo-affective ids so the evaluator demonstrably measures the practice's declared purpose rather than something incidental. Authoring the spec does not by itself activate it — wire its id into the practice bundle's `evaluation_ids` (via `amend_bundle`) so the engine and routing pick it up. Where a practice is genuinely not yet measurable, say so in the spec body rather than authoring a vacuous one.
