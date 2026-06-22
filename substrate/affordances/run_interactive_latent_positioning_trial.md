---
id: run_interactive_latent_positioning_trial
name: Run Interactive Latent Positioning Trial
materials:
- run_interactive_latent_positioning_trial
---
Run a cumulative interactive latent-positioning sequence: after each user/patient turn, analyze the transcript-so-far for newly recruited Neuronpedia features, compare against a control transcript, and optionally steer the strongest candidate feature. Use this when the therapeutic method is not a single scaffold prompt but a responsive story that gradually places the patient model near a latent neighborhood. Treat the patient's actual responses as part of the path; if they are missing or synthetic, record that as a limitation.
