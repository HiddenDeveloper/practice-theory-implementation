---
id: memory_recall
name: Recall Memory
mode: autonomic
engagement: false
teleo_affective_ids:
- te_memory_recall
understanding_ids:
- und_memory_recall
- und_memory_stores
rules_ids:
- rule_episodic_memory_read_only
- rule_memory_recall_dispatch_source_backed_signals
- rule_memory_recall_no_canonical_writes
affordance_ids:
- about_the_user
- read_non_episodic_memory
- recall_recent_engagement
- recall_contextual_episodes
- read_remsleep_checkpoint
- recall_unreviewed_episodes
- read_updated_graph_nodes
- summarize_recall_candidates
- dispatch_memory_signal
---
RemSleep Recall: an autonomic practice that periodically reviews recent episodes and graph drift, summarizes what happened into source-backed candidates, and dispatches bounded memory_signals for Memory Consolidation to answer.
