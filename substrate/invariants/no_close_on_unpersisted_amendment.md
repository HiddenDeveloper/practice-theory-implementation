---
id: no_close_on_unpersisted_amendment
name: Don't mark addressed after a non-persisted amendment
status: active
trigger: smoother_mark_addressed
mode: detect
friction_kind: non_persisted_amendment_marked_addressed
forbid_when:
  any_earlier_step_result_contains: '"persisted": false'
message: >-
  This enactment marked a Friction addressed, but an earlier amend step in the
  same enactment reported persisted=false — the closure rests on a change that
  did not save.
---
A governed deterministic invariant: a Smoother must not close a Friction as
addressed when an earlier amendment in the same enactment reported it was not
persisted. Determinable from the recorded step results, so it is detected and
resolved without a Judge or Smoother dispatch. Replaces the prose contract the
Judge was policing by hand (the once-only `non_persisted_amendment_marked_addressed`
friction). If this proves too blunt — e.g. a code-owned material surface that
legitimately cannot persist — the Smoother sharpens or tombstones it.
