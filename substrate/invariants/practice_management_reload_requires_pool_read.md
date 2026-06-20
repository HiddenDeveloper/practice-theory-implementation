---
id: practice_management_reload_requires_pool_read
name: Practice Management reload requires pool read
status: active
trigger: pm_reload_seed_substrate
mode: detect
friction_kind: quality_friction
forbid_when:
  not:
    step_exists:
      material_name: pm_read_pool
message: Practice Management reload must be preceded in the same enactment by pm_read_pool
  for the relied-on substrate pool; reload without that entry read violates the substrate
  stewardship gate.
---
Detects the determinable part of Practice Management's substrate stewardship gate: any enactment that invokes pm_reload_seed_substrate must already have a visible pm_read_pool step grounding the pool surface the work relies on. This turns the repeatedly hand-found missing-pool-read concern into a deterministic check at the earliest named violation point.
