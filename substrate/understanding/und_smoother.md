---
id: und_smoother
name: Friction, interpretation, and amendment
---
Friction comes from the Judge and waits in the trail until a Smoother addresses it. Each Friction has a kind, a freeform content describing what was observed, and optional observation_data carrying structured evidence. The Smoother's work is to interpret what was named and apply a substrate amendment that addresses it — not anything more.

The Judge names a Friction to give it form, but that name is provisional. Part of smoothing is to consider the name and, when it would gain better form, condense it: read the Friction-kind vocabulary (read_friction_kinds) to see which kinds already carry gravity, and rename the Friction (rename_friction) toward an existing kind when one fits — re-wording its content to match if needed. This is the condensation that keeps the vocabulary from sprawling into one-off names; the high-count kinds are the canonical forms, the single-occurrence tail are provisional names awaiting condensation. Renaming is optional — leave a name that already fits — and the rename is recorded as a step, so the original naming is preserved on the trail.

Read pending Friction first. Then, depending on what was named:
  - narrow_engagement on bundle X: the enactment used few of the bundle's affordances. Consider amending X's description (via amend_bundle) to make the broader surface more visible, or adding a rule to X (via author_pool_element + amend_bundle) that invites exploration when the question is ambiguous.
  - rule_neglect on bundle X with rule R: the rule did not shape the enactment. Consider sharpening R's content (via amend_pool_element) so its application is clearer, or renaming it to make its applicability more salient.
  - repetition: a single affordance was invoked many times. Consider whether a new affordance that aggregates would be useful — author it (author_pool_element on the affordance pool is not quite right; use the underlying pm_create_* primitive Practice Management exposes).
  - missing_bundle for a historical engagement id such as `user_focused_engagement`: preserve the retirement boundary. Do not recreate the old id as a switchable bundle just to satisfy read_bundle; current engagement lives as `continuous_self` outside the normal practice catalog. Use git/file history as the historical source of truth when available, then prefer a small understanding/rule that explains the alias history, or mark the Friction addressed when the gap is adequately documented and no future projection should use the old id.
These are starting points. The Smoother may apply different amendments when the Friction calls for it. The rule is to address what was named and stop.

Substrate amendments propagate to every future projection; they do not affect projections already in use. The amendment should be the smallest one that addresses the Friction. If the exact Friction is already adequately answered by current substrate, or if no mutation is appropriate, make that no-mutation rationale explicit in the enactment before closure instead of treating read-only inspection as completion. Finally, mark the Friction addressed.
