"""Deterministic Friction-lifecycle reconciliation.

A Smoother consumes its inbox row on dispatch-ran, not on Friction-addressed, so
an incomplete pass strands a Friction (consumed, never re-claimed; unaddressed,
never resolved). Reconciliation re-routes such Frictions up to a cap, then
tombstones them, so the lifecycle always terminates.
"""

from __future__ import annotations

from pathlib import Path

from practice_theory_implementation.friction_reconcile import (
    reconcile_smoother_frictions,
)
from practice_theory_implementation.trail import EnactmentStore


def _consume_unaddressed(
    store: EnactmentStore, *, consumer: str | None = None, kind: str = "narrow_engagement"
) -> tuple[int, str]:
    """Record a Friction, route it, and have a (closed by default) Smoother
    enactment consume it without addressing it."""
    fid = store.record_friction(
        observing_enactment_id="judge:obs",
        target_enactment_id="target",
        kind=kind,
        content="incomplete smoother pass",
    )
    store.route_friction_to_smoother_inbox()
    if consumer is None:
        consumer = store.open_enactment("smoother", mode="autonomic")
        store.close_enactment(consumer)
    store.consume_smoother_inbox(fid, consumer_enactment_id=consumer)
    return fid, consumer


def test_reroute_reopens_and_bumps_attempts(tmp_path: Path) -> None:
    store = EnactmentStore(tmp_path / "trail.db")
    fid, _ = _consume_unaddressed(store)
    assert store.pending_smoother_inbox_count() == 0  # consumed, not re-claimable

    summary = reconcile_smoother_frictions(store)

    assert summary.rerouted == 1 and summary.tombstoned == 0
    assert store.pending_smoother_inbox_count() == 1  # re-opened for another pass
    friction = next(f for f in store.all_friction() if f.id == fid)
    assert friction.addressed_at is None  # still unresolved, just retryable
    assert store.smoother_frictions_to_reconcile() == []  # no longer consumed


def test_skips_addressed_and_in_flight(tmp_path: Path) -> None:
    store = EnactmentStore(tmp_path / "trail.db")
    # Addressed: consumed and resolved — nothing to do.
    fid_a, consumer_a = _consume_unaddressed(store)
    store.mark_friction_addressed(fid_a, consumer_a)
    # In-flight: consumer still open — must not be disturbed.
    open_consumer = store.open_enactment("smoother", mode="autonomic")
    _consume_unaddressed(store, consumer=open_consumer, kind="rule_neglect")

    summary = reconcile_smoother_frictions(store)

    assert summary.examined == 0


def test_tombstones_at_cap_with_basis(tmp_path: Path) -> None:
    store = EnactmentStore(tmp_path / "trail.db")
    fid, consumer = _consume_unaddressed(store)

    # Two re-route passes (attempts 0->1, 1->2), the Smoother re-consuming each
    # time without addressing it.
    assert reconcile_smoother_frictions(store, max_attempts=2).rerouted == 1
    store.consume_smoother_inbox(fid, consumer_enactment_id=consumer)
    assert reconcile_smoother_frictions(store, max_attempts=2).rerouted == 1
    store.consume_smoother_inbox(fid, consumer_enactment_id=consumer)

    # attempts == 2 >= cap → tombstone with a recorded basis.
    summary = reconcile_smoother_frictions(store, max_attempts=2)

    assert summary.tombstoned == 1 and summary.rerouted == 0
    friction = next(f for f in store.all_friction() if f.id == fid)
    assert friction.addressed_at is not None
    assert friction.addressed_by_enactment_id == (
        "system:reconcile:unresolved_after_2_attempts"
    )


def test_clean_state_is_a_noop(tmp_path: Path) -> None:
    store = EnactmentStore(tmp_path / "trail.db")
    summary = reconcile_smoother_frictions(store)
    assert summary.examined == 0 and summary.rerouted == 0 and summary.tombstoned == 0


def test_claiming_smoother_work_returns_attempts(tmp_path: Path) -> None:
    # next_smoother_work builds a SmootherInboxRow from `RETURNING *`, so the new
    # attempts column must be a field on the row — otherwise the claim raises and
    # the Smoother loop crashes. Guards that regression.
    store = EnactmentStore(tmp_path / "trail.db")
    store.record_friction(
        observing_enactment_id="judge:obs",
        target_enactment_id="target",
        kind="narrow_engagement",
        content="c",
    )
    store.route_friction_to_smoother_inbox()

    claimed = store.next_smoother_work(worker_id="t", lease_seconds=60)

    assert claimed is not None
    assert claimed.attempts == 0
