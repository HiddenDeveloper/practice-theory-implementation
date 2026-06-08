---
id: dispatch_memory_signal
name: Dispatch memory signal
materials:
- remsleep_dispatch_memory_signal
---
Emit a bounded, source-backed memory_signal for Memory Consolidation to inspect. Invoke the reached material `remsleep_dispatch_memory_signal` with the material schema's top-level fields: required `content`; optional `kind` (use this for the signal type such as `coverage_gap`), `source_ids`, `evidence`, `suggested_anchor`, and `confidence`. Do not wrap the payload in `memory_signal`, `signal`, or top-level `signal_type`; those wrappers are not accepted by the material. This is Recall's handoff; it is not a canonical memory write.
