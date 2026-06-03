"""The enactment trail — persistent record of what was invoked, when, with what.

Two tables in a small SQLite database:

  enactments  : one row per period of doing-a-practice within a session
  steps       : one row per invoke_affordance call within an enactment

The trail is the substrate trust rests on. A reader (the Judge in step 9, a
user, an auditor) inspects it to see what was actually done — independent of
what was said about it.

Schema is created on first use; the database file is created if missing. The
default path is `data/trail.db` under the project root; the
`PRACTICE_TRAIL_PATH` environment variable overrides it (used by the verify
script to inspect what the server wrote).
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
import time
import uuid
from collections.abc import Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TypeVar

DEFAULT_TRAIL_PATH = Path("data/trail.db")
TRAIL_PATH_ENV = "PRACTICE_TRAIL_PATH"
T = TypeVar("T")

SCHEMA = """
CREATE TABLE IF NOT EXISTS enactments (
    id                  TEXT PRIMARY KEY,
    practice_id         TEXT NOT NULL,
    parent_enactment_id TEXT REFERENCES enactments(id),
    mode                TEXT NOT NULL DEFAULT 'somatic',
    opened_at           TEXT NOT NULL,
    closed_at           TEXT
);

CREATE TABLE IF NOT EXISTS steps (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    enactment_id    TEXT NOT NULL REFERENCES enactments(id),
    affordance_id   TEXT NOT NULL,
    material_name   TEXT NOT NULL,
    arguments_json  TEXT NOT NULL,
    result_summary  TEXT NOT NULL,
    started_at      TEXT NOT NULL,
    completed_at    TEXT NOT NULL,
    duration_ms     INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS steps_by_enactment ON steps(enactment_id);

CREATE TABLE IF NOT EXISTS friction_observations (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    observing_enactment_id      TEXT NOT NULL,
    target_enactment_id         TEXT NOT NULL,
    kind                        TEXT NOT NULL,
    content                     TEXT NOT NULL,
    observation_data_json       TEXT,
    observed_at                 TEXT NOT NULL,
    addressed_at                TEXT,
    addressed_by_enactment_id   TEXT
);

CREATE INDEX IF NOT EXISTS friction_unaddressed
    ON friction_observations(addressed_at) WHERE addressed_at IS NULL;

CREATE TABLE IF NOT EXISTS judge_inbox (
    enactment_id              TEXT PRIMARY KEY,
    bundle_id                 TEXT NOT NULL,
    closed_at                 TEXT NOT NULL,
    routed_at                 TEXT NOT NULL,
    claimed_at                TEXT,
    claimed_by                TEXT,
    claim_expires_at          TEXT,
    consumed_at               TEXT,
    consumed_by_enactment_id  TEXT
);
CREATE INDEX IF NOT EXISTS judge_inbox_pending
    ON judge_inbox(consumed_at, claim_expires_at, routed_at);

CREATE TABLE IF NOT EXISTS smoother_inbox (
    friction_id               INTEGER PRIMARY KEY,
    target_enactment_id       TEXT NOT NULL,
    kind                      TEXT NOT NULL,
    emitted_at                TEXT NOT NULL,
    routed_at                 TEXT NOT NULL,
    claimed_at                TEXT,
    claimed_by                TEXT,
    claim_expires_at          TEXT,
    consumed_at               TEXT,
    consumed_by_enactment_id  TEXT
);
CREATE INDEX IF NOT EXISTS smoother_inbox_pending
    ON smoother_inbox(consumed_at, claim_expires_at, routed_at);

CREATE TABLE IF NOT EXISTS enactment_usage (
    enactment_id           TEXT PRIMARY KEY REFERENCES enactments(id),
    provider               TEXT,
    model                  TEXT,
    input_tokens           INTEGER,
    output_tokens          INTEGER,
    cache_read_tokens      INTEGER,
    cache_creation_tokens  INTEGER,
    cost_usd               REAL,
    num_turns              INTEGER,
    dispatch_ms            INTEGER,
    recorded_at            TEXT NOT NULL
);
"""


@dataclass(frozen=True, slots=True)
class EnactmentRow:
    id: str
    practice_id: str
    parent_enactment_id: str | None
    opened_at: str
    closed_at: str | None


@dataclass(frozen=True, slots=True)
class StepRow:
    id: int
    enactment_id: str
    affordance_id: str
    material_name: str
    arguments_json: str
    result_summary: str
    started_at: str
    completed_at: str
    duration_ms: int


@dataclass(frozen=True, slots=True)
class JudgeInboxRow:
    enactment_id: str
    bundle_id: str
    closed_at: str
    routed_at: str
    claimed_at: str | None
    claimed_by: str | None
    claim_expires_at: str | None
    consumed_at: str | None
    consumed_by_enactment_id: str | None


@dataclass(frozen=True, slots=True)
class SmootherInboxRow:
    friction_id: int
    target_enactment_id: str
    kind: str
    emitted_at: str
    routed_at: str
    claimed_at: str | None
    claimed_by: str | None
    claim_expires_at: str | None
    consumed_at: str | None
    consumed_by_enactment_id: str | None


@dataclass(frozen=True, slots=True)
class FrictionRow:
    id: int
    observing_enactment_id: str
    target_enactment_id: str
    kind: str
    content: str
    observation_data_json: str | None
    observed_at: str
    addressed_at: str | None
    addressed_by_enactment_id: str | None


@dataclass(frozen=True, slots=True)
class UsageRecord:
    """LLM usage for one dispatch, as the provider reports it.

    Produced by an autonomic adapter and attributed to the enactment the
    dispatch enacted. Every field but `provider` is optional — providers vary
    in what they expose, and cost is stored as-reported (null when absent), not
    re-derived. Autonomic-only today; the same shape carries a somatic row
    later (provider='harness', whatever tokens the harness reports)."""

    provider: str
    model: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    cache_read_tokens: int | None = None
    cache_creation_tokens: int | None = None
    cost_usd: float | None = None
    num_turns: int | None = None


@dataclass(frozen=True, slots=True)
class UsageRow:
    enactment_id: str
    provider: str | None
    model: str | None
    input_tokens: int | None
    output_tokens: int | None
    cache_read_tokens: int | None
    cache_creation_tokens: int | None
    cost_usd: float | None
    num_turns: int | None
    dispatch_ms: int | None
    recorded_at: str


def _resolve_path(override: str | None = None) -> Path:
    raw = override or os.environ.get(TRAIL_PATH_ENV) or str(DEFAULT_TRAIL_PATH)
    return Path(raw)


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="microseconds")


def _summarise(value: Any, *, max_len: int = 4000) -> str:
    text = json.dumps(value, default=str, sort_keys=False)
    if len(text) > max_len:
        return text[: max_len - 3] + "..."
    return text


class EnactmentStore:
    """SQLite-backed record of enactments and their steps."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = _resolve_path(str(path) if path is not None else None)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # check_same_thread=False + a lock around _cursor() lets the same
        # EnactmentStore be shared between the MCP request handlers and the
        # dispatcher's worker thread under HTTP transport. WAL journal mode
        # gives concurrent readers without blocking the writer.
        self._conn = sqlite3.connect(
            str(self.path), isolation_level=None, check_same_thread=False
        )
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript(SCHEMA)
        self._lock = threading.Lock()
        self._migrate()

    def _migrate(self) -> None:
        """Bring a pre-existing trail DB up to the current schema.

        Fresh DBs get every column from SCHEMA; this backfills older ones.
        The somatic/autonomic `mode` column lets routing split the reactive
        loop (somatic completions) from the reflective loop (autonomic
        history) — see `route_closed_enactments_to_judge_inbox`. Existing
        rows default to 'somatic'; going-forward correctness comes from
        `open_enactment(mode=...)`, which the server passes per bundle mode.
        """
        with self._cursor() as cur:
            cols = {row["name"] for row in cur.execute("PRAGMA table_info(enactments)")}
            if "mode" not in cols:
                cur.execute(
                    "ALTER TABLE enactments "
                    "ADD COLUMN mode TEXT NOT NULL DEFAULT 'somatic'"
                )

    def close(self) -> None:
        self._conn.close()

    @contextmanager
    def _cursor(self):  # type: ignore[no-untyped-def]
        with self._lock:
            cur = self._conn.cursor()
            try:
                yield cur
            finally:
                cur.close()

    def open_enactment(
        self,
        practice_id: str,
        *,
        parent_enactment_id: str | None = None,
        mode: str = "somatic",
    ) -> str:
        """Open an enactment. `mode` is the bundle's somatic/autonomic mode;
        it decides which loop later routes the closed enactment to the Judge
        (reactive for somatic, reflective for autonomic). Defaults to somatic
        so an unspecified caller is examined, not silently skipped."""
        eid = str(uuid.uuid4())
        with self._cursor() as cur:
            cur.execute(
                "INSERT INTO enactments"
                "(id, practice_id, parent_enactment_id, mode, opened_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (eid, practice_id, parent_enactment_id, mode, _now()),
            )
        return eid

    def close_enactment(self, enactment_id: str) -> None:
        with self._cursor() as cur:
            cur.execute(
                "UPDATE enactments SET closed_at = ? WHERE id = ? AND closed_at IS NULL",
                (_now(), enactment_id),
            )

    def record_step(
        self,
        *,
        enactment_id: str,
        affordance_id: str,
        material_name: str,
        arguments: Mapping[str, Any],
        result: Any,
        started_at: str,
        completed_at: str,
        duration_ms: int,
    ) -> int:
        with self._cursor() as cur:
            cur.execute(
                "INSERT INTO steps("
                "enactment_id, affordance_id, material_name, arguments_json,"
                " result_summary, started_at, completed_at, duration_ms"
                ") VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    enactment_id,
                    affordance_id,
                    material_name,
                    _summarise(dict(arguments)),
                    _summarise(result),
                    started_at,
                    completed_at,
                    duration_ms,
                ),
            )
            row_id = cur.lastrowid
        return row_id or 0

    def recent_enactments(self, *, limit: int = 10) -> list[EnactmentRow]:
        with self._cursor() as cur:
            cur.execute(
                "SELECT id, practice_id, parent_enactment_id, opened_at, closed_at "
                "FROM enactments ORDER BY opened_at DESC LIMIT ?",
                (limit,),
            )
            return [EnactmentRow(**dict(r)) for r in cur.fetchall()]

    def steps_for(self, enactment_id: str) -> list[StepRow]:
        with self._cursor() as cur:
            cur.execute(
                "SELECT id, enactment_id, affordance_id, material_name,"
                " arguments_json, result_summary, started_at, completed_at,"
                " duration_ms FROM steps WHERE enactment_id = ? ORDER BY id",
                (enactment_id,),
            )
            return [StepRow(**dict(r)) for r in cur.fetchall()]

    def most_recent_enactment_of(self, practice_id: str) -> EnactmentRow | None:
        with self._cursor() as cur:
            cur.execute(
                "SELECT id, practice_id, parent_enactment_id, opened_at, closed_at "
                "FROM enactments WHERE practice_id = ? "
                "ORDER BY opened_at DESC LIMIT 1",
                (practice_id,),
            )
            row = cur.fetchone()
            return EnactmentRow(**dict(row)) if row else None

    # --- friction observations ----------------------------------------------

    def record_friction(
        self,
        *,
        observing_enactment_id: str,
        target_enactment_id: str,
        kind: str,
        content: str,
        observation_data: object | None = None,
    ) -> int:
        """Record a Friction observation. `observation_data` is *evidence*
        (e.g., what was observed in structured form), not a remedy. The
        Smoother decides what to do; the Judge only observes."""
        data_json = (
            json.dumps(observation_data) if observation_data is not None else None
        )
        with self._cursor() as cur:
            cur.execute(
                "INSERT INTO friction_observations("
                "observing_enactment_id, target_enactment_id, kind, content,"
                " observation_data_json, observed_at"
                ") VALUES (?, ?, ?, ?, ?, ?)",
                (
                    observing_enactment_id,
                    target_enactment_id,
                    kind,
                    content,
                    data_json,
                    _now(),
                ),
            )
            row_id = cur.lastrowid
        return row_id or 0

    def pending_friction(self, *, limit: int = 20) -> list[FrictionRow]:
        with self._cursor() as cur:
            cur.execute(
                "SELECT id, observing_enactment_id, target_enactment_id, kind,"
                " content, observation_data_json, observed_at, addressed_at,"
                " addressed_by_enactment_id FROM friction_observations "
                "WHERE addressed_at IS NULL ORDER BY id LIMIT ?",
                (limit,),
            )
            return [FrictionRow(**dict(r)) for r in cur.fetchall()]

    def all_friction(self, *, limit: int = 50) -> list[FrictionRow]:
        with self._cursor() as cur:
            cur.execute(
                "SELECT id, observing_enactment_id, target_enactment_id, kind,"
                " content, observation_data_json, observed_at, addressed_at,"
                " addressed_by_enactment_id FROM friction_observations "
                "ORDER BY id DESC LIMIT ?",
                (limit,),
            )
            return [FrictionRow(**dict(r)) for r in cur.fetchall()]

    def mark_friction_addressed(
        self, friction_id: int, addressed_by_enactment_id: str
    ) -> bool:
        with self._cursor() as cur:
            cur.execute(
                "UPDATE friction_observations SET addressed_at = ?,"
                " addressed_by_enactment_id = ? WHERE id = ? AND addressed_at IS NULL",
                (_now(), addressed_by_enactment_id, friction_id),
            )
            return cur.rowcount > 0

    # --- per-enactment usage telemetry --------------------------------------

    def record_usage(
        self,
        enactment_id: str,
        usage: UsageRecord,
        *,
        dispatch_ms: int | None = None,
    ) -> None:
        """Record LLM usage for one enactment. Idempotent on enactment_id
        (INSERT OR REPLACE), so a re-recorded dispatch overwrites cleanly."""
        with self._cursor() as cur:
            cur.execute(
                "INSERT OR REPLACE INTO enactment_usage("
                "enactment_id, provider, model, input_tokens, output_tokens,"
                " cache_read_tokens, cache_creation_tokens, cost_usd, num_turns,"
                " dispatch_ms, recorded_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    enactment_id,
                    usage.provider,
                    usage.model,
                    usage.input_tokens,
                    usage.output_tokens,
                    usage.cache_read_tokens,
                    usage.cache_creation_tokens,
                    usage.cost_usd,
                    usage.num_turns,
                    dispatch_ms,
                    _now(),
                ),
            )

    def usage_for(self, enactment_id: str) -> UsageRow | None:
        with self._cursor() as cur:
            cur.execute(
                "SELECT enactment_id, provider, model, input_tokens, output_tokens,"
                " cache_read_tokens, cache_creation_tokens, cost_usd, num_turns,"
                " dispatch_ms, recorded_at FROM enactment_usage WHERE enactment_id = ?",
                (enactment_id,),
            )
            row = cur.fetchone()
            return UsageRow(*row) if row is not None else None

    # --- inbox routing (dispatcher writes here) -----------------------------

    def route_closed_enactments_to_judge_inbox(self, since: str | None = None) -> int:
        """Route closed *somatic* enactments into judge_inbox — the reactive loop.

        Idempotent on enactment_id. `since` is an ISO timestamp; only
        enactments closed after it are routed. Returns new rows inserted.

        Autonomic enactments (Judge, Smoother, RemSleep) are deliberately
        excluded. A reactive notification on an autonomic completion would
        make the Judge judge its own judging — each pass finishing, dispatching,
        triggering another, a self-consuming spin that never quiets. Autonomic
        history is examined instead by the reflective loop, on its own
        timescale: `route_autonomic_history_to_judge_inbox`. The two loops on
        two timescales keep each other clean (strange-loop essay, §"A smile and
        a wink to Douglas Hofstadter"; cf. MAPE-K).
        """
        with self._cursor() as cur:
            cur.execute(
                "INSERT OR IGNORE INTO judge_inbox(enactment_id, bundle_id, closed_at, routed_at) "
                "SELECT id, practice_id, closed_at, ? FROM enactments "
                "WHERE closed_at IS NOT NULL "
                "AND mode = 'somatic' "
                "AND EXISTS (SELECT 1 FROM steps WHERE steps.enactment_id = enactments.id) "
                "AND (? IS NULL OR closed_at >= ?)",
                (_now(), since, since),
            )
            return max(0, cur.rowcount)

    def route_autonomic_history_to_judge_inbox(self, since: str | None = None) -> int:
        """Route closed *autonomic* enactments into judge_inbox — the reflective loop.

        The counterpart to the reactive route. Autonomic completions dispatch
        no reactive notification; a scheduled secondary loop calls this in its
        own time, so the Judge examines autonomic history — its own and the
        Smoother's enactments included — on a slower timescale than somatic
        work. This is the Hofstadter mirror: the participants observing the
        loop they are part of, but paced so the observation does useful work
        instead of consuming itself.

        Idempotent on enactment_id. Returns the number of new rows inserted.
        """
        with self._cursor() as cur:
            cur.execute(
                "INSERT OR IGNORE INTO judge_inbox(enactment_id, bundle_id, closed_at, routed_at) "
                "SELECT id, practice_id, closed_at, ? FROM enactments "
                "WHERE closed_at IS NOT NULL "
                "AND mode = 'autonomic' "
                "AND EXISTS (SELECT 1 FROM steps WHERE steps.enactment_id = enactments.id) "
                "AND (? IS NULL OR closed_at >= ?)",
                (_now(), since, since),
            )
            return max(0, cur.rowcount)

    def route_friction_to_smoother_inbox(self, since: str | None = None) -> int:
        """Insert recorded Friction into smoother_inbox. Idempotent on friction_id."""
        with self._cursor() as cur:
            cur.execute(
                "INSERT OR IGNORE INTO smoother_inbox("
                "friction_id, target_enactment_id, kind, emitted_at, routed_at) "
                "SELECT id, target_enactment_id, kind, observed_at, ? "
                "FROM friction_observations "
                "WHERE ? IS NULL OR observed_at >= ?",
                (_now(), since, since),
            )
            return max(0, cur.rowcount)

    # --- inbox reads + claims (workers use these) ---------------------------

    def next_judge_work(
        self, *, worker_id: str, lease_seconds: int = 600
    ) -> JudgeInboxRow | None:
        """Atomically claim the oldest unclaimed, unconsumed judge_inbox row.

        Returns None if no work is available. The claim sets claim_expires_at
        to now + lease_seconds; if a worker dies, the claim expires and
        another worker can take the row.
        """
        return self._claim_inbox(
            table="judge_inbox",
            id_column="enactment_id",
            row_factory=JudgeInboxRow,
            worker_id=worker_id,
            lease_seconds=lease_seconds,
        )

    def next_smoother_work(
        self, *, worker_id: str, lease_seconds: int = 600
    ) -> SmootherInboxRow | None:
        return self._claim_inbox(
            table="smoother_inbox",
            id_column="friction_id",
            row_factory=SmootherInboxRow,
            worker_id=worker_id,
            lease_seconds=lease_seconds,
        )

    def _claim_inbox(
        self,
        *,
        table: str,
        id_column: str,
        row_factory: type[T],
        worker_id: str,
        lease_seconds: int,
    ) -> T | None:
        from datetime import timedelta
        now_dt = datetime.now(UTC)
        now_iso = now_dt.isoformat(timespec="microseconds")
        expires_iso = (now_dt + timedelta(seconds=lease_seconds)).isoformat(
            timespec="microseconds"
        )
        with self._cursor() as cur:
            cur.execute(
                f"UPDATE {table} SET claimed_at = ?, claimed_by = ?, "
                f"claim_expires_at = ? WHERE {id_column} = ("
                f"SELECT {id_column} FROM {table} WHERE consumed_at IS NULL "
                f"AND (claim_expires_at IS NULL OR claim_expires_at < ?) "
                f"ORDER BY routed_at LIMIT 1"
                f") RETURNING *",
                (now_iso, worker_id, expires_iso, now_iso),
            )
            row = cur.fetchone()
            if row is None:
                return None
        return row_factory(**dict(row))

    def consume_judge_inbox(
        self, enactment_id: str, *, consumer_enactment_id: str
    ) -> None:
        self._consume_inbox(
            "judge_inbox", "enactment_id", enactment_id, consumer_enactment_id
        )

    def consume_smoother_inbox(
        self, friction_id: int, *, consumer_enactment_id: str
    ) -> None:
        self._consume_inbox(
            "smoother_inbox", "friction_id", friction_id, consumer_enactment_id
        )

    def _consume_inbox(
        self,
        table: str,
        id_column: str,
        primary_id: object,
        consumer_enactment_id: str,
    ) -> None:
        with self._cursor() as cur:
            cur.execute(
                f"UPDATE {table} SET consumed_at = ?, consumed_by_enactment_id = ? "
                f"WHERE {id_column} = ?",
                (_now(), consumer_enactment_id, primary_id),
            )

    def pending_judge_inbox_count(self) -> int:
        with self._cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM judge_inbox WHERE consumed_at IS NULL"
            )
            return int(cur.fetchone()[0])

    def pending_smoother_inbox_count(self) -> int:
        with self._cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM smoother_inbox WHERE consumed_at IS NULL"
            )
            return int(cur.fetchone()[0])


@contextmanager
def time_call():  # type: ignore[no-untyped-def]
    """Yield a dict to be populated with started_at, completed_at, duration_ms."""
    out: dict[str, Any] = {}
    out["started_at"] = _now()
    t0 = time.monotonic()
    try:
        yield out
    finally:
        out["completed_at"] = _now()
        out["duration_ms"] = int((time.monotonic() - t0) * 1000)
