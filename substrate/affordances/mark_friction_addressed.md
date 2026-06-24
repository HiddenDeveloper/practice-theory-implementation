---
id: mark_friction_addressed
name: Mark Friction addressed
materials:
- smoother_mark_addressed
check_materials:
- guard_smoother_mark_addressed__non_persisted_amendment_marked_addressed
- guard_smoother_mark_addressed__unavailable_affordance_invocation
- guard_smoother_mark_addressed__ungrounded_closure_attempt
---
Mark a Friction observation as addressed by this Smoother enactment. For dispatched Smoother work, invoke this only after the same enactment has recorded a targeted read of that friction_id, so the readable trail exposes the Friction content and observation_data as the resolution basis; a truncated batch read is not enough. The mark must also carry a concise rationale: after a substrate amendment, name the persisted amended id or surface; when no mutation is made, name the explicit no-mutation, already-addressed, absent/no-longer-pending, failed-persistence, or blocker basis. Do not use this affordance for inspection-only closure with no visible judgement basis. (The specific case of closing after an amendment that reported persisted=false is now enforced deterministically by the governed invariant `no_close_on_unpersisted_amendment` — detected and resolved without a Judge dispatch — so this prose need not be policed by hand.)
