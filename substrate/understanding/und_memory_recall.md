---
id: und_memory_recall
name: Recall produces memory signals
---
Memory Recall is the first half of RemSleep. It reads the checkpoint, episodic turns, updated non-canonical graph nodes, and current canonical context to identify what may matter. Its output is a memory_signal: a small, source-backed event describing what happened, why it might matter, and what evidence Memory Consolidation should inspect. Recall does not update canonical memory and does not advance the checkpoint.
