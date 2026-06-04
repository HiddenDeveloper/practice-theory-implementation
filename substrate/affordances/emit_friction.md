---
id: emit_friction
name: Emit a Friction observation
materials:
- judge_emit_friction
---
Record a Friction observation against an enactment, with a kind, a freeform content description, and optional structured evidence. Observation only; no remedies. When the Judge has completed judgement-oriented reads but cannot record a warranted no-finding because no dedicated no-finding surface is projected, use this same observation surface as the active fallback closure surface to record that missing closure surface narrowly, e.g. kind `no_finding_surface_missing`, with the inspected target id and read/list basis in observation_data instead of ending silently. That fallback emission is the required recorded judgement outcome for the Judge enactment in this surface-limited case, so the trail can distinguish a completed no-finding attempt from an enactment that stopped after inspection; it is not a no-finding verdict about the inspected target.
