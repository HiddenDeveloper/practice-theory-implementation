---
id: pm_create_element_requires_pool_read
name: Practice Management pool-element authoring requires prior pool read
status: tombstoned
trigger: pm_create_element
mode: detect
friction_kind: practice_quality_substrate_authoring_without_pool_read
forbid_when:
  not:
    step_exists:
      material_name: pm_read_pool
message: Practice Management invoked pm_create_element without an earlier pm_read_pool
  grounding step in the same enactment.
tombstoned_at: '2026-06-24T23:04:28+00:00'
tombstone_reason: migrated to an affordance precondition (phase 3)
---
For Practice Management pool-element authoring, a current-enactment pm_read_pool step must appear before pm_create_element. This covers the generic teleo-affective, understanding, and rules authoring path named by Friction 743's repeated quality_affordance_coverage concern, where authoring-shaped substrate stewardship is still being found by hand when the pool-read gate is absent. The invariant intentionally checks only for an earlier pm_read_pool presence; judging whether the exact pool read was sufficient remains a judgement-shaped concern.
