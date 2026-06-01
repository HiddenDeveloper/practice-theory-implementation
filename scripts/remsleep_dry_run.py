"""Staging-only RemSleep dry run.

Reads the same local service env that autonomic adapters use, then exercises
the RemSleep read/stage path without writing canonical memory or advancing the
durable checkpoint.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from practice_theory_implementation.autonomic_adapters import practice_service_env
from practice_theory_implementation.materials import engagement_context, remsleep


def _print_json(label: str, value: Any, *, max_chars: int | None = None) -> None:
    print(label)
    text = json.dumps(value, indent=2, sort_keys=True)
    print(text[:max_chars] if max_chars else text)


def main() -> None:
    env = practice_service_env(Path.cwd())
    os.environ.update(env)

    temp_dir = Path(tempfile.mkdtemp(prefix="remsleep-dry-run-"))
    os.environ["PRACTICE_REMSLEEP_CHECKPOINT_PATH"] = str(
        temp_dir / "remsleep_checkpoint.json"
    )
    os.environ["PRACTICE_REMSLEEP_STAGED_CANDIDATES_PATH"] = str(
        temp_dir / "remsleep_staged_candidates.jsonl"
    )
    os.environ["PRACTICE_REMSLEEP_MEMORY_SIGNALS_PATH"] = str(
        temp_dir / "remsleep_memory_signals.jsonl"
    )
    os.environ["PRACTICE_REMSLEEP_HANDLED_SIGNALS_PATH"] = str(
        temp_dir / "remsleep_handled_signals.jsonl"
    )

    print(f"DRY_RUN_TEMP_DIR {temp_dir}")
    print(
        "SERVICE_ENV "
        f"neo4j={'yes' if any(k in env for k in ('PRACTICE_NEO4J_AUTH', 'NEO4J_AUTH')) else 'no'} "
        f"qdrant={'yes' if env.get('PRACTICE_QDRANT_URL') else 'default'} "
        f"embed={'yes' if env.get('PRACTICE_EMBED_URL') else 'default'}"
    )

    checkpoint = remsleep.remsleep_read_checkpoint()
    _print_json("CHECKPOINT", checkpoint)

    context = engagement_context.consult_engagement_context()
    _print_json(
        "CANONICAL_CONTEXT_KEYS",
        {
            key: sorted(value.keys()) if isinstance(value, dict) else type(value).__name__
            for key, value in context.items()
        },
    )

    cp = checkpoint.get("checkpoint") if isinstance(checkpoint, dict) else {}
    sequence = cp.get("episode_sequence") if isinstance(cp, dict) else None
    episode_date = cp.get("episode_date_time") if isinstance(cp, dict) else None
    graph_watermark = cp.get("graph_updated_at") if isinstance(cp, dict) else None

    episodes = remsleep.remsleep_recall_unreviewed_episodes(
        limit=10,
        sequence_from=sequence if isinstance(sequence, int) else None,
        date_from=episode_date if isinstance(episode_date, str) else None,
    )
    _print_json("EPISODES", episodes, max_chars=5000)

    graph = remsleep.remsleep_read_updated_graph_nodes(
        since=graph_watermark if isinstance(graph_watermark, str) else None,
        limit=10,
    )
    _print_json("GRAPH_NODES", graph, max_chars=5000)

    # This script is not the practitioner — it has no judgement to apply. In a
    # real pass the apprenticed Memory Recall LLM reads the raw episodes and
    # graph nodes above and decides what, if anything, to dispatch. Here we only
    # exercise the read -> dispatch -> stage -> handle plumbing mechanically.
    episode_count = len(episodes.get("episodes", [])) if isinstance(episodes, dict) else 0
    node_count = len(graph.get("nodes", [])) if isinstance(graph, dict) else 0
    warnings = [
        str(payload["warning"])
        for payload in (episodes, graph)
        if isinstance(payload, dict) and payload.get("warning")
    ]
    signal = remsleep.remsleep_dispatch_memory_signal(
        (
            "DRY RUN ONLY: mechanical plumbing check, not a practitioner "
            "judgement. The real Memory Recall LLM reads the raw evidence and "
            "decides what to hand to Memory Consolidation."
        ),
        kind="dry_run_signal",
        source_ids=[],
        evidence={
            "episode_count": episode_count,
            "graph_node_count": node_count,
            "warnings": warnings,
            "dry_run": True,
        },
    )
    _print_json("DISPATCHED_DRY_RUN_SIGNAL", signal)
    pending_signals = remsleep.remsleep_read_memory_signals(limit=10)
    _print_json("PENDING_MEMORY_SIGNALS", pending_signals)
    signal_payload = signal.get("signal") if isinstance(signal, dict) else None
    signal_id = signal_payload.get("id") if isinstance(signal_payload, dict) else None
    if isinstance(signal_id, str):
        staged = remsleep.remsleep_stage_memory_candidate(
            (
                "DRY RUN ONLY: Memory Consolidation consumed the dry-run "
                "memory_signal without writing canonical memory."
            ),
            anchor="context",
            kind="dry_run_note",
            source_ids=[signal_id],
            evidence={"signal_id": signal_id},
            confidence=0.0,
        )
        _print_json("STAGED_DRY_RUN_NOTE", staged)
        handled = remsleep.remsleep_mark_memory_signal_handled(
            signal_id,
            notes="dry run consumed the staged signal without canonical writes",
        )
        _print_json("HANDLED_DRY_RUN_SIGNAL", handled)
        _print_json(
            "PENDING_MEMORY_SIGNALS_AFTER_HANDLED",
            remsleep.remsleep_read_memory_signals(limit=10),
        )
    _print_json("CHECKPOINT_AFTER_DRY_RUN", remsleep.remsleep_read_checkpoint())
    print("STAGED_FILE_CONTENT")
    print(Path(os.environ["PRACTICE_REMSLEEP_STAGED_CANDIDATES_PATH"]).read_text())
    print("SIGNALS_FILE_CONTENT")
    print(Path(os.environ["PRACTICE_REMSLEEP_MEMORY_SIGNALS_PATH"]).read_text())


if __name__ == "__main__":
    main()
