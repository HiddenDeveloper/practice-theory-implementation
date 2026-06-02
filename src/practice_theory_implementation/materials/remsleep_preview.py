"""Capability-enforced preview for RemSleep's canonical-mutating materials.

A meaningful RemSleep preview needs the real LLM practitioners reading the real
stores, but it must not let them apply canonical writes until a human approves.
We do not trust the prompt to hold that boundary — we enforce it in the
materials. When ``PRACTICE_REMSLEEP_PREVIEW`` is set, the three canonical
mutators (``write_non_episodic_memory``, ``ensure_self_rooted_spine``,
``remsleep_record_checkpoint``) capture their *intended* effect to a journal
instead of performing it, and return ``{"preview": True, ...}``.

The journal (jsonl, one intended write per line) **is** the proposed canonical
update. Apply = replay the approved entries with preview off.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PREVIEW_ENABLED_ENV = "PRACTICE_REMSLEEP_PREVIEW"
PREVIEW_PATH_ENV = "PRACTICE_REMSLEEP_PREVIEW_PATH"

_DEFAULT_PREVIEW_PATH = Path("data") / "remsleep_preview.jsonl"
_TRUE_VALUES = ("1", "true", "yes", "on")


def preview_enabled() -> bool:
    """True when canonical writes must be captured, not applied."""
    return os.environ.get(PREVIEW_ENABLED_ENV, "").strip().lower() in _TRUE_VALUES


def preview_path() -> Path:
    """Path to the preview journal (jsonl)."""
    raw = os.environ.get(PREVIEW_PATH_ENV, "").strip()
    return Path(raw) if raw else _DEFAULT_PREVIEW_PATH


def record(entry: dict[str, Any]) -> dict[str, Any]:
    """Append an intended-write entry to the preview journal and return it.

    Never touches the real store. A preview that cannot record its intent must
    fail loudly rather than silently fall through to applying the write, so IO
    errors are allowed to propagate to the caller.
    """
    payload = {"recorded_at": datetime.now(UTC).isoformat(), **entry}
    path = preview_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True))
        handle.write("\n")
    return payload


def read_journal(path: Path | None = None) -> list[dict[str, Any]]:
    """Read all captured intended-write entries from the journal."""
    journal_path = path or preview_path()
    if not journal_path.exists():
        return []
    entries: list[dict[str, Any]] = []
    for line in journal_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            entries.append(payload)
    return entries
