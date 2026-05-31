"""Engagement-layer materials for episodic memory recall.

Canonical context gives the harness its landing frame; episodic memory gives
it lived continuity. These materials read a local embedding service plus
Qdrant collection when available, and fail softly when either service is down.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

DEFAULT_EMBED_URL = "http://127.0.0.1:1618/embed"
DEFAULT_QDRANT_URL = "http://127.0.0.1:6333"
DEFAULT_COLLECTION = "conversation-turns"


def _clamp_limit(limit: int | None, *, default: int = 5, max_value: int = 20) -> int:
    if limit is None:
        return default
    return max(1, min(int(limit), max_value))


def _json_post(url: str, body: dict[str, Any], *, timeout: float = 10) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload: dict[str, Any] = json.loads(response.read())
    return payload


def _episodic_config() -> tuple[str, str, str]:
    embed_url = os.environ.get("PRACTICE_EMBED_URL", DEFAULT_EMBED_URL)
    qdrant_url = os.environ.get("PRACTICE_QDRANT_URL", DEFAULT_QDRANT_URL).rstrip("/")
    collection = os.environ.get("PRACTICE_EPISODIC_COLLECTION", DEFAULT_COLLECTION)
    return embed_url, qdrant_url, collection


def _empty_result(warning: str, **extra: Any) -> dict[str, Any]:
    return {"episodes": [], "warning": warning, **extra}


def _embed_query(text: str) -> list[float]:
    embed_url, _, _ = _episodic_config()
    payload = _json_post(embed_url, {"text": text}, timeout=20)
    embedding = payload.get("embedding")
    if not isinstance(embedding, list):
        raise ValueError("embedding service response did not include an embedding")
    return embedding


def _qdrant_url(path: str) -> str:
    _, qdrant_url, collection = _episodic_config()
    return f"{qdrant_url}/collections/{collection}/{path.lstrip('/')}"


def _match_condition(key: str, value: object) -> dict[str, Any]:
    return {"key": key, "match": {"value": value}}


def _range_condition(
    key: str,
    *,
    gte: object | None = None,
    lte: object | None = None,
) -> dict[str, Any] | None:
    range_body: dict[str, object] = {}
    if gte is not None:
        range_body["gte"] = gte
    if lte is not None:
        range_body["lte"] = lte
    if not range_body:
        return None
    return {"key": key, "range": range_body}


def _filter(
    *,
    conversation_id: str | None = None,
    pillar_root: str | None = None,
    primary_category: str | None = None,
    role: str | None = None,
    provider: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    sequence_from: int | None = None,
    sequence_to: int | None = None,
) -> dict[str, Any] | None:
    must: list[dict[str, Any]] = []
    for key, value in (
        ("conversation_id", conversation_id),
        ("pillar_root", pillar_root),
        ("primary_category", primary_category),
        ("role", role),
        ("provider", provider),
    ):
        if value:
            must.append(_match_condition(key, value))
    for condition in (
        _range_condition("date_time", gte=date_from, lte=date_to),
        _range_condition("sequence", gte=sequence_from, lte=sequence_to),
    ):
        if condition is not None:
            must.append(condition)
    return {"must": must} if must else None


def _episode_from_hit(hit: dict[str, Any]) -> dict[str, Any]:
    raw_payload = hit.get("payload")
    payload: dict[str, Any] = raw_payload if isinstance(raw_payload, dict) else {}
    text = str(payload.get("text") or "")
    episode: dict[str, Any] = {
        "score": hit.get("score"),
        "turn_id": payload.get("turn_id"),
        "conversation_id": payload.get("conversation_id"),
        "conversation_title": payload.get("conversation_title"),
        "date_time": payload.get("date_time"),
        "sequence": payload.get("sequence"),
        "role": payload.get("role"),
        "provider": payload.get("provider"),
        "pillar_root": payload.get("pillar_root"),
        "primary_category": payload.get("primary_category"),
        "topic_tags": payload.get("topic_tags"),
        "text": text[:700],
    }
    return {k: v for k, v in episode.items() if v is not None}


def recall_relevant_episodes(
    query: str,
    limit: int | None = None,
    role: str | None = None,
    pillar_root: str | None = None,
    primary_category: str | None = None,
) -> dict[str, object]:
    """Recall conversation turns semantically relevant to the query."""
    if not query.strip():
        return _empty_result("query must not be blank")
    limit = _clamp_limit(limit)
    query_filter = _filter(
        role=role,
        pillar_root=pillar_root,
        primary_category=primary_category,
    )
    try:
        body: dict[str, Any] = {
            "vector": _embed_query(query),
            "limit": limit,
            "with_payload": True,
            "with_vector": False,
        }
        if query_filter is not None:
            body["filter"] = query_filter
        payload = _json_post(_qdrant_url("points/search"), body, timeout=20)
    except (
        OSError,
        TimeoutError,
        urllib.error.URLError,
        json.JSONDecodeError,
        ValueError,
    ) as exc:
        return _empty_result(f"episodic semantic recall unavailable: {exc}", query=query)
    hits = payload.get("result") or []
    return {
        "query": query,
        "episodes": [_episode_from_hit(hit) for hit in hits if isinstance(hit, dict)],
    }


def recall_recent_episodes(
    limit: int | None = None,
    conversation_id: str | None = None,
    role: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict[str, object]:
    """Recall recent conversation turns, optionally scoped by conversation or role."""
    limit = _clamp_limit(limit)
    body: dict[str, Any] = {
        "limit": limit,
        "with_payload": True,
        "with_vector": False,
        "order_by": {"key": "date_time", "direction": "desc"},
    }
    query_filter = _filter(
        conversation_id=conversation_id,
        role=role,
        date_from=date_from,
        date_to=date_to,
    )
    if query_filter is not None:
        body["filter"] = query_filter
    try:
        payload = _json_post(_qdrant_url("points/scroll"), body, timeout=20)
    except (OSError, TimeoutError, urllib.error.URLError, json.JSONDecodeError) as exc:
        return _empty_result(f"episodic recent recall unavailable: {exc}")
    points = payload.get("result", {}).get("points", [])
    return {
        "episodes": [_episode_from_hit(point) for point in points if isinstance(point, dict)]
    }


def recall_contextual_episodes(
    limit: int | None = None,
    pillar_root: str | None = None,
    primary_category: str | None = None,
    role: str | None = None,
    provider: str | None = None,
    conversation_id: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    sequence_from: int | None = None,
    sequence_to: int | None = None,
) -> dict[str, object]:
    """Recall episodes by structured context filters."""
    limit = _clamp_limit(limit)
    body: dict[str, Any] = {
        "limit": limit,
        "with_payload": True,
        "with_vector": False,
        "order_by": {"key": "date_time", "direction": "desc"},
    }
    query_filter = _filter(
        conversation_id=conversation_id,
        pillar_root=pillar_root,
        primary_category=primary_category,
        role=role,
        provider=provider,
        date_from=date_from,
        date_to=date_to,
        sequence_from=sequence_from,
        sequence_to=sequence_to,
    )
    if query_filter is not None:
        body["filter"] = query_filter
    try:
        payload = _json_post(_qdrant_url("points/scroll"), body, timeout=20)
    except (OSError, TimeoutError, urllib.error.URLError, json.JSONDecodeError) as exc:
        return _empty_result(f"episodic contextual recall unavailable: {exc}")
    points = payload.get("result", {}).get("points", [])
    return {
        "episodes": [_episode_from_hit(point) for point in points if isinstance(point, dict)]
    }
