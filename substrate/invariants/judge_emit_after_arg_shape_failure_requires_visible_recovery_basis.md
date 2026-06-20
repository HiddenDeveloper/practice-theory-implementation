---
id: judge_emit_after_arg_shape_failure_requires_visible_recovery_basis
name: Judge emit after argument-shape failure requires visible recovery basis
status: tombstoned
trigger: judge_emit_friction
mode: detect
friction_kind: recovery_basis_not_trail_visible
forbid_when:
  all:
  - any_earlier_step_result_contains: unexpected keyword argument
  - not:
      any:
      - step_exists:
          affordance_id: discover_affordances
      - step_exists:
          affordance_id: current_practice
message: A Judge emit_friction step followed an earlier argument-shape failure, but
  the Judge enactment being evaluated does not show a visible schema/projection affordance
  read establishing the corrected argument shape before the emission. Ordinary inspected-target
  evidence reads such as list_recent_enactments, read_enactment_steps, or read_bundle
  do not by themselves establish a corrected material argument shape for the Judge's
  own final-outcome invocation.
tombstoned_at: '2026-06-19T14:58:42.197759+00:00'
tombstone_reason: 'Friction 592 showed this invariant was mismatched to the concern
  it was authored to close: its predicate only checked for any qualifying recovery-basis
  read anywhere earlier in the Judge enactment, while Friction 567 required a visible
  recovery basis between the failed emit_friction argument-shape error and the corrected
  emission, or an exact visible recovery step. The current declarative invariant vocabulary
  does not express that ordered recovery window, so keeping this invariant would permit
  the same overclaimed closure pattern while appearing to resolve it deterministically.'
---
When a Judge enactment recovers from an argument-shape failure before emitting Friction, the corrected `judge_emit_friction` step must be preceded in that same Judge enactment's visible step sequence by a schema or projection affordance read that can actually establish the corrected material argument shape, such as `discover_affordances` or `current_practice`. The evaluated target for this invariant is the Judge enactment that contains the failed and corrected final-outcome calls. The inspected target enactment named inside the emitted Friction's observation_data is a separate evidence subject: ordinary inspected-target reads (`list_recent_enactments`, `read_enactment_steps`, `read_bundle`) may ground the judgement about practitioner conduct, but they do not by themselves expose the corrected argument key for the Judge's own final-outcome material and therefore do not satisfy this recovery-basis invariant. This amendment addresses Friction 575 by making the trail-visible recovery basis boundary explicit: if the corrected emission cites `discover_affordances` or another schema/projection read, that read must be visible in the Judge enactment being evaluated before the corrected outcome, not merely asserted in the outcome or confused with evidence read from the inspected target.
