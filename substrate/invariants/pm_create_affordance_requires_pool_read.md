---
id: pm_create_affordance_requires_pool_read
name: Practice Management affordance creation requires prior pool read
status: active
trigger: pm_create_affordance
mode: detect
friction_kind: quality_friction:substrate_authoring_without_pool_read
forbid_when:
  not:
    step_exists:
      material_name: pm_read_pool
message: Practice Management created an affordance without an earlier pm_read_pool
  step in the same enactment, so the authoring surface was used without inspecting
  the current substrate pool.
---
This governed invariant addresses the determinable part of Friction 516: in Practice Management enactment 8367059f-db1e-4e9e-b5fc-5528b101e612, the trail shows reload_seed_substrate followed by pm_create_affordance for read_morning_site_list and pm_amend_bundle for morning_briefing, with pm_read_pool_present=false. The existing rule rule_pm_read_pool_before_authoring already says to read the target pool before creating or amending substrate, but the evaluated target missed that step. This invariant therefore detects the exact first-write shape deterministically: when pm_create_affordance is triggered and no earlier pm_read_pool step exists in the same enactment, route quality_friction:substrate_authoring_without_pool_read instead of leaving the Judge to rediscover the missing substrate inspection by hand. It is intentionally scoped to pm_create_affordance because that was the first substrate write in the cited target; bundle-amendment, material, evaluation, and pool-element write variants remain judgement concerns or future invariants unless separately named by Friction.
