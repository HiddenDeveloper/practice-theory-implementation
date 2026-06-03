---
id: recall_relevant_episodes
name: Recall relevant episodes
materials:
- recall_relevant_episodes
---
Search episodic memory for prior conversation turns semantically relevant to the current request or practice. The result is a ranked proposal, not a verdict: each turn comes back in the store's own similarity order with its native score, and the ranking is only as good as the query. Before acting on what comes back, inspect the basis — read the scores and the returned titles, and judge whether they actually concern what you asked. A low top score or off-topic matches mean the retrieval failed, not that nothing relevant exists; flag it and re-query with better terms or wider filters rather than forwarding a weak result downstream or pivoting blindly. And a retrieval is not a synthesis: turns surfaced here still have to be weighed and turned into something, not just gathered.
