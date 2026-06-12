---
id: no_invalid_material_invocation_before_no_finding
name: No invalid material invocation before no-finding closure
status: active
trigger: judge_record_no_finding
mode: detect
friction_kind: invalid_material_invocation
forbid_when:
  any_earlier_step_result_contains: not reached for by affordance
message: A Judge enactment reached judge_record_no_finding only after an earlier invalid
  material-name invocation; use the material names exposed by the projection rather
  than stale aliases such as judge_no_finding_outcome.
---
When a Judge enactment reaches `judge_record_no_finding`, forbid closure if any earlier step result contains `not reached for by affordance`. That validation error means the enactment first invoked an affordance with an invalid or stale material name, including the determinable pattern where a material name mirrors the affordance id (`judge_no_finding_outcome`) instead of the reached material name (`judge_record_no_finding`) listed by the projection. The invariant raises and auto-resolves `invalid_material_invocation` deterministically for that closure surface so the Judge does not need to rediscover the same stale-alias invocation by hand.
