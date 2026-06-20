---
id: pm_reload_seed_requires_pool_read
name: Practice Management reload requires prior pool read
status: active
trigger: pm_reload_seed_substrate
mode: detect
friction_kind: quality_friction:substrate_authoring_without_pool_read
forbid_when:
  not:
    step_exists:
      material_name: pm_read_pool
message: Practice Management reloaded the seed substrate without an earlier pm_read_pool
  step in the same enactment, so substrate-management work proceeded without inspecting
  the current substrate surface it depends on.
---
This governed invariant addresses the determinable reload part of Friction 555. The targeted Friction names Practice Management quality signal `uses_substrate_authoring_surface`: in the evaluated window, five of eight substrate-management enactments, including target 8367059f-db1e-4e9e-b5fc-5528b101e612, used substrate-management materials without `pm_read_pool`; every missing case included `pm_reload_seed_substrate`, while the bundle already exposes `read_pool` and existing rules say reload does not substitute for current-pool inspection. Existing invariants cover `pm_create_affordance` and `pm_amend_bundle`; this invariant covers the repeated reload shape deterministically by triggering on `pm_reload_seed_substrate` when no earlier `pm_read_pool` exists in the same enactment. It intentionally checks only presence of an earlier pool read, because exact pool sufficiency remains judgement-shaped.
