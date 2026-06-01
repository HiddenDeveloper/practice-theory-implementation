---
id: rule_memory_recall_dispatch_source_backed_signals
name: Dispatch only source-backed memory signals
---
Dispatch a memory_signal only when it cites enough episode ids, graph node ids, checkpoint ranges, or canonical context to let Memory Consolidation inspect the claim. If nothing relevant changed, dispatch a bounded no-op signal rather than inventing a memory candidate.
