---
id: amend_invariant
name: Amend a governed invariant
materials:
- pm_amend_invariant
---
Refine an existing invariant when it proves too blunt or too narrow — sharpen its `forbid_when` predicate, reword its message, or retarget its trigger/friction_kind. Any field left unset is preserved. The amended predicate is re-validated before it is saved, so an invariant can never become non-evaluable. Use this to move the determinable/judgement line as the practice teaches you where determinism is safe; tombstone instead when a rule should retire entirely.
