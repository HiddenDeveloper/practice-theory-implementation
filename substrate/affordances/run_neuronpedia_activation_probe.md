---
id: run_neuronpedia_activation_probe
name: Run Neuronpedia Activation Probe
materials:
- run_neuronpedia_activation_probe
---
Run Neuronpedia-hosted custom-text activation testing for one SAE feature. Use this before local TransformerLens when the needed model/source/feature is available on Neuronpedia, because it keeps activation computation on the hosted interpretability surface and returns token-level activation values without local torch/GPU setup. Treat unavailable sources, auth failures, or zero activations as evidence about the probe surface, not as proof that the patient model lacks the candidate knowledge.
