---
id: pm_amend_bundle_requires_pool_read
name: Practice Management bundle amendment requires prior pool read
status: active
trigger: pm_amend_bundle
mode: detect
friction_kind: quality_friction:substrate_authoring_without_pool_read
forbid_when:
  not:
    step_exists:
      material_name: pm_read_pool
message: Practice Management amended a bundle without an earlier pm_read_pool step
  in the same enactment, so bundle selection changed without inspecting the current
  substrate pool surface it depends on.
---
This governed invariant addresses the determinable bundle-amendment part of Friction 551. The targeted Friction names Practice Management enactments, including target 8367059f-db1e-4e9e-b5fc-5528b101e612, where substrate work used reload and then amended the morning_briefing bundle without any pm_read_pool. The existing Practice Management rule rule_pm_read_pool_before_authoring already says bundle amendments must read the pools whose ids are selected or relied on, and reload_seed_substrate does not substitute for that inspection. This invariant makes the simplest deterministic check for that named write shape: when pm_amend_bundle occurs and no earlier pm_read_pool step exists in the same enactment, route quality_friction:substrate_authoring_without_pool_read automatically instead of leaving the Judge to rediscover the missing pool-read gate by hand. It intentionally requires only presence of an earlier pm_read_pool because the invariant language can determine presence from recorded steps; whether the exact pool was sufficient remains judgement-shaped and is left to the Judge.
