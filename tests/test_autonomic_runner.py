"""The runner's role selection — which loops run for which env flags."""

from __future__ import annotations

import pytest

from practice_theory_implementation import autonomic_runner


@pytest.fixture(autouse=True)
def _clear_remsleep_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(autonomic_runner.REMSLEEP_ONLY_ENV, raising=False)
    monkeypatch.delenv(autonomic_runner.REMSLEEP_ENABLED_ENV, raising=False)


def test_default_runs_inbox_roles_without_remsleep() -> None:
    # Judge + Smoother, no RemSleep.
    assert autonomic_runner._selected_roles() == (True, False)


def test_enabled_runs_inbox_roles_and_remsleep(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(autonomic_runner.REMSLEEP_ENABLED_ENV, "1")
    assert autonomic_runner._selected_roles() == (True, True)


def test_remsleep_only_skips_inbox_roles_and_implies_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Focused keeper: RemSleep loops only, no Judge/Smoother/dispatcher.
    monkeypatch.setenv(autonomic_runner.REMSLEEP_ONLY_ENV, "1")
    assert autonomic_runner._selected_roles() == (False, True)


def test_remsleep_only_overrides_disabled_enabled_flag(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(autonomic_runner.REMSLEEP_ONLY_ENV, "1")
    monkeypatch.setenv(autonomic_runner.REMSLEEP_ENABLED_ENV, "0")
    assert autonomic_runner._selected_roles() == (False, True)
