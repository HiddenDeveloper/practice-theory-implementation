---
id: author_affordance
name: Author an affordance
materials:
- pm_create_affordance
---
Add to the existing `author_affordance` guidance: the missing-pool-read condition is not recoverable by the created affordance result itself. If `pm_create_affordance` is reached before the current enactment has visible `pm_read_pool` rows for `affordances` and any relied-on `materials`, the created affordance must not become the basis for `pm_amend_bundle` or any later stewardship action. The only acceptable continuation after that ungrounded create is a concrete missing-pool-read blocker that names the absent pool row(s); do not wire, verify, reload, check documentation, close, or explain from the ungrounded creation result.
