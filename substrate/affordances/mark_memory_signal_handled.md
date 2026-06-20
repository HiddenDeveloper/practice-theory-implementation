---
id: mark_memory_signal_handled
name: Mark memory signal handled
materials:
- remsleep_mark_memory_signal_handled
---
Mark a memory_signal handled only after Memory Consolidation has actually answered the candidate it named: written, staged, deferred, or explicitly skipped. A preview-only mutation is not itself a handled answer. Invoke the reached material `remsleep_mark_memory_signal_handled`; `mark_memory_signal_handled` is the affordance id, not a valid material name. Pass `signal_id` and, when recording a handling explanation, use the optional `notes` argument (not `note` or `handled_note`). If a write material returned preview=true or written=false, do not mark the signal handled solely as written; first stage the candidate, explicitly defer/skip it, or later apply a committed write, and make the handled note preserve that concrete result state.
