"""The two-loop separation — the reactive route must never carry autonomic work.

The risk (strange-loop essay, §"A smile and a wink to Douglas Hofstadter"): if
an autonomic completion dispatches a reactive notification, the Judge ends up
judging its own judging — each pass finishing, dispatching, triggering another,
a self-consuming spin that never quiets. The fix is two loops on two timescales:
the reactive route carries only *somatic* completions; *autonomic* history is
examined by a scheduled reflective route.

These are guard tests. Before the fix landed, routing had no `mode` filter and
carried every closed enactment, autonomic included — so
`test_reactive_route_excludes_autonomic_enactments` would have failed. It is the
tripwire that makes a future regression loud instead of silent.
"""

from __future__ import annotations

from pathlib import Path

from practice_theory_implementation.trail import EnactmentStore


def _claim_all_judge_inbox(store: EnactmentStore) -> set[str]:
    """Enactment ids currently routed to the Judge, via the real claim path."""
    ids: set[str] = set()
    while (row := store.next_judge_work(worker_id="test")) is not None:
        ids.add(row.enactment_id)
    return ids


def test_reactive_route_excludes_autonomic_enactments(tmp_path: Path) -> None:
    store = EnactmentStore(tmp_path / "trail.db")
    somatic = store.open_enactment("correspondent", mode="somatic")
    judge = store.open_enactment("judge", mode="autonomic")
    store.close_enactment(somatic)
    store.close_enactment(judge)

    routed = store.route_closed_enactments_to_judge_inbox()

    inbox = _claim_all_judge_inbox(store)
    assert somatic in inbox
    assert judge not in inbox  # the spin-breaker: autonomic is NOT reactively routed
    assert routed == 1
    store.close()


def test_reflective_route_carries_autonomic_history(tmp_path: Path) -> None:
    store = EnactmentStore(tmp_path / "trail.db")
    judge = store.open_enactment("judge", mode="autonomic")
    smoother = store.open_enactment("smoother", mode="autonomic")
    store.close_enactment(judge)
    store.close_enactment(smoother)

    # Reactive pass ignores them entirely...
    assert store.route_closed_enactments_to_judge_inbox() == 0
    # ...the reflective pass picks them up, on its own timescale.
    routed = store.route_autonomic_history_to_judge_inbox()

    inbox = _claim_all_judge_inbox(store)
    assert judge in inbox
    assert smoother in inbox
    assert routed == 2
    store.close()


def test_reflective_route_respects_since_watermark(tmp_path: Path) -> None:
    # The reflective loop passes a moving `since` cutoff so it never re-grinds
    # pre-existing autonomic history. A `since` after the enactment closed routes
    # nothing; a `since` before it routes it.
    store = EnactmentStore(tmp_path / "trail.db")
    eid = store.open_enactment("judge", mode="autonomic")
    store.close_enactment(eid)

    assert store.route_autonomic_history_to_judge_inbox("2099-01-01T00:00:00") == 0
    routed = store.route_autonomic_history_to_judge_inbox("2000-01-01T00:00:00")
    assert routed == 1
    assert eid in _claim_all_judge_inbox(store)
    store.close()


def test_default_mode_is_somatic(tmp_path: Path) -> None:
    # A caller that does not specify mode is treated as somatic (reactive),
    # so an unlabelled enactment is examined, never silently skipped.
    store = EnactmentStore(tmp_path / "trail.db")
    eid = store.open_enactment("correspondent")
    store.close_enactment(eid)
    assert store.route_closed_enactments_to_judge_inbox() == 1
    store.close()


def test_mode_column_backfills_on_existing_db(tmp_path: Path) -> None:
    # A trail DB created before the `mode` column must migrate cleanly and
    # treat its pre-existing rows as somatic (the safe, examined default).
    db = tmp_path / "trail.db"
    store = EnactmentStore(db)
    eid = store.open_enactment("correspondent", mode="somatic")
    store.close_enactment(eid)
    store.close()

    # Reopen — _migrate runs again, idempotently — and routing still works.
    reopened = EnactmentStore(db)
    assert reopened.route_closed_enactments_to_judge_inbox() == 1
    reopened.close()
