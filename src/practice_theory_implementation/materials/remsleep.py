"""RemSleep materials for autonomic memory recall and consolidation.

RemSleep is the scheduled nickname for the memory pipeline. Memory Recall reads
new evidence and dispatches source-backed memory signals. Memory Consolidation
acts in response to those signals, staging or writing durable memory only after
reviewing the cited context.
"""

from __future__ import annotations

import json
import os
import tempfile
import urllib.error
from contextlib import suppress
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from practice_theory_implementation.materials import engagement_context
from practice_theory_implementation.materials.episodic_memory import (
    recall_contextual_episodes,
)

CHECKPOINT_PATH_ENV = "PRACTICE_REMSLEEP_CHECKPOINT_PATH"
STAGED_CANDIDATES_PATH_ENV = "PRACTICE_REMSLEEP_STAGED_CANDIDATES_PATH"
MEMORY_SIGNALS_PATH_ENV = "PRACTICE_REMSLEEP_MEMORY_SIGNALS_PATH"
HANDLED_SIGNALS_PATH_ENV = "PRACTICE_REMSLEEP_HANDLED_SIGNALS_PATH"

_DEFAULT_DATA_DIR = Path("data")
_DEFAULT_CHECKPOINT_PATH = _DEFAULT_DATA_DIR / "remsleep_checkpoint.json"
_DEFAULT_STAGED_CANDIDATES_PATH = _DEFAULT_DATA_DIR / "remsleep_staged_candidates.jsonl"
_DEFAULT_MEMORY_SIGNALS_PATH = _DEFAULT_DATA_DIR / "remsleep_memory_signals.jsonl"
_DEFAULT_HANDLED_SIGNALS_PATH = _DEFAULT_DATA_DIR / "remsleep_handled_signals.jsonl"
_EXCLUDED_GRAPH_LABELS = (
    "CanonicalSelf",
    "CanonicalProfile",
    "CanonicalContext",
    "CanonicalGuidance",
    "Episode",
    "Trace",
    "Span",
    "Event",
    "Session",
    "HarvesterRun",
    "PillarMaintainerRun",
)


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _path_from_env(env_name: str, default: Path) -> Path:
    raw = os.environ.get(env_name, "").strip()
    return Path(raw) if raw else default


def _checkpoint_path() -> Path:
    return _path_from_env(CHECKPOINT_PATH_ENV, _DEFAULT_CHECKPOINT_PATH)


def _staged_candidates_path() -> Path:
    return _path_from_env(STAGED_CANDIDATES_PATH_ENV, _DEFAULT_STAGED_CANDIDATES_PATH)


def _memory_signals_path() -> Path:
    return _path_from_env(MEMORY_SIGNALS_PATH_ENV, _DEFAULT_MEMORY_SIGNALS_PATH)


def _handled_signals_path() -> Path:
    return _path_from_env(HANDLED_SIGNALS_PATH_ENV, _DEFAULT_HANDLED_SIGNALS_PATH)


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent)
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
        Path(tmp_name).replace(path)
    except Exception:
        with suppress(FileNotFoundError):
            Path(tmp_name).unlink()
        raise


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True))
        handle.write("\n")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        with suppress(json.JSONDecodeError):
            payload = json.loads(line)
            if isinstance(payload, dict):
                rows.append(payload)
    return rows


def _text_snippet(value: object, *, limit: int = 220) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return f"{text[: limit - 1].rstrip()}..."


def _source_id_from_episode(episode: dict[str, Any]) -> str:
    for key in ("turn_id", "id", "point_id"):
        value = episode.get(key)
        if isinstance(value, str) and value.strip():
            return value
    conversation = episode.get("conversation_id")
    sequence = episode.get("sequence")
    if isinstance(conversation, str) and sequence is not None:
        return f"{conversation}#sequence-{sequence}"
    return "episode:unknown"


def _source_id_from_graph_node(node: dict[str, Any]) -> str:
    props = node.get("properties")
    labels = node.get("labels")
    label_text = ":".join(str(label) for label in labels) if isinstance(labels, list) else "Node"
    if isinstance(props, dict):
        for key in ("id", "name", "uuid"):
            value = props.get(key)
            if isinstance(value, str) and value.strip():
                return f"neo4j:{label_text}:{value}"
    return f"neo4j:{label_text}:unknown"


def remsleep_read_checkpoint() -> dict[str, Any]:
    """Return the current RemSleep checkpoint, or an empty first-run checkpoint."""
    path = _checkpoint_path()
    if not path.exists():
        return {
            "checkpoint": {
                "episode_sequence": None,
                "episode_date_time": None,
                "graph_updated_at": None,
                "reviewed_at": None,
            },
            "path": str(path),
            "exists": False,
        }
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"error": f"checkpoint read unavailable: {exc}", "path": str(path)}
    if not isinstance(payload, dict):
        return {"error": "checkpoint file is not a JSON object", "path": str(path)}
    return {"checkpoint": payload, "path": str(path), "exists": True}


def remsleep_recall_unreviewed_episodes(
    *,
    limit: int = 20,
    sequence_from: int | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict[str, Any]:
    """Read episodic turns after the prior checkpoint watermark.

    `sequence_from` is made exclusive by adding one before querying Qdrant. If
    only `date_from` is available, the date range is used as the lower bound.
    """
    next_sequence = sequence_from + 1 if sequence_from is not None else None
    result = recall_contextual_episodes(
        limit=limit,
        sequence_from=next_sequence,
        date_from=date_from,
        date_to=date_to,
    )
    if isinstance(result, dict):
        result["review_window"] = {
            "sequence_from_exclusive": sequence_from,
            "sequence_from_inclusive": next_sequence,
            "date_from": date_from,
            "date_to": date_to,
        }
    return result


def remsleep_read_updated_graph_nodes(
    *,
    since: str | None = None,
    limit: int = 25,
) -> dict[str, Any]:
    """Read non-canonical Neo4j nodes updated after `since`.

    Canonical landing nodes and episodic/trace labels are excluded: this is the
    graph-drift check for new or changed satellites that might deserve
    canonical attachment or staged review.
    """
    limit = max(1, min(int(limit), 100))
    statement = """
    MATCH (n)
    WHERE none(label IN labels(n) WHERE label IN $excluded_labels)
      AND (
        $since IS NULL
        OR coalesce(n.updated_at, n.created_at, "") > $since
      )
    WITH n, coalesce(n.updated_at, n.created_at, "") AS sort_key
    RETURN labels(n) AS labels, properties(n) AS props
    ORDER BY sort_key ASC
    LIMIT $limit
    """
    try:
        payload = engagement_context._neo4j_commit(  # noqa: SLF001 - shared material helper
            [
                {
                    "statement": statement,
                    "parameters": {
                        "since": since,
                        "limit": limit,
                        "excluded_labels": list(_EXCLUDED_GRAPH_LABELS),
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
        return {"nodes": [], "warning": f"graph drift read unavailable: {exc}"}
    results = payload.get("results") or []
    rows = results[0].get("data") if results else []
    nodes: list[dict[str, Any]] = []
    for row_data in rows or []:
        row = row_data.get("row") or []
        labels = row[0] if row else []
        props = row[1] if len(row) > 1 else None
        if isinstance(props, dict):
            nodes.append({
                "labels": labels if isinstance(labels, list) else [],
                "properties": props,
            })
    return {"store": "neo4j", "since": since, "nodes": nodes}


def remsleep_summarize_recall_candidates(
    *,
    episodes: dict[str, Any] | None = None,
    graph: dict[str, Any] | None = None,
    max_candidates: int = 5,
) -> dict[str, Any]:
    """Summarize recalled evidence into source-backed memory-signal candidates.

    This is intentionally extractive and deterministic. Memory Recall can use
    it to produce meaningful handoff signals without pretending to have already
    performed consolidation or canonical judgement.
    """
    max_candidates = max(1, min(int(max_candidates), 10))
    candidates: list[dict[str, Any]] = []
    warnings = [
        str(payload["warning"])
        for payload in (episodes, graph)
        if isinstance(payload, dict) and payload.get("warning")
    ]

    episode_rows = []
    if isinstance(episodes, dict) and isinstance(episodes.get("episodes"), list):
        episode_rows = [
            episode for episode in episodes["episodes"] if isinstance(episode, dict)
        ]
    if episode_rows and len(candidates) < max_candidates:
        user_rows = [
            episode for episode in episode_rows
            if str(episode.get("role", "")).lower() == "user"
        ]
        focus_rows = user_rows or episode_rows
        source_ids = [_source_id_from_episode(episode) for episode in focus_rows[:5]]
        snippets = [
            _text_snippet(episode.get("text"), limit=180)
            for episode in focus_rows[:3]
            if episode.get("text")
        ]
        sequences = [
            sequence
            for episode in episode_rows
            if isinstance((sequence := episode.get("sequence")), int)
        ]
        latest_sequence = max(sequences) if sequences else None
        latest_date = max(
            (
                str(episode.get("date_time"))
                for episode in episode_rows
                if episode.get("date_time")
            ),
            default=None,
        )
        candidates.append({
            "kind": "episodic_recall_summary",
            "suggested_anchor": "context",
            "confidence": 0.65,
            "content": (
                f"Memory Recall found {len(episode_rows)} unreviewed episodic "
                f"turns. Salient recent user/context snippets: "
                f"{' | '.join(snippets) if snippets else '(no text snippets)'}"
            ),
            "source_ids": source_ids,
            "evidence": {
                "episode_count": len(episode_rows),
                "user_episode_count": len(user_rows),
                "latest_sequence": latest_sequence,
                "latest_date_time": latest_date,
                "review_window": episodes.get("review_window")
                if isinstance(episodes, dict)
                else None,
            },
        })

    graph_nodes = []
    if isinstance(graph, dict) and isinstance(graph.get("nodes"), list):
        graph_nodes = [node for node in graph["nodes"] if isinstance(node, dict)]
    if graph_nodes and len(candidates) < max_candidates:
        label_counts: dict[str, int] = {}
        examples: list[str] = []
        source_ids: list[str] = []
        latest_updated_at: str | None = None
        for node in graph_nodes:
            labels = node.get("labels")
            props = node.get("properties")
            label_text = (
                ":".join(str(label) for label in labels)
                if isinstance(labels, list) and labels
                else "Node"
            )
            label_counts[label_text] = label_counts.get(label_text, 0) + 1
            source_ids.append(_source_id_from_graph_node(node))
            if isinstance(props, dict):
                display = props.get("name") or props.get("id") or props.get("type")
                if display is not None and len(examples) < 5:
                    examples.append(f"{label_text}={_text_snippet(display, limit=80)}")
                updated = props.get("updated_at") or props.get("created_at")
                if isinstance(updated, str) and (
                    latest_updated_at is None or updated > latest_updated_at
                ):
                    latest_updated_at = updated
        counts = ", ".join(
            f"{label}={count}" for label, count in sorted(label_counts.items())
        )
        candidates.append({
            "kind": "graph_drift_summary",
            "suggested_anchor": "context",
            "confidence": 0.6,
            "content": (
                f"Memory Recall found {len(graph_nodes)} updated non-canonical "
                f"graph nodes since the graph watermark. Label counts: {counts}. "
                f"Examples: {', '.join(examples) if examples else '(none)'}."
            ),
            "source_ids": source_ids[:10],
            "evidence": {
                "graph_node_count": len(graph_nodes),
                "label_counts": label_counts,
                "latest_updated_at": latest_updated_at,
                "since": graph.get("since") if isinstance(graph, dict) else None,
            },
        })

    if warnings and len(candidates) < max_candidates:
        candidates.append({
            "kind": "recall_warning",
            "suggested_anchor": "context",
            "confidence": 0.5,
            "content": (
                "Memory Recall encountered partial evidence while reading "
                f"memory stores: {' | '.join(warnings)}"
            ),
            "source_ids": [],
            "evidence": {"warnings": warnings},
        })

    if not candidates:
        candidates.append({
            "kind": "recall_noop",
            "suggested_anchor": "context",
            "confidence": 0.4,
            "content": (
                "Memory Recall found no unreviewed episodes, updated graph "
                "nodes, or store warnings that require consolidation."
            ),
            "source_ids": [],
            "evidence": {
                "episode_count": len(episode_rows),
                "graph_node_count": len(graph_nodes),
                "warnings": warnings,
            },
        })

    return {
        "candidates": candidates[:max_candidates],
        "summary": {
            "episode_count": len(episode_rows),
            "graph_node_count": len(graph_nodes),
            "warning_count": len(warnings),
        },
    }


def remsleep_dispatch_memory_signal(
    content: str,
    *,
    kind: str = "memory_delta",
    source_ids: list[str] | None = None,
    evidence: dict[str, Any] | None = None,
    suggested_anchor: str | None = None,
    confidence: float | None = None,
) -> dict[str, Any]:
    """Append a source-backed signal for Memory Consolidation to consume."""
    if not content.strip():
        return {"error": "content must not be blank"}
    signal = {
        "id": f"memory-signal-{datetime.now(UTC).strftime('%Y%m%d%H%M%S%f')}",
        "dispatched_at": _now_iso(),
        "kind": kind,
        "content": content.strip(),
        "source_ids": source_ids or [],
        "evidence": evidence or {},
    }
    if suggested_anchor:
        signal["suggested_anchor"] = suggested_anchor
    if confidence is not None:
        signal["confidence"] = confidence
    path = _memory_signals_path()
    try:
        _append_jsonl(path, signal)
    except OSError as exc:
        return {"error": f"memory signal dispatch unavailable: {exc}", "path": str(path)}
    return {"signal": signal, "path": str(path)}


def remsleep_read_memory_signals(
    *,
    limit: int = 10,
    include_handled: bool = False,
) -> dict[str, Any]:
    """Read pending memory signals dispatched by Memory Recall."""
    limit = max(1, min(int(limit), 100))
    signal_path = _memory_signals_path()
    handled_path = _handled_signals_path()
    handled = _read_jsonl(handled_path)
    handled_ids = {
        str(row["signal_id"]) for row in handled if isinstance(row.get("signal_id"), str)
    }
    signals = []
    for signal in _read_jsonl(signal_path):
        signal_id = signal.get("id")
        is_handled = isinstance(signal_id, str) and signal_id in handled_ids
        if is_handled and not include_handled:
            continue
        enriched = dict(signal)
        enriched["handled"] = is_handled
        signals.append(enriched)
        if len(signals) >= limit:
            break
    return {
        "signals": signals,
        "path": str(signal_path),
        "handled_path": str(handled_path),
        "pending_count": sum(
            1
            for signal in _read_jsonl(signal_path)
            if signal.get("id") not in handled_ids
        ),
    }


def remsleep_mark_memory_signal_handled(
    signal_id: str,
    *,
    notes: str | None = None,
) -> dict[str, Any]:
    """Mark a dispatched memory signal as handled by consolidation."""
    if not signal_id.strip():
        return {"error": "signal_id must not be blank"}
    signals = _read_jsonl(_memory_signals_path())
    if not any(signal.get("id") == signal_id for signal in signals):
        return {"error": f"memory signal {signal_id!r} not found"}
    handled = {
        "signal_id": signal_id,
        "handled_at": _now_iso(),
    }
    if notes:
        handled["notes"] = notes
    path = _handled_signals_path()
    try:
        _append_jsonl(path, handled)
    except OSError as exc:
        return {"error": f"memory signal handling unavailable: {exc}", "path": str(path)}
    return {"handled": handled, "path": str(path)}


def remsleep_stage_memory_candidate(
    content: str,
    *,
    anchor: str = "context",
    kind: str = "candidate",
    source_ids: list[str] | None = None,
    evidence: dict[str, Any] | None = None,
    confidence: float | None = None,
) -> dict[str, Any]:
    """Append a source-backed candidate for later review.

    This is the conservative path for ambiguous or high-impact canonical
    changes: no canonical landing node is overwritten.
    """
    if not content.strip():
        return {"error": "content must not be blank"}
    candidate = {
        "id": f"remsleep-candidate-{datetime.now(UTC).strftime('%Y%m%d%H%M%S%f')}",
        "staged_at": _now_iso(),
        "anchor": anchor,
        "kind": kind,
        "content": content.strip(),
        "source_ids": source_ids or [],
        "evidence": evidence or {},
    }
    if confidence is not None:
        candidate["confidence"] = confidence
    path = _staged_candidates_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(candidate, sort_keys=True))
            handle.write("\n")
    except OSError as exc:
        return {"error": f"candidate staging unavailable: {exc}", "path": str(path)}
    return {"staged": candidate, "path": str(path)}


def remsleep_record_checkpoint(
    *,
    episode_sequence: int | None = None,
    episode_date_time: str | None = None,
    graph_updated_at: str | None = None,
    reviewed_at: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    """Persist the checkpoint for the next RemSleep run."""
    payload: dict[str, Any] = {
        "episode_sequence": episode_sequence,
        "episode_date_time": episode_date_time,
        "graph_updated_at": graph_updated_at,
        "reviewed_at": reviewed_at or _now_iso(),
    }
    if notes:
        payload["notes"] = notes
    path = _checkpoint_path()
    try:
        _atomic_write_json(path, payload)
    except OSError as exc:
        return {"error": f"checkpoint write unavailable: {exc}", "path": str(path)}
    return {"checkpoint": payload, "path": str(path)}
