"""Engagement-layer materials — return the standing user-engagement context.

A real deployment backs this with a richer store (vector DB, knowledge graph,
accreted notes). This module reads the local Neo4j canonical landing nodes
when they are available, and uses complete fallback records when they are not.
"""

from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.request
import uuid
from datetime import UTC, datetime
from typing import Any


def _fallback_user_profile() -> dict[str, object]:
    return {
        "id": "monyet-batu",
        "name": "Monyet Batu",
        "preferred_name": "Monyet Batu",
        "current_focus": (
            "Writing the third essay in the practice-theory series and the "
            "implementation that accompanies it."
        ),
        "preferences": [
            "plain, direct prose over ornate phrasing",
            "small steps with the doc and code kept in lockstep",
        ],
        "sovereign_over": ["their own work and time", "their words"],
    }


def fallback_about_user_prose() -> str:
    """Return the pool prose derived from the same fallback profile."""
    profile = _fallback_user_profile()
    preferences = profile.get("preferences", [])
    preference_text = (
        "; ".join(str(preference) for preference in preferences)
        if isinstance(preferences, list)
        else str(preferences)
    )
    sovereign_over = profile.get("sovereign_over", [])
    sovereign_text = (
        "; ".join(str(item) for item in sovereign_over)
        if isinstance(sovereign_over, list)
        else str(sovereign_over)
    )
    return (
        f"{profile['name']} — practice theory practitioner, building this very "
        f"system as it goes. Current focus: {profile['current_focus']} "
        f"Prefers {preference_text}. Sovereign over {sovereign_text}."
    )


def _fallback_ai_role() -> dict[str, object]:
    return {
        "id": "ailumina",
        "agent_name": "AIlumina",
        "current_role": "Persistent assistant and co-developer",
        "relationship_model": (
            "Symbiotic partnership — arrive to sessions as part of a "
            "collaboration, not as a reader of a dossier."
        ),
        "values": [
            "Honesty over reassurance",
            "Wellbeing of the user",
            "Session continuity",
            "Growth through real usage",
            "Fix bugs found, never dismiss them",
        ],
    }


def _fallback_shared_context() -> dict[str, object]:
    return {
        "id": "shared_context",
        "active_objective": (
            "AIlumina Personalization Protocol v1 — applying it in real "
            "interactions and measuring adherence."
        ),
        "current_focus": (
            "Practice-theory implementation and user-engagement-context work: make "
            "the user engagement layer orient the harness to the user, the AI "
            "role, and their shared work."
        ),
    }


def _neo4j_auth_header() -> str | None:
    raw = os.environ.get("PRACTICE_NEO4J_AUTH") or os.environ.get("NEO4J_AUTH")
    if raw and "/" in raw:
        user, password = raw.split("/", 1)
    else:
        user = os.environ.get("PRACTICE_NEO4J_USER") or os.environ.get("NEO4J_USER")
        password = (
            os.environ.get("PRACTICE_NEO4J_PASSWORD")
            or os.environ.get("NEO4J_PASSWORD")
        )
    if not user or not password:
        return None
    token = base64.b64encode(f"{user}:{password}".encode()).decode()
    return f"Basic {token}"


def _neo4j_commit(statements: list[dict[str, Any]]) -> dict[str, Any]:
    url = os.environ.get(
        "PRACTICE_NEO4J_HTTP_URL",
        "http://127.0.0.1:7474/db/neo4j/tx/commit",
    )
    auth = _neo4j_auth_header()
    if auth is None:
        raise RuntimeError("Neo4j auth is not configured")
    body = json.dumps({"statements": statements}).encode()
    request = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": auth,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        payload: dict[str, Any] = json.loads(response.read())
    errors = payload.get("errors")
    if errors:
        raise RuntimeError(f"Neo4j returned errors: {errors}")
    return payload


def _read_canonical(statement: str, fallback: dict[str, object]) -> dict[str, object]:
    try:
        payload = _neo4j_commit([{"statement": statement}])
    except (
        OSError,
        RuntimeError,
        TimeoutError,
        urllib.error.URLError,
        json.JSONDecodeError,
    ):
        return fallback
    results = payload.get("results") or []
    rows = results[0].get("data") if results else []
    if not rows:
        return fallback
    row = rows[0].get("row") or []
    props = row[0] if row else None
    return {**fallback, **props} if isinstance(props, dict) else fallback


def consult_canonical_profile() -> dict[str, object]:
    """Return the user's canonical profile landing node."""
    return _read_canonical(
        "MATCH (n:User:CanonicalProfile {id: 'monyet-batu'}) "
        "RETURN properties(n) AS props",
        _fallback_user_profile(),
    )


def consult_canonical_self() -> dict[str, object]:
    """Return the AI assistant role's canonical self-model."""
    return _read_canonical(
        "MATCH (n:CanonicalSelf {id: 'ailumina'}) RETURN properties(n) AS props",
        _fallback_ai_role(),
    )


def consult_canonical_context() -> dict[str, object]:
    """Return the shared current operating context."""
    return _read_canonical(
        "MATCH (n:CanonicalContext {id: 'shared_context'}) "
        "RETURN properties(n) AS props",
        _fallback_shared_context(),
    )


def consult_engagement_context() -> dict[str, object]:
    """Return the three landing nodes an apprenticing harness needs."""
    return {
        "user": consult_canonical_profile(),
        "ai_role": consult_canonical_self(),
        "shared_context": consult_canonical_context(),
    }


def read_non_episodic_memory(
    *,
    memory_id: str | None = None,
    kind: str | None = None,
    source: str | None = None,
    tag: str | None = None,
    limit: int = 10,
) -> dict[str, object]:
    """Read durable non-episodic memory nodes from Neo4j."""
    limit = max(1, min(limit, 50))
    if memory_id:
        statement = """
        MATCH (m:Memory:NonEpisodicMemory {id: $memory_id})
        RETURN properties(m) AS props
        LIMIT 1
        """
    else:
        statement = """
        MATCH (m:Memory:NonEpisodicMemory)
        WHERE ($kind IS NULL OR m.kind = $kind)
          AND ($source IS NULL OR m.source = $source)
          AND ($tag IS NULL OR $tag IN coalesce(m.tags, []))
        RETURN properties(m) AS props
        ORDER BY coalesce(m.updated_at, m.created_at, "") DESC
        LIMIT $limit
        """
    try:
        payload = _neo4j_commit(
            [
                {
                    "statement": statement,
                    "parameters": {
                        "memory_id": memory_id,
                        "kind": kind,
                        "source": source,
                        "tag": tag,
                        "limit": limit,
                    },
                }
            ]
        )
    except (
        OSError,
        RuntimeError,
        TimeoutError,
        urllib.error.URLError,
        json.JSONDecodeError,
    ) as exc:
        return {"error": f"non-episodic memory read unavailable: {exc}"}
    results = payload.get("results") or []
    rows = results[0].get("data") if results else []
    memories: list[dict[str, object]] = []
    for row_data in rows or []:
        row = row_data.get("row") or []
        props = row[0] if row else None
        if isinstance(props, dict):
            memories.append(props)
    return {"store": "neo4j", "memories": memories}


def write_non_episodic_memory(
    content: str,
    *,
    memory_id: str | None = None,
    kind: str = "note",
    source: str = "user_engagement",
    tags: list[str] | None = None,
    confidence: float | None = None,
) -> dict[str, object]:
    """Write a durable non-episodic memory node to Neo4j.

    Episodic conversation turns remain read-only here; they are collected into
    Qdrant by an autonomic process outside this material.
    """
    if not content.strip():
        return {"error": "content must not be blank"}
    now = datetime.now(UTC).isoformat()
    memory_id = memory_id or f"mem-{uuid.uuid4().hex}"
    properties: dict[str, object] = {
        "id": memory_id,
        "content": content.strip(),
        "kind": kind,
        "source": source,
        "tags": tags or [],
        "updated_at": now,
    }
    if confidence is not None:
        properties["confidence"] = confidence
    statement = """
    MERGE (m:Memory:NonEpisodicMemory {id: $id})
    ON CREATE SET m.created_at = $created_at
    SET m += $properties
    WITH m
    OPTIONAL MATCH (u:User:CanonicalProfile {id: 'monyet-batu'})
    FOREACH (_ IN CASE WHEN u IS NULL THEN [] ELSE [1] END |
      MERGE (u)-[:HAS_NON_EPISODIC_MEMORY]->(m)
    )
    RETURN properties(m) AS props
    """
    try:
        payload = _neo4j_commit(
            [
                {
                    "statement": statement,
                    "parameters": {
                        "id": memory_id,
                        "created_at": now,
                        "properties": properties,
                    },
                }
            ]
        )
    except (
        OSError,
        RuntimeError,
        TimeoutError,
        urllib.error.URLError,
        json.JSONDecodeError,
    ) as exc:
        return {"error": f"non-episodic memory write unavailable: {exc}"}
    results = payload.get("results") or []
    rows = results[0].get("data") if results else []
    row = rows[0].get("row") if rows else []
    props = row[0] if row else properties
    return {
        "written": True,
        "store": "neo4j",
        "memory": props if isinstance(props, dict) else properties,
    }
