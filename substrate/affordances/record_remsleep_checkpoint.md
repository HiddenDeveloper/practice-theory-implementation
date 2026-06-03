---
id: record_remsleep_checkpoint
name: Record RemSleep checkpoint
materials:
- remsleep_record_checkpoint
---
Close a Memory Consolidation checkpoint lifecycle after the reviewed episode range and graph watermark have been inspected and selected candidates have been written, staged, or explicitly skipped. When a consolidation pass has handled the memory_signal(s) it chose to review, use this affordance in the same enactment to record the reviewed watermarks; if the pass is partial or failed, leave the prior checkpoint intact and state that rather than advancing it.
