---
id: rule_latent_probe_confidence_labels
name: Use bounded confidence labels
---
Classify each candidate as one of `retrieval-supported`, `constructed-plausible`, `activation-present-response-blocked`, `confabulation-likely`, or `unknown`. Do not invent stronger labels in the final judgment; if the evidence does not fit, use `unknown` and name the next discriminating probe.
