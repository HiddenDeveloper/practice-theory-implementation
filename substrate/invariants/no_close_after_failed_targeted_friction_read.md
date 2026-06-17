---
id: no_close_after_failed_targeted_friction_read
name: No addressed mark after failed or empty targeted Friction read
status: active
trigger: smoother_mark_addressed
mode: detect
friction_kind: ungrounded_closure_attempt
forbid_when:
  any:
  - all:
    - any_earlier_step_result_contains: unexpected keyword argument 'friction_id'
    - not:
        step_exists:
          affordance_id: read_pending_friction
          result_contains: '"id"'
  - all:
    - any_earlier_step_result_contains: '[]'
    - step_exists:
        affordance_id: read_pending_friction
        result_contains: '[]'
    - not:
        step_exists:
          affordance_id: read_pending_friction
          result_contains: '"id"'
message: A Smoother enactment invoked mark_friction_addressed after an earlier targeted
  read_pending_friction call failed or returned an empty pending result, including
  the empty-basis/addressing variant where the terminal mark has no retrieved Friction
  content or observation_data as its basis; the concern still applies when that terminal
  mark itself fails because the Friction id is absent, no longer pending, or already
  addressed, leaving the failed closure attempt unresolved unless a later step records
  a disposition.
---
When a Smoother closure is triggered by smoother_mark_addressed, forbid the closure if an earlier targeted read_pending_friction call either failed with the historical unexpected-keyword TypeError or returned an empty pending result, and the enactment has no successful read_pending_friction result exposing a Friction id. This captures the determinable part of ungrounded_closure_attempt: an absent, failed, or empty targeted Friction read is not a grounded pending-Friction basis for an addressed mark, disposition, or closure attempt.

This invariant explicitly covers the empty-basis/addressing variant named by Friction 360: mark_friction_addressed after a targeted read_pending_friction result of [] leaves no retrieved Friction content or observation_data in the enactment as the basis for the terminal address action, even when the rationale says the requested id may be absent, no longer pending, or already handled elsewhere.

It also covers the failed-mark variant named by Friction 379: if the same terminal mark_friction_addressed attempt fails because the requested Friction id is not found or is already addressed, the enactment is still an ungrounded closure attempt over an unavailable target. The invariant intentionally stays at the recorded-step level available to the predicate language; same-id matching remains a judgement concern unless the predicate language later gains argument comparison.

Friction 383 names the same determinable shape as an unresolved_failed_invocation: the target enactment read friction_id 355, received an empty pending result, then ended on a mark_friction_addressed error saying friction 355 was not found or already addressed. This invariant addresses the future-contract part of that concern by detecting the attempted addressed mark that follows an empty or failed targeted Friction read with no retrieved Friction id, so the closure attempt is raised and auto-resolved deterministically instead of requiring the Judge to rediscover that failed terminal mark by hand.

Friction 406 names the same determinable shape under the provisional kind absent_friction_address_attempt: enactment b77f7d44-20dd-487c-a0f9-b7469db4e50d read friction_id 368, received an empty result, then attempted smoother_mark_addressed and got "friction 368 not found or already addressed". The current invariant keeps the canonical emitted friction_kind ungrounded_closure_attempt because the friction-kind vocabulary shows it as the higher-gravity kind, while this content records that the absent/no-longer-pending failed-mark variant is included in the same governed contract.

Friction 407 names the same determinable shape: enactment d7f7bc77-b096-407c-9b07-3f8237e04f9c read friction_id 369, received an empty result, then attempted smoother_mark_addressed and got "friction 369 not found or already addressed", closing with that failed mark and no later successful amendment, addressed mark, or explicit disposition. This invariant remains the governed home for that contract: future Smoother enactments with an empty targeted Friction read followed by an addressed-mark attempt and no successful read exposing a Friction id are raised and auto-resolved as ungrounded_closure_attempt rather than rediscovered by hand.

Friction 409 names the same governed shape after condensation to unresolved_failed_invocation: enactment 5baf4aac-928b-4b86-a68a-8797bf000df0 read friction_id 371, received an empty result, then attempted smoother_mark_addressed and got "friction 371 not found or already addressed", closing with that failed invocation and no later inspection, adaptation, alternate read, or explicit disposition. This amendment does not reconstruct or re-close Friction 371; it records that the already-governed empty-read plus failed-mark terminal pattern is the deterministic future-conduct repair for this concern.

Friction 411 names the same already-governed determinable shape after condensation to failed_closure_after_empty_read: enactment f5b685bf-0bee-40e9-a57c-da11de0a4775 read friction_id 374, received an empty result, then attempted smoother_mark_addressed and got "friction 374 not found or already addressed", with no later successful addressed mark, persisted amendment, or explicit post-failure disposition. The existing predicate remains sufficient: an empty targeted Friction read followed by an addressed-mark attempt without any later successful read exposing a Friction id is detected deterministically, while same-id matching and richer disposition quality remain judgement concerns.

Friction 412 names the same governed shape after condensation from failed_address_mark_after_empty_pending_read to ungrounded_closure_attempt: enactment 42a4fada-3db3-4ad6-a66e-8921bfcd585d read friction_id 375, received an empty result, then attempted smoother_mark_addressed and got "friction 375 not found or already addressed", leaving the target's final state grounded only by a failed mark step rather than a successful addressed closure. The existing predicate remains the right deterministic boundary: future enactments with an empty targeted Friction read followed by an addressed-mark attempt and no successful read_pending_friction result exposing a Friction id are raised and auto-resolved as ungrounded_closure_attempt; richer same-id and disposition-quality questions remain for judgement.

Friction 439 names the same governed shape after the Judge observed enactment bbf4a5ce-4311-421d-9a0a-443e6eef81fb read friction_id 389, receive an empty pending result, and then attempt smoother_mark_addressed, which failed with "friction 389 not found or already addressed" and left the enactment ending on that failed closure call. The existing predicate remains the smallest correct deterministic boundary: future addressed-mark attempts after an empty targeted Friction read and without a later successful read exposing a Friction id are raised and auto-resolved as ungrounded_closure_attempt, while the exact same-id and richer disposition-quality questions remain judgement concerns.

Friction 440 names the same governed shape after condensation from ungrounded_address_attempt to ungrounded_closure_attempt: enactment 3906f005-4fe1-4f2b-a8bd-7df7f718e21b read friction_id 390, received an empty result, then attempted smoother_mark_addressed and got "friction 390 not found or already addressed", leaving only a failed addressed-mark attempt over an unavailable target. The existing predicate remains the smallest correct deterministic boundary: future addressed-mark attempts after an empty targeted Friction read and without a later successful read exposing a Friction id are raised and auto-resolved as ungrounded_closure_attempt; same-id matching and richer disposition-quality questions remain judgement concerns.

Friction 441 names the same governed shape after condensation from failed_disposition_after_empty_read to ungrounded_closure_attempt: enactment b45c23db-9a0e-44f6-ac2c-5ac09dafda0e read friction_id 395, received an empty result, then attempted smoother_mark_addressed and got "friction 395 not found or already addressed", closing with no later successful read, amendment, or explicit disposition. The existing predicate remains the smallest correct deterministic boundary: future addressed-mark attempts after an empty targeted Friction read and without a later successful read exposing a Friction id are raised and auto-resolved as ungrounded_closure_attempt; same-id matching and richer disposition-quality questions remain judgement concerns.

Friction 442 names the same governed shape after condensation from ungrounded_address_attempt to ungrounded_closure_attempt: enactment f66c5181-8d88-416d-beeb-95d1dc24f244 read friction_id 397, received an empty result, then attempted smoother_mark_addressed and got "friction 397 not found or already addressed", leaving a failed closure attempt over an unavailable target. The existing predicate remains the smallest correct deterministic boundary: future addressed-mark attempts after an empty targeted Friction read and without a later successful read exposing a Friction id are raised and auto-resolved as ungrounded_closure_attempt; same-id matching and richer disposition-quality questions remain judgement concerns.

Friction 444 names the same governed shape after condensation from ungrounded_addressing_attempt to ungrounded_closure_attempt: enactment ef6a4ff4-d076-4eb9-a2cd-cd8e18b01821 read friction_id 399, received an empty pending result, then attempted smoother_mark_addressed for that same unavailable id and got "friction 399 not found or already addressed". The existing predicate remains the smallest correct deterministic boundary: future addressed-mark attempts after an empty targeted Friction read and without a later successful read exposing a Friction id are raised and auto-resolved as ungrounded_closure_attempt; same-id matching and richer disposition-quality questions remain judgement concerns.

Friction 446 names the same governed shape after condensation from failed_disposition_record to ungrounded_closure_attempt: enactment bf9e1f6e-930e-4448-a968-0a223134602c read friction_id 401, received an empty result, then attempted smoother_mark_addressed with the intended no-mutation disposition in the rationale, but the mark failed with "friction 401 not found or already addressed". The existing predicate remains the smallest correct deterministic boundary: future addressed-mark attempts after an empty targeted Friction read and without a later successful read exposing a Friction id are raised and auto-resolved as ungrounded_closure_attempt; carrying the intended disposition only inside the failed addressed-mark call is part of the terminal failed-closure shape this invariant governs, while same-id matching and richer disposition-quality questions remain judgement concerns.
