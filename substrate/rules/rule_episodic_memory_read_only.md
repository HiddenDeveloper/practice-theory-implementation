---
id: rule_episodic_memory_read_only
name: Do not write episodic memory directly
---
Do not write conversation-turn episodes into Qdrant from the engagement surface. Use Neo4j for deliberate non-episodic memory writes; episodic memory is collected autonomically.
