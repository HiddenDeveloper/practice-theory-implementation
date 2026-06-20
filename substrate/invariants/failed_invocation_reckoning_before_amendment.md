---
id: failed_invocation_reckoning_before_amendment
name: Failed invocation reckoning before amendment
status: tombstoned
trigger: pm_amend_element
mode: detect
friction_kind: rule_neglect
forbid_when:
  all:
  - step_exists:
      material_name: pm_*
      result_contains: '"error"'
  - any:
    - step_exists:
        material_name: pm_*
        result_contains: 'ValueError:'
    - step_exists:
        material_name: pm_*
        result_contains: 'TypeError:'
    - step_exists:
        material_name: pm_*
        result_contains: not reached for by affordance
    - step_exists:
        material_name: pm_*
        result_contains: unexpected keyword argument
  - not:
      any:
      - any_earlier_step_result_contains: changed no amendment choice
      - any_earlier_step_result_contains: did not change the chosen amendment
      - any_earlier_step_result_contains: irrelevant to the amendment
      - any_earlier_step_result_contains: irrelevant to this amendment
      - any_earlier_step_result_contains: remains a blocker
      - any_earlier_step_result_contains: blocks this amendment
message: A substrate amendment followed a failed invocation without an earlier explicit
  reckoning naming whether the failure changed the amendment, was irrelevant to it,
  or remains a blocker.
tombstoned_at: '2026-06-19T19:31:33.023974+00:00'
tombstone_reason: Friction 642 showed this invariant firing on error substrings quoted
  inside a successful read_pending_friction payload, not on a target-local failed
  invocation before amendment. The current declarative predicate surface uses broad
  result-substring checks and does not expose a way to distinguish nested Friction
  evidence from an actual failed invocation step, so the deterministic invariant is
  too blunt and should be retired rather than continue producing false positives.
---
This invariant addresses the determinable contract only where it is safely detectable from the invoked material surface: before `pm_amend_element`, a failed Practice Management material invocation (`pm_*`) must already have a visible failure-bearing reckoning, not first appear inside `mark_friction_addressed`. It requires a same-enactment `pm_*` step with an error-shaped result plus one of the known failure markers. It must not fire merely because failure text such as `ValueError:`, `TypeError:`, `not reached for by affordance`, or `unexpected keyword argument` appears inside quoted evidence returned by a successful read, including a `smoother_read_pending_friction` payload. Friction 628 confirmed this boundary for firing 623: the matched `ValueError:` / stale-material text was embedded in pending Friction evidence, and the reviewed Smoother enactment had no local failed amendment invocation before its amendment. Failed non-`pm_*` calls before amendment remain judgement or a more targeted invariant's concern until the predicate language can safely distinguish a step's own failure envelope from quoted evidence in read results.
