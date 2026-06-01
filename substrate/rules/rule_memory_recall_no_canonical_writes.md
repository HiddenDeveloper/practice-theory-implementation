---
id: rule_memory_recall_no_canonical_writes
name: Recall does not write canonicals
---
Memory Recall may read episodic memory, graph nodes, checkpoints, and canonicals, then dispatch memory_signals. It must not write non-episodic memory, stage canonical candidates, mark signals handled, or record checkpoints. Those are Memory Consolidation responsibilities.
