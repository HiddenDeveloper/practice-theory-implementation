---
id: tombstone_invariant
name: Tombstone a governed invariant
materials:
- pm_tombstone_invariant
---
Soft-retire an invariant that is wrong, obsolete, or superseded — for example once the underlying cause it guarded against is fixed, or it produced false positives the audit surfaced. Tombstoning keeps the file (and its history) but sets `status: tombstoned` so the evaluator skips it; nothing is deleted. Always give a `reason` so the trail records why the determinable line moved back.
