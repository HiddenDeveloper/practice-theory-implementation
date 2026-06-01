---
id: rule_memory_consolidation_checkpoint
name: Advance checkpoints only after review
---
Record the RemSleep checkpoint only after the reviewed episode range and graph-drift watermark have been inspected and any selected candidates have been written or staged. A failed or partial run must leave the prior checkpoint intact.
