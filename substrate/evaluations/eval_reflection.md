---
id: eval_reflection
name: Reflection - objective delivery
practice_id: reflection
objective_ref: te_reflection
derived_from: reflection@practice_missing_evaluation_459
window: 8
signals:
- id: records_reflection_verbatim_material
  kind: affordance_coverage
  required_materials:
  - store_reflection
  detail: Reflection should use the reflection storage material when the user offers
    a reflection, because the objective is to write down and preserve the user's own
    words rather than merely discuss or analyze them.
- id: stored_reflection_outcome_present
  kind: outcome_presence
  outcome_materials:
  - store_reflection
  max_consecutive_without: 3
  detail: The practice exists to record reflections. Several consecutive enactments
    with no stored reflection may be legitimate if the user never offered one, but
    it is a measurable stall for the Judge to inspect.
- id: reflection_words_not_transformed
  kind: recurring_summary_marker
  markers:
  - paraphrase
  - summarize
  - summary
  - rewrote
  - rephrased
  - analysis instead of record
  - not stored
  max_consecutive: 3
  detail: Repeated trail summaries indicating paraphrase, summary, rewriting, analysis
    instead of recording, or failure to store suggest the practice is drifting away
    from the verbatim-reflection objective and should be judged.
---

