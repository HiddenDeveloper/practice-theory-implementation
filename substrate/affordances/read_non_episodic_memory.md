---
id: read_non_episodic_memory
name: Read non-episodic memory
materials:
- read_non_episodic_memory
---
Read durable non-episodic memory from Neo4j. This is distinct from Qdrant episodic recall. When a broad canonical read returns a landing node, inspect its returned fields before issuing a narrower semantic query; do not re-query for a detail already present in that node. When the same concern is being grounded across episodic and non-episodic memory, make the non-episodic read a single gathered pass where possible — by anchor, id/filter, or one broad semantic query with an adequate limit — then compare its returned nodes with the episodic recall already in hand before issuing near-duplicate semantic queries. Re-query only when the inspected nodes show a distinct missing anchor, filter, or memory id.
