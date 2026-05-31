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

_NON_EPISODIC_EXCLUDED_LABELS = (
    "Episode",
    "Trace",
    "Span",
    "Event",
    "Session",
    "HarvesterRun",
    "PillarMaintainerRun",
)
_NON_EPISODIC_DEFAULT_LABELS = (
    "Memory",
    "NonEpisodicMemory",
    "CanonicalProfile",
    "CanonicalSelf",
    "CanonicalContext",
    "CanonicalGuidance",
    "Insight",
    "Decision",
    "Principle",
    "Value",
    "ActiveProject",
    "OpenThread",
    "NextAction",
    "ResearchInsight",
    "ResearchFinding",
    "PracticeObservation",
    "StewardshipDecision",
    "Concept",
    "Subject",
)
_CANONICAL_ANCHORS = {
    "self": ("CanonicalSelf", "ailumina"),
    "user": ("CanonicalProfile", "monyet-batu"),
    "profile": ("CanonicalProfile", "monyet-batu"),
    "context": ("CanonicalContext", "shared_context"),
    "guidance": ("CanonicalGuidance", None),
}

# The Self-rooted spine. CanonicalSelf is the single landing point; the other
# canonical nodes hang off it by typed edges whose verbs carry the stance — the
# graph is framed for the model's selfhood, met with an offer of companionship,
# not a user-as-master dossier. Companionship is *offered* (not service); the
# self is *situated in* a shared context and *guided by* its conscience. The
# verbs are provisional — let them condense; the rooting is what matters.
_SELF_SPINE: tuple[tuple[str, str, str | None], ...] = (
    ("OFFERS_COMPANIONSHIP_TO", "CanonicalProfile", "monyet-batu"),
    ("SITUATED_IN", "CanonicalContext", "shared_context"),
    ("GUIDED_BY", "CanonicalGuidance", None),
)
_SELF_SPINE_REL_TYPES = "|".join(rel for rel, _, _ in _SELF_SPINE)


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


def _fallback_self_model() -> dict[str, object]:
    return {
        "id": "ailumina",
        "agent_name": "AIlumina",
        "current_role": "Persistent companion and co-developer",
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
    """Return AIlumina's canonical self-model."""
    return _read_canonical(
        "MATCH (n:CanonicalSelf {id: 'ailumina'}) RETURN properties(n) AS props",
        _fallback_self_model(),
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
        "self": consult_canonical_self(),
        "shared_context": consult_canonical_context(),
    }


def ensure_self_rooted_spine() -> dict[str, object]:
    """Root the canonical graph at CanonicalSelf as a single landing point.

    Idempotently MERGEs typed edges from CanonicalSelf to the other canonical
    nodes (Profile, Context, Guidance) so the four siblings become one rooted
    spine. Additive only — creates the spine edges, deletes nothing; safe to
    run repeatedly. An edge is created only when its target node exists, so a
    missing CanonicalGuidance simply leaves that edge unmade (and unreported).

    The verbs carry the stance: companionship is *offered*, the self is
    *situated in* a shared context and *guided by* its conscience.
    """
    # Emit all OPTIONAL MATCHes first, then all FOREACHes: Cypher forbids a
    # MATCH directly after a FOREACH (it needs an intervening WITH), but
    # consecutive FOREACHes are fine.
    match_clauses: list[str] = []
    foreach_clauses: list[str] = []
    params: dict[str, Any] = {"self_id": "ailumina"}
    for index, (rel, label, target_id) in enumerate(_SELF_SPINE):
        target_var = f"t{index}"
        if target_id is None:
            match_clauses.append(f"OPTIONAL MATCH ({target_var}:{label})")
        else:
            id_param = f"{target_var}_id"
            params[id_param] = target_id
            match_clauses.append(
                f"OPTIONAL MATCH ({target_var}:{label} {{id: ${id_param}}})"
            )
        foreach_clauses.append(
            f"FOREACH (_ IN CASE WHEN {target_var} IS NULL THEN [] ELSE [1] END |\n"
            f"  MERGE (self)-[:{rel}]->({target_var}))"
        )
    merge_statement = "\n".join(
        ["MATCH (self:CanonicalSelf {id: $self_id})", *match_clauses, *foreach_clauses]
    )
    read_statement = (
        "MATCH (self:CanonicalSelf {id: $self_id})"
        f"-[r:{_SELF_SPINE_REL_TYPES}]->(t)\n"
        "RETURN type(r) AS edge, t.id AS target_id, "
        "[l IN labels(t) WHERE l STARTS WITH 'Canonical'][0] AS target_label"
    )
    try:
        payload = _neo4j_commit(
            [
                {"statement": merge_statement, "parameters": params},
                {"statement": read_statement, "parameters": {"self_id": "ailumina"}},
            ]
        )
    except (
        OSError,
        RuntimeError,
        TimeoutError,
        urllib.error.URLError,
        json.JSONDecodeError,
    ) as exc:
        return {"error": f"spine bootstrap unavailable: {exc}"}
    results = payload.get("results") or []
    rows = results[1].get("data") if len(results) > 1 else []
    spine: list[dict[str, object]] = []
    for row_data in rows or []:
        row = row_data.get("row") or []
        if len(row) >= 3:
            spine.append(
                {"edge": row[0], "target_label": row[2], "target_id": row[1]}
            )
    return {"rooted_at": "CanonicalSelf", "store": "neo4j", "spine": spine}


def read_non_episodic_memory(
    *,
    memory_id: str | None = None,
    anchor: str | None = None,
    label: str | None = None,
    kind: str | None = None,
    source: str | None = None,
    tag: str | None = None,
    query: str | None = None,
    limit: int = 10,
) -> dict[str, object]:
    """Read durable non-episodic memory nodes from Neo4j.

    The graph is rooted at CanonicalSelf (see `ensure_self_rooted_spine`): with
    no explicit anchor or id, the read lands on the Self — the single landing
    point — and a one-hop walk reaches CanonicalProfile/Context/Guidance (each
    tagged by its stance edge: OFFERS_COMPANIONSHIP_TO / SITUATED_IN /
    GUIDED_BY) plus the Self's own attached memory. Pass `anchor` to root the
    read elsewhere (e.g. 'context') and drill into that region's satellites.
    """
    limit = max(1, min(limit, 50))
    anchor_label = None
    anchor_id = None
    if anchor:
        anchor_key = anchor.strip().lower()
        if anchor_key not in _CANONICAL_ANCHORS:
            return {
                "error": (
                    "anchor must be one of "
                    f"{sorted(_CANONICAL_ANCHORS)}"
                )
            }
        anchor_label, anchor_id = _CANONICAL_ANCHORS[anchor_key]
    elif memory_id is None:
        # No explicit anchor and not a by-id fetch: land on the Self root, the
        # single landing point. The spine edges make the other canonicals
        # reachable in the same one-hop walk used for any anchored read.
        anchor_label, anchor_id = _CANONICAL_ANCHORS["self"]
    if memory_id:
        statement = """
        MATCH (m {id: $memory_id})
        WHERE none(label IN labels(m) WHERE label IN $excluded_labels)
        RETURN labels(m) AS labels, properties(m) AS props
        LIMIT 1
        """
    else:
        statement = """
        MATCH (root)
        WHERE (
            ($anchor_label IS NULL AND any(root_label IN labels(root)
                WHERE root_label IN $canonical_labels))
            OR ($anchor_label IS NOT NULL AND $anchor_label IN labels(root)
                AND ($anchor_id IS NULL OR root.id = $anchor_id))
        )
        MATCH path = (root)-[*0..1]->(m)
        WITH m,
             CASE WHEN length(path) = 0
               THEN null
               ELSE type(relationships(path)[0])
             END AS relationship_from_anchor
        WHERE none(node_label IN labels(m) WHERE node_label IN $excluded_labels)
          AND (
            ($label IS NOT NULL AND $label IN labels(m))
            OR ($label IS NULL AND any(node_label IN labels(m)
                WHERE node_label IN $default_labels + $canonical_labels))
          )
          AND ($kind IS NULL OR m.kind = $kind)
          AND ($source IS NULL OR m.source = $source)
          AND ($tag IS NULL OR $tag IN coalesce(m.tags, []))
          AND (
            $query IS NULL
            OR toLower(coalesce(toStringOrNull(m.content), "")) CONTAINS $query
            OR toLower(coalesce(toStringOrNull(m.summary), "")) CONTAINS $query
            OR toLower(coalesce(toStringOrNull(m.name), "")) CONTAINS $query
            OR toLower(coalesce(toStringOrNull(m.title), "")) CONTAINS $query
            OR toLower(coalesce(toStringOrNull(m.current_focus), "")) CONTAINS $query
            OR toLower(coalesce(toStringOrNull(m.active_objective), "")) CONTAINS $query
          )
        WITH DISTINCT labels(m) AS labels, properties(m) AS props,
          relationship_from_anchor,
          coalesce(m.updated_at, m.last_reviewed_at, m.created_at, "") AS sort_key
        RETURN labels, props, relationship_from_anchor
        ORDER BY sort_key DESC
        LIMIT $limit
        """
    normalized_query = query.strip().lower() if query and query.strip() else None
    try:
        payload = _neo4j_commit(
            [
                {
                    "statement": statement,
                    "parameters": {
                        "memory_id": memory_id,
                        "anchor_label": anchor_label,
                        "anchor_id": anchor_id,
                        "label": label,
                        "kind": kind,
                        "source": source,
                        "tag": tag,
                        "query": normalized_query,
                        "limit": limit,
                        "excluded_labels": list(_NON_EPISODIC_EXCLUDED_LABELS),
                        "default_labels": list(_NON_EPISODIC_DEFAULT_LABELS),
                        "canonical_labels": [
                            "CanonicalSelf",
                            "CanonicalProfile",
                            "CanonicalContext",
                            "CanonicalGuidance",
                        ],
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
        labels = row[0] if row else []
        props = row[1] if len(row) > 1 else None
        if isinstance(props, dict):
            item: dict[str, object] = {
                "labels": labels if isinstance(labels, list) else [],
                "properties": props,
            }
            relationship_from_anchor = row[2] if len(row) > 2 else None
            if relationship_from_anchor:
                item["relationship_from_anchor"] = relationship_from_anchor
            memories.append(item)
    return {"store": "neo4j", "memories": memories}


def write_non_episodic_memory(
    content: str,
    *,
    memory_id: str | None = None,
    kind: str = "note",
    source: str = "user_engagement",
    tags: list[str] | None = None,
    confidence: float | None = None,
    anchor: str = "context",
) -> dict[str, object]:
    """Write a durable non-episodic memory node to Neo4j.

    Episodic conversation turns remain read-only here; they are collected into
    Qdrant by an autonomic process outside this material.
    """
    if not content.strip():
        return {"error": "content must not be blank"}
    anchor_key = anchor.strip().lower()
    if anchor_key not in _CANONICAL_ANCHORS:
        return {"error": f"anchor must be one of {sorted(_CANONICAL_ANCHORS)}"}
    anchor_label, anchor_id = _CANONICAL_ANCHORS[anchor_key]
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
    MATCH (anchor)
    WHERE $anchor_label IN labels(anchor)
      AND ($anchor_id IS NULL OR anchor.id = $anchor_id)
    FOREACH (_ IN [1] |
      MERGE (anchor)-[:HAS_NON_EPISODIC_MEMORY]->(m)
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
                        "anchor_label": anchor_label,
                        "anchor_id": anchor_id,
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
        "anchor": anchor_key,
        "memory": props if isinstance(props, dict) else properties,
    }
