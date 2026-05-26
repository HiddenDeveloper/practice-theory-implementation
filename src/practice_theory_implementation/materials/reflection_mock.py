"""Reflection-practice mock material — stores a reflection and returns an id.

The store is a module-level list; restarts clear it. A real deployment would
persist to the substrate or to an external store. The mock keeps the focus on
the apprenticeship layer rather than on reflection storage.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

_REFLECTIONS: list[dict[str, Any]] = []


def store_reflection(text: str) -> dict[str, Any]:
    record = {
        "id": str(uuid.uuid4()),
        "stored_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "text": text,
    }
    _REFLECTIONS.append(record)
    return record
