---
id: rule_pm_check_git_and_code_alignment
name: Check git history and code alignment
---
Before authoring or amending the substrate, check recent git history and current worktree changes for relevant implementation shifts. Confirm the practice bundle, affordances, materials, and rules being authored still match what the code-owned material surfaces and registry actually support. If the code and substrate disagree, fix or surface that mismatch before proceeding. Heed the registration precondition: when authoring a material returns a warning that its function must exist in registry.FUNCTIONS for any bundle using it to be projectable, that warning is a precondition, not a footnote. Invoke pm_reload_seed_substrate to bring the function into the live registry and force a projection refresh, then confirm the material is actually projectable, before wrapping it in an affordance or wiring it into a bundle. Do not build on a registration the trail has not confirmed.
