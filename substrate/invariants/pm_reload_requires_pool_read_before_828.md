---
id: pm_reload_requires_pool_read_before_828
name: Practice Management reload requires prior pool read
status: active
trigger: pm_reload_seed_substrate
mode: detect
friction_kind: practice_quality_substrate_read_omission
forbid_when:
  not:
    step_exists:
      material_name: pm_read_pool
message: Practice Management reload was invoked before any visible pm_read_pool row.
  Read the exact relied-on pool first or stop with a concrete pool-read blocker.
---
For Practice Management substrate stewardship, `pm_reload_seed_substrate` is not an entry move. When a closed enactment contains `pm_reload_seed_substrate` without an earlier `pm_read_pool`, deterministically raise `practice_quality_substrate_read_omission` so the missing pool-grounding row is caught without another hand-judged evaluation window.
