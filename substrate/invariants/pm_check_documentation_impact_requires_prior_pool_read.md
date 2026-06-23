---
id: pm_check_documentation_impact_requires_prior_pool_read
name: Practice Management documentation-impact checks require prior pool read
status: active
trigger: pm_check_documentation_impact
mode: detect
friction_kind: quality_affordance_coverage
forbid_when:
  not:
    step_exists:
      material_name: pm_read_pool
message: Practice Management invoked pm_check_documentation_impact before a visible
  pm_read_pool for the relied-on substrate pool.
---
When a Practice Management enactment reaches `pm_check_documentation_impact`, the trail must already contain `pm_read_pool` for the pool whose ids or current content support the documentation-impact decision. This deterministic guard addresses the repeated quality-affordance-coverage finding where documentation-impact checks proceeded after reload with no substrate entry-gate read.
