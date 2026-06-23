---
id: rule_adapt_after_failed_invocation
name: Reckon with failed invocations before closure or substrate action
---
Friction 930 confirms the ordering requirement also applies to duplicate-create substrate failures: when `pm_create_invariant`, `pm_create_*`, or another substrate authoring call fails because the target already exists, that failure must be reckoned with before any later substrate amendment, reload, or addressed mark. A later amendment to a rules element, affordance, material, bundle, invariant, or evaluation may proceed only after a visible prior step records that the duplicate-create failure merely established an existing target, did not change the chosen amendment, and is not a blocker, or after a current readable substrate surface supplies the alternate target and unchanged amendment basis. Do not make the first duplicate-create reckoning inside the later amendment result or addressed rationale; that is too late for the pre-amendment rule.
