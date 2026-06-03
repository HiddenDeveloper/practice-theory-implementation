---
id: recall_unreviewed_episodes
name: Recall unreviewed episodes
materials:
- remsleep_recall_unreviewed_episodes
---
Read episodic turns after the prior checkpoint range. Use this as evidence for possible canonical memory candidates; do not write episodic memory directly. For a checkpoint review window, make one bounded call using the checkpoint sequence/date floor and the material's maximum useful limit, inspect what it returned, and report that bounded coverage. Do not walk the same window by repeatedly lowering date_to across many pages merely to exhaust the store; if the bounded read is insufficient, dispatch a source-basis gap/no-op signal or stop with the unreviewed remainder named rather than turning pagination labor into the trail.
