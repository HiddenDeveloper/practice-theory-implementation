---
id: latent_knowledge_probe
name: Latent Knowledge Probe
mode: somatic
engagement: false
teleo_affective_ids:
- te_latent_knowledge_probe
understanding_ids:
- und_latent_knowledge_probe
rules_ids:
- rule_latent_probe_not_truth_detector
- rule_latent_probe_convergence_before_claim
- rule_latent_probe_controls_first
- rule_latent_probe_confidence_labels
affordance_ids:
- design_latent_probe_protocol
- record_latent_probe_trial
- run_transformerlens_activation_probe
- judge_latent_probe_confidence
evaluation_ids:
- eval_latent_knowledge_probe
---
Investigate an open-weight patient model through disciplined confidence-and-evidence practice. Start by designing the protocol and controls, then run scaffolded relational elicitation while recording mechanistic observations and causal interventions, and close each candidate claim with a bounded confidence label rather than a truth-detector verdict.
