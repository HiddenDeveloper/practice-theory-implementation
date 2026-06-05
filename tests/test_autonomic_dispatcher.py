"""`route_now` must exercise production dispatch semantics, not the legacy route.

`route_now` is the synchronous single-shot router used by the verify
(`verify_autonomic_loop`) and the live-provider eval (`drive_live`). For a long
time it called the legacy bulk `route_closed_enactments_to_judge_inbox`, which
routes *every* closed somatic enactment straight to the Judge inbox. That let
the harness pass while bypassing the deterministic triage gate the live loops
actually use — clean work that production clears with no Judge dispatch would
still be queued for the LLM under the harness, so a triage regression could not
be caught here. These tests pin `route_now` to the triage semantics so that gap
cannot silently reopen.
"""

from __future__ import annotations

from pathlib import Path

from practice_theory_implementation.autonomic_dispatcher import route_now
from practice_theory_implementation.trail import EnactmentStore


def _seed(
    store: EnactmentStore,
    bundle: str,
    *,
    mode: str = "somatic",
    steps: int = 1,
    error: bool = False,
) -> str:
    eid = store.open_enactment(bundle, mode=mode)
    for _ in range(steps):
        store.record_step(
            enactment_id=eid,
            affordance_id="a",
            material_name="m",
            arguments={"x": 1},
            result={"error": "boom"} if error else {"ok": True},
            started_at="2026-06-04T00:00:00+00:00",
            completed_at="2026-06-04T00:00:01+00:00",
            duration_ms=5,
        )
    store.close_enactment(eid)
    return eid


def test_route_now_clears_clean_work_without_judge_dispatch(tmp_path: Path) -> None:
    # A resolved bundle with steps and no error signal is clean: the legacy
    # bulk route would have queued it for the Judge; triage must not.
    store = EnactmentStore(tmp_path / "trail.db")
    _seed(store, "judge", mode="somatic", steps=2)

    j, _s = route_now(store)

    assert j == 0
    assert store.pending_judge_inbox_count() == 0


def test_route_now_routes_only_the_ambiguous_to_judge(tmp_path: Path) -> None:
    store = EnactmentStore(tmp_path / "trail.db")
    _seed(store, "judge", mode="somatic", steps=2)  # clean
    errored = _seed(store, "smoother", mode="somatic", error=True)  # ambiguous

    j, _s = route_now(store)

    assert j == 1
    assert store.pending_judge_inbox_count() == 1
    claimed = store.next_judge_work(worker_id="t", lease_seconds=60)
    assert claimed is not None and claimed.enactment_id == errored


def test_route_now_emits_provable_friction_to_smoother_not_judge(
    tmp_path: Path,
) -> None:
    # An enactment tagged to a bundle that no longer resolves is provable
    # friction: deterministic, no Judge dispatch, routed to the Smoother.
    store = EnactmentStore(tmp_path / "trail.db")
    _seed(store, "user_focused_engagement", mode="somatic")

    j, s = route_now(store)

    assert j == 0
    assert store.pending_judge_inbox_count() == 0
    assert s == 1
    assert store.pending_smoother_inbox_count() == 1


def test_route_now_also_triages_autonomic_enactments(tmp_path: Path) -> None:
    # The strange-loop half: route_now must triage autonomic (Judge/Smoother)
    # enactments too, not just somatic ones. The legacy somatic-only route would
    # have missed the autonomic enactment entirely; triage classifies it the
    # same way — clean autonomic work is a no-finding, an ambiguous one queues.
    store = EnactmentStore(tmp_path / "trail.db")
    _seed(store, "judge", mode="autonomic", steps=2)  # clean autonomic → no-finding
    errored = _seed(store, "judge", mode="autonomic", error=True)  # ambiguous

    j, _s = route_now(store)

    assert j == 1
    assert store.pending_judge_inbox_count() == 1
    claimed = store.next_judge_work(worker_id="t", lease_seconds=60)
    assert claimed is not None and claimed.enactment_id == errored


def test_route_now_triages_both_modes_in_one_call(tmp_path: Path) -> None:
    # One ambiguous somatic + one ambiguous autonomic → both reach the Judge in
    # a single route_now (the reactive and reflective passes the verify drives).
    store = EnactmentStore(tmp_path / "trail.db")
    _seed(store, "judge", mode="somatic", error=True)
    _seed(store, "judge", mode="autonomic", error=True)

    j, _s = route_now(store)

    assert j == 2
    assert store.pending_judge_inbox_count() == 2


def test_route_now_is_idempotent(tmp_path: Path) -> None:
    store = EnactmentStore(tmp_path / "trail.db")
    _seed(store, "smoother", mode="somatic", error=True)

    first = route_now(store)
    second = route_now(store)

    assert first == (1, 0)
    assert second == (0, 0)
    assert store.pending_judge_inbox_count() == 1
