---
id: reload_seed_substrate
name: Reload seed substrate
materials:
- pm_reload_seed_substrate
---
Reload the file-backed substrate pools and bundles plus code-owned material surfaces and registry functions without restarting the MCP server. In Practice Management substrate stewardship this is not an entry move: before invoking `pm_reload_seed_substrate`, the current enactment must first expose the relevant pool surface with `read_pool` / `pm_read_pool`, or record a concrete pool-read surface blocker and stop. If reload has already happened without that pool read, do not continue into documentation-impact checking, authoring, amendment, evaluation, invariant work, or bundle wiring; backfill the exact relevant `pm_read_pool` before any write, or stop with the missing-pool-read blocker. This affordance-level gate responds to Friction 698's repeated `uses_substrate_authoring_surface` misses, where all five missing Practice Management enactments entered through reload without `pm_read_pool` despite existing bundle and rule guidance.
