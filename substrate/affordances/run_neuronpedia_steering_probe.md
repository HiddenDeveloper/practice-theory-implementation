---
id: run_neuronpedia_steering_probe
name: Run Neuronpedia Steering Probe
materials:
- run_neuronpedia_steering_probe
---
Run a Neuronpedia-hosted SAE feature steering probe for a completion prompt, returning the default and steered completions plus logprob evidence when available. Use this as the hosted causal-intervention step after activation evidence suggests a feature is relevant: it can show whether amplifying or suppressing that latent changes the patient model's output distribution. Do not treat a changed completion as proof of latent knowledge by itself; compare against baseline, scaffold prompts, and controls.
