---
id: recall_unreviewed_episodes
name: Recall unreviewed episodes
materials:
- remsleep_recall_unreviewed_episodes
---
Read episodic turns after the prior checkpoint range. Invoke `remsleep_recall_unreviewed_episodes` as the material_name for this affordance; do not pass the affordance id `recall_unreviewed_episodes` as a material alias. Use this as evidence for possible canonical memory candidates; do not write episodic memory directly. For a checkpoint review window, make one bounded call using the checkpoint sequence/date floor and the material's maximum useful limit, inspect what it returned, and report that bounded coverage. Use the material's exact argument names: `sequence_from` for an exclusive sequence lower bound, `date_from` for a timestamp lower bound, optional `date_to` for a timestamp upper bound, and `limit` up to 20. Do not probe aliases such as `after_sequence`, `after_date_time`, or `since`; if the checkpoint gives a timestamp floor, pass it as `date_from`. Do not walk the same window by repeatedly lowering date_to across many pages merely to exhaust the store; if the bounded read is insufficient, dispatch a source-basis gap/no-op signal or stop with the unreviewed remainder named rather than turning pagination labor into the trail.
