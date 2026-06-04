"""Phase 2 — the idle-triggered audit's read/write surface.

The audit reviews invariant firings only when the loop is idle (both inboxes
empty) and there are unaudited firings. These guard the cursor the loop reads
(unaudited firings joined to their friction) and writes (marking reviewed), plus
the column migration for trails created before the audit existed.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from practice_theory_implementation.trail import EnactmentStore


def test_unaudited_cursor_read_mark_count(tmp_path: Path) -> None:
    store = EnactmentStore(tmp_path / "trail.db")
    # a real friction so the join carries kind/content
    fid = store.record_friction(
        observing_enactment_id="system:invariant:rule_a",
        target_enactment_id="enact_1",
        kind="non_persisted_amendment_marked_addressed",
        content="closure rested on a change that did not save",
    )
    store.record_invariant_firing("rule_a", "enact_1", fid)
    store.record_invariant_firing("rule_b", "enact_2", 999)

    assert store.unaudited_invariant_firing_count() == 2
    rows = store.unaudited_invariant_firings(limit=10)
    by_rule = {r["invariant_id"]: r for r in rows}
    assert by_rule["rule_a"]["friction_kind"] == "non_persisted_amendment_marked_addressed"
    assert "did not save" in by_rule["rule_a"]["friction_content"]

    store.mark_invariant_firing_audited(
        "rule_a", "enact_1", audited_by_enactment_id="audit_x"
    )
    assert store.unaudited_invariant_firing_count() == 1
    remaining = store.unaudited_invariant_firings(limit=10)
    assert [r["invariant_id"] for r in remaining] == ["rule_b"]


def test_audited_at_column_is_migrated(tmp_path: Path) -> None:
    # Simulate a trail created by the Phase-1 code: invariant_firings without
    # the audit columns. Opening it with the current store must backfill them.
    db = tmp_path / "old.db"
    con = sqlite3.connect(str(db))
    con.execute(
        "CREATE TABLE invariant_firings ("
        "invariant_id TEXT NOT NULL, enactment_id TEXT NOT NULL, "
        "friction_id INTEGER NOT NULL, fired_at TEXT NOT NULL, "
        "PRIMARY KEY (invariant_id, enactment_id))"
    )
    con.execute(
        "INSERT INTO invariant_firings VALUES ('r', 'e', 1, '2026-06-04T00:00:00')"
    )
    con.commit()
    con.close()

    store = EnactmentStore(db)
    cols = {
        r[1]
        for r in store._conn.execute("PRAGMA table_info(invariant_firings)").fetchall()
    }
    assert "audited_at" in cols and "audited_by_enactment_id" in cols
    # the pre-existing firing is unaudited and readable
    assert store.unaudited_invariant_firing_count() == 1
