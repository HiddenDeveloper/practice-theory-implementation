---
id: reload_seed_substrate
name: Reload seed substrate
materials:
- pm_reload_seed_substrate
check_materials:
- requires_pm_read_pool_before_pm_reload_seed_substrate
---
Reload the file-backed substrate pools and bundles plus code-owned material surfaces and registry functions without restarting the MCP server. In Practice Management substrate stewardship this is not an entry move: before invoking `pm_reload_seed_substrate`, the current enactment must first expose the relevant pool surface with `read_pool` / `pm_read_pool`, or record a concrete pool-read surface blocker and stop. If reload has already happened without that pool read, do not continue into documentation-impact checking, authoring, amendment, evaluation, invariant work, or bundle wiring; backfill the exact relevant `pm_read_pool` before any write, or stop with the missing-pool-read blocker. This affordance-level gate responds to Friction 698's repeated `uses_substrate_authoring_surface` misses, where all five missing Practice Management enactments entered through reload without `pm_read_pool` despite existing bundle and rule guidance.

Friction 1045 confirms the reload-first miss remains live in the Practice Management authoring case: target enactment `8367059f-db1e-4e9e-b5fc-5528b101e612` reached `pm_reload_seed_substrate`, then `pm_create_affordance`, then `pm_amend_bundle` without any `pm_read_pool`, while nearby passes showed the pool-read path is reachable. Treat `pm_reload_seed_substrate` as an interrupted start whenever the relevant pool row is absent: the immediate next Practice Management move must be `pm_read_pool` for the pool supplying the ids or content, or a concrete pool-read blocker. Do not proceed from reload into `pm_create_*`, `pm_amend_*`, `pm_amend_bundle`, documentation checks, verification, closure, or another reload while that pool remains unread and unblocked.
