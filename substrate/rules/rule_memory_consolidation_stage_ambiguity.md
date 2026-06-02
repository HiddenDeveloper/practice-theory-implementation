---
id: rule_memory_consolidation_stage_ambiguity
name: Stage ambiguous canonical changes
---
Do not silently overwrite canonical landing nodes. When a landing-node field has clearly drifted and the correction is source-backed and uncontested, update that field with `update_canonical_field` (append to a list field, replace a scalar) — these writes are preview-captured and applied only on approval, so this is a deliberate correction, not a silent overwrite. Otherwise prefer additive non-episodic memory attached to an anchor. When evidence conflicts, the change is contested or high-impact in a contested way, or it touches identity wording (CanonicalProfile name / public_handles), stage the candidate for review instead of writing it.
