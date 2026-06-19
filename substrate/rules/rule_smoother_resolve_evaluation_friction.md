---
id: rule_smoother_resolve_evaluation_friction
name: Resolve evaluation friction at the right layer
---
Friction from the practice-evaluation regime is addressed by layer, and the layer matters:

- `practice_missing_evaluation` — the practice has no measure of whether it delivers its objective. Author one (`author_evaluation`): choose generic signal kinds that exercise the practice's purpose, set `objective_ref` to one of the practice bundle's teleo-affective ids, then wire the spec into the bundle's `evaluation_ids` (`amend_bundle`). The spec is only active once wired, and the wire is gated: it is rejected unless the objective is covered. If the practice is genuinely not yet measurable, say so honestly in the spec body rather than authoring a hollow measure.
- `evaluation_objective_uncovered` — a spec exists but does not measure the practice's declared objective. Fix the spec (`amend_evaluation`): correct its `objective_ref` to a real teleo-affective id of the bundle and ensure its signals exercise that objective. Do not delete the practice's objective to make the friction disappear.
- a practice-quality concern the Judge has confirmed (a stall, unresolved drift, an objective the practice is failing) — this is the practitioner underperforming, not a faulty measure. Fix it by improving the **practice the practitioner apprentices into**: sharpen a rule, add an understanding, or adjust the teleo-affective of that practice's bundle (`amend_pool_element` + `amend_bundle`). Do NOT resolve a genuine quality concern by weakening or removing the evaluation spec that surfaced it — that silences the measure instead of improving the practice, and the next enactment inherits the unimproved bundle.

In every case apply the smallest amendment that addresses what the Friction names, then mark it addressed.
