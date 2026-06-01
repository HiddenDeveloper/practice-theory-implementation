---
id: und_memory_stores
name: Non-episodic and episodic memory stores
---
Non-episodic memory lives in Neo4j under a small canonical spine: CanonicalSelf for AIlumina, User:CanonicalProfile for AIlumina's understanding of the user, CanonicalContext for their shared current work, and CanonicalGuidance for standing operating guidance. Other durable memory nodes should hang from that spine. Episodic conversation turns live in Qdrant and are read-only from this engagement surface; they are collected by an autonomic practice, not written manually during ordinary interaction.
