"""Tests for the escalate-when-unsure Phase-1 primitives."""

from __future__ import annotations

from typing import Any

import pytest

from practice_theory_implementation import escalation
from practice_theory_implementation.escalation import Severity, emit_escalation
from practice_theory_implementation.trail import TRAIL_PATH_ENV, EnactmentStore


@pytest.fixture
def store(tmp_path, monkeypatch: pytest.MonkeyPatch) -> EnactmentStore:
    path = tmp_path / "trail.db"
    monkeypatch.setenv(TRAIL_PATH_ENV, str(path))
    return EnactmentStore(path)


def test_record_escalation_is_idempotent_on_dedup_key(store: EnactmentStore) -> None:
    a = store.record_escalation(
        kind="k", severity="attention", source="s", dedup_key="d1", content="c"
    )
    b = store.record_escalation(
        kind="k", severity="attention", source="s", dedup_key="d1", content="c again"
    )
    assert a == b  # same open escalation, not a stream
    assert len(store.open_escalations()) == 1

    # once resolved, the same key may open a fresh escalation
    assert store.resolve_escalations("d1") == 1
    c = store.record_escalation(
        kind="k", severity="attention", source="s", dedup_key="d1", content="c3"
    )
    assert c != a
    assert len(store.open_escalations()) == 1


def test_notify_line_unconfigured_is_noop(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(escalation.LINE_TOKEN_ENV, raising=False)
    monkeypatch.delenv(escalation.LINE_TO_ENV, raising=False)
    assert escalation.notify_line("hello") is False


def test_notify_line_posts_when_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(escalation.LINE_TOKEN_ENV, "tok")
    monkeypatch.setenv(escalation.LINE_TO_ENV, "U123")
    sent: dict[str, Any] = {}

    class _Resp:
        def raise_for_status(self) -> None:
            return None

    def _fake_post(url: str, headers: dict, json: dict, timeout: float) -> _Resp:
        sent["url"] = url
        sent["headers"] = headers
        sent["json"] = json
        return _Resp()

    import httpx

    monkeypatch.setattr(httpx, "post", _fake_post)
    assert escalation.notify_line("ping") is True
    assert sent["url"] == escalation.LINE_PUSH_URL
    assert sent["headers"]["Authorization"] == "Bearer tok"
    assert sent["json"] == {"to": "U123", "messages": [{"type": "text", "text": "ping"}]}


def test_emit_critical_pushes_and_marks_notified(
    store: EnactmentStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    pushed: list[str] = []
    monkeypatch.setattr(
        escalation, "notify_line", lambda text: pushed.append(text) or True
    )
    eid = emit_escalation(
        kind="autonomic_halt",
        severity=Severity.CRITICAL,
        source="circuit_breaker",
        dedup_key="halt:quota",
        content="the loop halted",
        store=store,
    )
    assert eid is not None
    assert len(pushed) == 1
    row = next(r for r in store.open_escalations() if r.id == eid)
    assert row.notified_at is not None and row.state == "notified"


def test_emit_attention_records_but_does_not_push(
    store: EnactmentStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    pushed: list[str] = []
    monkeypatch.setattr(
        escalation, "notify_line", lambda text: pushed.append(text) or True
    )
    eid = emit_escalation(
        kind="friction_unresolved",
        severity=Severity.ATTENTION,
        source="friction_reconcile",
        dedup_key="friction_tombstoned:7",
        content="unresolved",
        store=store,
    )
    assert eid is not None
    assert pushed == []  # attention does not push in phase 1
    row = next(r for r in store.open_escalations() if r.id == eid)
    assert row.notified_at is None and row.state == "open"
