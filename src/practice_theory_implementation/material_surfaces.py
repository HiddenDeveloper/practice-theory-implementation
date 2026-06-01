"""Material captured surfaces — code-owned, paired with the registry functions.

Each Material here is the *captured surface* (name, description, input_schema)
of a material; its executable function lives in `registry.FUNCTIONS`. The two
halves are code-owned and travel together (the schema describes the function's
parameters), so they live in code, not in the file-based substrate. The loader
injects these into `Substrate.materials`.
"""

from __future__ import annotations

from practice_theory_implementation.types import Material

MATERIAL_SURFACES: dict[str, Material] = {
    el.name: el
    for el in (
        # Engagement-layer materials: read canonical user-engagement context.
        Material(
            name="consult_canonical_profile",
            description=(
                "Return CanonicalProfile for the user landing node."
            ),
            input_schema={"type": "object", "properties": {}},
        ),
        Material(
            name="consult_canonical_self",
            description=(
                "Return CanonicalSelf for AIlumina's model-side self."
            ),
            input_schema={"type": "object", "properties": {}},
        ),
        Material(
            name="consult_canonical_context",
            description=(
                "Return CanonicalContext for the shared work and objectives."
            ),
            input_schema={"type": "object", "properties": {}},
        ),
        Material(
            name="consult_engagement_context",
            description=(
                "Return the three canonical user-engagement landing nodes together."
            ),
            input_schema={"type": "object", "properties": {}},
        ),
        Material(
            name="read_non_episodic_memory",
            description=(
                "Read durable non-episodic memory from Neo4j through the "
                "canonical spine: CanonicalSelf, CanonicalProfile, "
                "CanonicalContext, and CanonicalGuidance. Supports id, anchor, "
                "label, simple filters, or text query. Episodic Qdrant memory "
                "remains read-only through the separate recall materials."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "memory_id": {"type": "string"},
                    "anchor": {
                        "type": "string",
                        "enum": ["self", "user", "profile", "context", "guidance"],
                    },
                    "label": {"type": "string"},
                    "kind": {"type": "string"},
                    "source": {"type": "string"},
                    "tag": {"type": "string"},
                    "query": {"type": "string"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 50},
                },
            },
        ),
        Material(
            name="write_non_episodic_memory",
            description=(
                "Write durable non-episodic memory to Neo4j under one of the "
                "canonical anchors. Episodic Qdrant memory remains read-only "
                "from this material."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "content": {"type": "string"},
                    "memory_id": {"type": "string"},
                    "kind": {"type": "string"},
                    "source": {"type": "string"},
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "confidence": {"type": "number"},
                    "anchor": {
                        "type": "string",
                        "enum": ["self", "user", "profile", "context", "guidance"],
                    },
                },
                "required": ["content"],
            },
        ),
        Material(
            name="ensure_self_rooted_spine",
            description=(
                "Idempotently root the canonical graph at CanonicalSelf: MERGE "
                "typed edges from CanonicalSelf to CanonicalProfile, "
                "CanonicalContext, and CanonicalGuidance. Additive; deletes "
                "nothing. Takes no arguments."
            ),
            input_schema={"type": "object", "properties": {}},
        ),
        Material(
            name="recall_relevant_episodes",
            description=(
                "Return compact episodic memory turns semantically relevant "
                "to a query, using the local embedding service and Qdrant."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 20},
                    "role": {"type": "string"},
                    "pillar_root": {"type": "string"},
                    "primary_category": {"type": "string"},
                    "date_from": {"type": "string"},
                    "date_to": {"type": "string"},
                    "score_threshold": {"type": "number"},
                    "prefer_recent": {"type": "boolean"},
                },
                "required": ["query"],
            },
        ),
        Material(
            name="recall_recent_episodes",
            description=(
                "Return the most recent episodic memory turns by date_time, "
                "optionally scoped by conversation, role, or date range."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "minimum": 1, "maximum": 20},
                    "conversation_id": {"type": "string"},
                    "role": {"type": "string"},
                    "date_from": {"type": "string"},
                    "date_to": {"type": "string"},
                },
            },
        ),
        Material(
            name="recall_contextual_episodes",
            description=(
                "Return episodic memory turns using structured filters over "
                "canonical pillar, category, role, provider, conversation, "
                "date_time, and sequence."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "minimum": 1, "maximum": 20},
                    "pillar_root": {"type": "string"},
                    "primary_category": {"type": "string"},
                    "role": {"type": "string"},
                    "provider": {"type": "string"},
                    "conversation_id": {"type": "string"},
                    "date_from": {"type": "string"},
                    "date_to": {"type": "string"},
                    "sequence_from": {"type": "integer"},
                    "sequence_to": {"type": "integer"},
                },
            },
        ),
        # Calendar Stewardship materials — Google-Calendar-shaped mock.
        Material(
            name="cal_list_events",
            description=(
                "List the user's upcoming events in a date range, with "
                "attendee counts and an external-attendee flag."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "start_date": {"type": "string", "format": "date"},
                    "end_date": {"type": "string", "format": "date"},
                },
                "required": ["start_date", "end_date"],
            },
        ),
        Material(
            name="cal_propose_reschedule",
            description=(
                "Stage a reschedule on an event. No attendees notified "
                "(send_updates='none'). Returns a staging id."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "event_id": {"type": "string"},
                    "new_start": {"type": "string"},
                    "new_end": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["event_id", "new_start", "new_end", "reason"],
            },
        ),
        Material(
            name="cal_invite_stance",
            description=(
                "Record a question for the user with named options; no "
                "commitment is made on their behalf."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "question": {"type": "string"},
                    "options": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["question", "options"],
            },
        ),
        Material(
            name="cal_issue_reschedule",
            description=(
                "Convert a staged reschedule into an issued change. "
                "Notifications go to every attendee (send_updates='all'). "
                "Requires a staging id from a prior cal_propose_reschedule."
            ),
            input_schema={
                "type": "object",
                "properties": {"staging_id": {"type": "string"}},
                "required": ["staging_id"],
            },
        ),
        # Reflection-practice material: stores a written reflection.
        Material(
            name="store_reflection",
            description=(
                "Store a short written reflection verbatim and return its id."
            ),
            input_schema={
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
            },
        ),
        Material(
            name="garmin_list_activities",
            description="List the user's activities within a date range.",
            input_schema={
                "type": "object",
                "properties": {
                    "start_date": {"type": "string", "format": "date"},
                    "end_date": {"type": "string", "format": "date"},
                    "activity_type": {"type": "string"},
                },
                "required": ["start_date", "end_date"],
            },
        ),
        Material(
            name="garmin_get_activity",
            description="Fetch full detail for a single activity by its Garmin ID.",
            input_schema={
                "type": "object",
                "properties": {"activity_id": {"type": "string"}},
                "required": ["activity_id"],
            },
        ),
        Material(
            name="garmin_get_daily_summary",
            description="Fetch the daily wellness summary for a given date.",
            input_schema={
                "type": "object",
                "properties": {"date": {"type": "string", "format": "date"}},
                "required": ["date"],
            },
        ),
        Material(
            name="garmin_get_user_stats",
            description=(
                "Fetch aggregate stats (volume, distance, time-in-zones) for a period."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "start_date": {"type": "string", "format": "date"},
                    "end_date": {"type": "string", "format": "date"},
                },
                "required": ["start_date", "end_date"],
            },
        ),
        # Practice Management meta-materials.
        Material(
            name="pm_read_pool",
            description=(
                "Return every entry in the named pool. Valid pools: "
                "teleo_affective, understanding, rules, affordances, materials."
            ),
            input_schema={
                "type": "object",
                "properties": {"pool": {"type": "string"}},
                "required": ["pool"],
            },
        ),
        Material(
            name="pm_create_element",
            description="Add a new entry to a teleo_affective / understanding / rules pool.",
            input_schema={
                "type": "object",
                "properties": {
                    "pool": {"type": "string"},
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["pool", "id", "name", "content"],
            },
        ),
        Material(
            name="pm_amend_element",
            description=(
                "Amend an existing teleo_affective / understanding / rules entry "
                "(any of name/content)."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "pool": {"type": "string"},
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["pool", "id"],
            },
        ),
        Material(
            name="pm_create_affordance",
            description="Add an affordance that reaches for one or more existing materials.",
            input_schema={
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "materials": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["id", "name", "description", "materials"],
            },
        ),
        Material(
            name="pm_amend_affordance",
            description="Amend an existing affordance (any of name/description/materials).",
            input_schema={
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "materials": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["id"],
            },
        ),
        Material(
            name="pm_create_material",
            description=(
                "Add a material's captured surface (name, description, input "
                "schema) and, optionally, a persisted dynamic implementation."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "input_schema": {"type": "object"},
                    "implementation": {
                        "type": "object",
                        "properties": {
                            "kind": {
                                "type": "string",
                                "enum": ["constant", "echo", "expression"],
                            },
                            "result": {},
                            "expression": {"type": "string"},
                        },
                    },
                },
                "required": ["name", "description", "input_schema"],
            },
        ),
        Material(
            name="pm_amend_material",
            description=(
                "Amend an existing material's description, input schema, or "
                "dynamic implementation."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "input_schema": {"type": "object"},
                    "implementation": {
                        "type": "object",
                        "properties": {
                            "kind": {
                                "type": "string",
                                "enum": ["constant", "echo", "expression"],
                            },
                            "result": {},
                            "expression": {"type": "string"},
                        },
                    },
                },
                "required": ["name"],
            },
        ),
        Material(
            name="pm_create_bundle",
            description=(
                "Add a new bundle to the catalog as a selection over the pools."
                " mode defaults to somatic; pass 'autonomic' for autonomic bundles."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "teleo_affective_ids": {
                        "type": "array", "items": {"type": "string"}
                    },
                    "understanding_ids": {
                        "type": "array", "items": {"type": "string"}
                    },
                    "rules_ids": {"type": "array", "items": {"type": "string"}},
                    "affordance_ids": {
                        "type": "array", "items": {"type": "string"}
                    },
                    "mode": {"type": "string", "enum": ["somatic", "autonomic"]},
                },
                "required": [
                    "id", "name", "description",
                    "teleo_affective_ids", "understanding_ids",
                    "rules_ids", "affordance_ids",
                ],
            },
        ),
        Material(
            name="pm_amend_bundle",
            description="Change which pool ids an existing bundle selects.",
            input_schema={
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "teleo_affective_ids": {
                        "type": "array", "items": {"type": "string"}
                    },
                    "understanding_ids": {
                        "type": "array", "items": {"type": "string"}
                    },
                    "rules_ids": {"type": "array", "items": {"type": "string"}},
                    "affordance_ids": {
                        "type": "array", "items": {"type": "string"}
                    },
                },
                "required": ["id"],
            },
        ),
        Material(
            name="pm_reload_seed_substrate",
            description=(
                "Reload file-backed pools and bundles plus code-owned material "
                "surfaces and registry functions, then force projection refresh."
            ),
            input_schema={"type": "object", "properties": {}},
        ),
        Material(
            name="pm_check_documentation_impact",
            description=(
                "Search README/docs/social-media markdown for references likely "
                "affected by changed substrate ids, files, or query terms."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "changed_ids": {"type": "array", "items": {"type": "string"}},
                    "changed_files": {"type": "array", "items": {"type": "string"}},
                    "query": {"type": "string"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 100},
                },
            },
        ),
        # Judge primitives.
        Material(
            name="judge_list_recent_enactments",
            description=(
                "Return recent enactments most-recent-first. Optionally filter "
                "by bundle_id."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 10},
                    "bundle_id": {"type": "string"},
                },
            },
        ),
        Material(
            name="judge_read_enactment_steps",
            description=(
                "Read every step recorded against a single enactment, in order."
            ),
            input_schema={
                "type": "object",
                "properties": {"enactment_id": {"type": "string"}},
                "required": ["enactment_id"],
            },
        ),
        Material(
            name="judge_read_bundle",
            description=(
                "Return a bundle's structure as data — its mode and the pool "
                "ids it selects."
            ),
            input_schema={
                "type": "object",
                "properties": {"bundle_id": {"type": "string"}},
                "required": ["bundle_id"],
            },
        ),
        Material(
            name="judge_emit_friction",
            description=(
                "Record a Friction observation. kind is a short tag; content "
                "is the description; observation_data is optional structured "
                "evidence."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "target_enactment_id": {"type": "string"},
                    "kind": {"type": "string"},
                    "content": {"type": "string"},
                    "observation_data": {"type": "object"},
                },
                "required": ["target_enactment_id", "kind", "content"],
            },
        ),
        # Smoother — two smoother-specific materials; the Smoother bundle's
        # other six affordances reuse PM materials defined above.
        Material(
            name="smoother_read_pending_friction",
            description=(
                "Return Friction observations that have not been addressed yet."
            ),
            input_schema={
                "type": "object",
                "properties": {"limit": {"type": "integer", "default": 10}},
            },
        ),
        Material(
            name="smoother_mark_addressed",
            description="Mark a Friction observation as addressed by this enactment.",
            input_schema={
                "type": "object",
                "properties": {"friction_id": {"type": "integer"}},
                "required": ["friction_id"],
            },
        ),
        # RemSleep / Memory Recall and Memory Consolidation.
        Material(
            name="remsleep_read_checkpoint",
            description=(
                "Read the RemSleep checkpoint that marks the last reviewed "
                "episodic-memory and graph-drift watermarks."
            ),
            input_schema={"type": "object", "properties": {}},
        ),
        Material(
            name="remsleep_recall_unreviewed_episodes",
            description=(
                "Recall episodic turns after the prior RemSleep checkpoint "
                "watermark. sequence_from is treated as exclusive."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "minimum": 1, "maximum": 20},
                    "sequence_from": {"type": "integer"},
                    "date_from": {"type": "string"},
                    "date_to": {"type": "string"},
                },
            },
        ),
        Material(
            name="remsleep_read_updated_graph_nodes",
            description=(
                "Read non-canonical Neo4j nodes updated after a graph watermark."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "since": {"type": "string"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 100},
                },
            },
        ),
        Material(
            name="remsleep_summarize_recall_candidates",
            description=(
                "Summarize recalled episodes and graph drift into source-backed "
                "memory-signal candidates without writing canonicals."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "episodes": {"type": "object"},
                    "graph": {"type": "object"},
                    "max_candidates": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 10,
                    },
                },
            },
        ),
        Material(
            name="remsleep_dispatch_memory_signal",
            description=(
                "Dispatch a source-backed memory signal for Memory Consolidation "
                "to consume."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "content": {"type": "string"},
                    "kind": {"type": "string"},
                    "source_ids": {"type": "array", "items": {"type": "string"}},
                    "evidence": {"type": "object"},
                    "suggested_anchor": {
                        "type": "string",
                        "enum": ["self", "user", "profile", "context", "guidance"],
                    },
                    "confidence": {"type": "number"},
                },
                "required": ["content"],
            },
        ),
        Material(
            name="remsleep_read_memory_signals",
            description=(
                "Read pending memory signals dispatched by Memory Recall."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "minimum": 1, "maximum": 100},
                    "include_handled": {"type": "boolean"},
                },
            },
        ),
        Material(
            name="remsleep_mark_memory_signal_handled",
            description=(
                "Mark a dispatched memory signal as handled after consolidation "
                "has staged, written, or explicitly skipped it."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "signal_id": {"type": "string"},
                    "notes": {"type": "string"},
                },
                "required": ["signal_id"],
            },
        ),
        Material(
            name="remsleep_stage_memory_candidate",
            description=(
                "Append a source-backed canonical-memory candidate to the "
                "RemSleep staging file for later review."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "content": {"type": "string"},
                    "anchor": {
                        "type": "string",
                        "enum": ["self", "user", "profile", "context", "guidance"],
                    },
                    "kind": {"type": "string"},
                    "source_ids": {"type": "array", "items": {"type": "string"}},
                    "evidence": {"type": "object"},
                    "confidence": {"type": "number"},
                },
                "required": ["content"],
            },
        ),
        Material(
            name="remsleep_record_checkpoint",
            description=(
                "Persist the RemSleep checkpoint after the review range has "
                "been inspected and selected candidates have been written or staged."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "episode_sequence": {"type": "integer"},
                    "episode_date_time": {"type": "string"},
                    "graph_updated_at": {"type": "string"},
                    "reviewed_at": {"type": "string"},
                    "notes": {"type": "string"},
                },
            },
        ),
    )
}
