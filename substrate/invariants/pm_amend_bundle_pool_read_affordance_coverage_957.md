---
id: pm_amend_bundle_pool_read_affordance_coverage_957
name: Practice Management bundle wiring requires pool read for affordance coverage
status: active
trigger: pm_amend_bundle
mode: detect
friction_kind: practice_quality_affordance_coverage
forbid_when:
  not:
    step_exists:
      material_name: pm_read_pool
message: Practice Management invoked pm_amend_bundle without an earlier pm_read_pool
  in the same enactment, so the uses_substrate_authoring_surface affordance-coverage
  contract was breached at bundle wiring.
---
Friction 957 confirms that the Practice Management `uses_substrate_authoring_surface` affordance-coverage concern is still being emitted by the quality layer even though prose rules and narrower substrate-authoring invariants already state the pool-read gate. The determinable part named in the target enactment is bundle wiring after reload and authoring with no same-enactment `pm_read_pool`. This invariant triggers on `pm_amend_bundle` and forbids that trigger when no earlier `pm_read_pool` step exists, raising and auto-resolving the same `practice_quality_affordance_coverage` kind so the repeated contract is handled deterministically rather than rediscovered by the Judge. It intentionally checks only presence of the pool-read row; whether the exact pool was sufficient remains judgement-shaped.
