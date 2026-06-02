"""Read-only status of the unattended RemSleep keeper.

A window into the autonomous loop: the resume checkpoint, recent RemSleep
enactments on the trail, the pending staged-candidate count (the human-review
queue for contentious/identity changes), unhandled memory signals, and the most
recent RemSleep-sourced canonical writes.

    uv run python scripts/remsleep_status.py
"""

from __future__ import annotations

import json
from pathlib import Path

from practice_theory_implementation.autonomic_adapters import practice_service_env
from practice_theory_implementation.materials import engagement_context, remsleep
from practice_theory_implementation.trail import EnactmentStore


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def main() -> None:
    import os

    os.environ.update(practice_service_env(Path.cwd()))

    checkpoint = remsleep.remsleep_read_checkpoint()
    print("=== CHECKPOINT (resume watermark) ===")
    print(json.dumps(checkpoint.get("checkpoint", checkpoint), indent=2, sort_keys=True))

    signals = remsleep.remsleep_read_memory_signals(limit=100)
    pending = signals.get("pending_count") if isinstance(signals, dict) else None
    staged = _read_jsonl(remsleep._staged_candidates_path())
    print("\n=== QUEUES ===")
    print(f"pending memory signals (recall -> consolidation): {pending}")
    print(f"staged candidates (human-review queue): {len(staged)}")
    for candidate in staged[-5:]:
        print(
            f"  - [{candidate.get('anchor')}/{candidate.get('kind')}] "
            f"{str(candidate.get('content'))[:90]}"
        )

    print("\n=== RECENT REMSLEEP ENACTMENTS (trail) ===")
    store = EnactmentStore()
    try:
        rows = [
            row
            for row in store.recent_enactments(limit=40)
            if getattr(row, "practice_id", None)
            in ("memory_recall", "memory_consolidation")
        ]
        for row in rows[:10]:
            print(f"  {row.opened_at}  {row.practice_id}  {row.id}")
        if not rows:
            print("  (none yet)")
    finally:
        store.close()

    print("\n=== RECENT REMSLEEP CANONICAL WRITES ===")
    seen = 0
    for anchor in ("self", "user", "context"):
        result = engagement_context.read_non_episodic_memory(anchor=anchor, limit=10)
        memories = result.get("memories")
        if not isinstance(memories, list):
            continue
        for memory in memories:
            props = memory.get("properties") if isinstance(memory, dict) else None
            if not isinstance(props, dict):
                continue
            if str(props.get("source", "")).startswith("remsleep"):
                print(
                    f"  [{anchor}] {props.get('kind')}: "
                    f"{str(props.get('content'))[:80]}"
                )
                seen += 1
    if not seen:
        print("  (none yet)")


if __name__ == "__main__":
    main()
