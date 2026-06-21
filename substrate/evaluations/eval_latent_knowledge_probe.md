---
id: eval_latent_knowledge_probe
name: Latent Knowledge Probe evaluation
practice_id: latent_knowledge_probe
objective_ref: te_latent_knowledge_probe
window: 6
signals:
- id: protocol_and_judgment_coverage
  kind: affordance_coverage
  required_materials:
  - latent_probe_design_protocol
  - latent_probe_record_trial
  - latent_probe_confidence_judgment
- id: confidence_judgment_present
  kind: outcome_presence
  outcome_materials:
  - latent_probe_confidence_judgment
  max_consecutive_without: 3
---

