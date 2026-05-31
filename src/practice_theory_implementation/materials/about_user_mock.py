"""Engagement-layer materials — return the standing companion context.

A real deployment backs this with a richer store (vector DB, knowledge graph,
accreted notes). This demo can read the local Neo4j canonical landing nodes
when they are available, and falls back to fixed content when they are not.

**The user named below is the author of the essay series this repo
accompanies, used as concrete demo content so the engagement layer's
about-the-user knowing is visible in the trail rather than abstract.** If
you fork this repo to use any practice for yourself, replace both the
returned dict here AND the `und_about_the_user` pool entry in `pools.py`
with your own content — otherwise the LLM in your session will address you
as "Monyet Batu" and reference the author's essay-writing focus rather than
your own work. The two must stay in sync; the engagement is internally
inconsistent if this mock and the pool prose disagree.
"""

from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.request
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


def _fallback_ai_role() -> dict[str, object]:
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
            "Practice-theory implementation and companion-context work: make "
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


def _read_canonical(statement: str, fallback: dict[str, object]) -> dict[str, object]:
    url = os.environ.get(
        "PRACTICE_NEO4J_HTTP_URL",
        "http://127.0.0.1:7474/db/neo4j/tx/commit",
    )
    auth = _neo4j_auth_header()
    if auth is None:
        return fallback
    body = json.dumps({"statements": [{"statement": statement}]}).encode()
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
    try:
        with urllib.request.urlopen(request, timeout=2) as response:
            payload: dict[str, Any] = json.loads(response.read())
    except (OSError, TimeoutError, urllib.error.URLError, json.JSONDecodeError):
        return fallback
    if payload.get("errors"):
        return fallback
    results = payload.get("results") or []
    rows = results[0].get("data") if results else []
    if not rows:
        return fallback
    row = rows[0].get("row") or []
    props = row[0] if row else None
    return props if isinstance(props, dict) else fallback


def consult_canonical_profile() -> dict[str, object]:
    """Return the user's canonical profile landing node."""
    return _read_canonical(
        "MATCH (n:User:CanonicalProfile {id: 'monyet-batu'}) "
        "RETURN properties(n) AS props",
        _fallback_user_profile(),
    )


def consult_canonical_self() -> dict[str, object]:
    """Return the AI companion role's canonical self-model."""
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


def consult_companion_context() -> dict[str, object]:
    """Return the three landing nodes an apprenticing harness needs."""
    return {
        "user": consult_canonical_profile(),
        "ai_role": consult_canonical_self(),
        "shared_context": consult_canonical_context(),
    }


def consult_about_user() -> dict[str, object]:
    """Backward-compatible entry point for the engagement affordance."""
    return consult_companion_context()
