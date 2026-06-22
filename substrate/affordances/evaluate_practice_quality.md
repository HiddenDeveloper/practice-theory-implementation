---
id: evaluate_practice_quality
name: Evaluate a practice's quality
materials:
- evaluate_quality_for_practice
---
Measure whether a practice is delivering its objective, by running its own evaluation layer over its real trail. Invoke this affordance with the reached material `evaluate_quality_for_practice`, passing the practice (bundle) id as `name`; optionally pass `window` to override how many recent closed enactments are considered. The result is a measurement, not a verdict: per-signal `pass`/`concern` findings with the evidence each rests on. A `concern` is a candidate for quality friction, not proof of one — examine the evidence and judge whether it is a genuine stall or acceptable variation (holding, legitimately periodic work) before naming any Friction. A result with `spec_present: false` and `newness_signal: true` means the practice has no evaluation layer yet and is not measurable until one is authored. This affordance is read-only: it neither emits Friction nor changes substrate.
