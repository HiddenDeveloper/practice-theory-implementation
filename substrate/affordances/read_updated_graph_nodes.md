---
id: read_updated_graph_nodes
name: Read updated graph nodes
materials:
- remsleep_read_updated_graph_nodes
---
Inspect non-canonical Neo4j nodes updated since the last graph watermark, excluding the canonical spine and episodic trace nodes. Invoke `remsleep_read_updated_graph_nodes` with the material's exact argument names: optional `since` for the graph watermark timestamp and optional `limit` up to 100. Do not pass aliases such as `updated_since`; the material accepts `since` only.
