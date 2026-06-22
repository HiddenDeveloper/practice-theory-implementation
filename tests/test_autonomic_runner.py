"""The runner's role selection — which loops run for which env flags."""

from __future__ import annotations

import os

import pytest

from practice_theory_implementation import autonomic_runner


@pytest.fixture(autouse=True)
def _clear_remsleep_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(autonomic_runner.REMSLEEP_ONLY_ENV, raising=False)
    monkeypatch.delenv(autonomic_runner.REMSLEEP_ENABLED_ENV, raising=False)
    monkeypatch.delenv(autonomic_runner.REMSLEEP_STARTUP_DELAY_ENV, raising=False)
    monkeypatch.delenv(autonomic_runner.REMSLEEP_MAX_BACKLOG_ENV, raising=False)
    monkeypatch.delenv(autonomic_runner.REMSLEEP_BACKLOG_RETRY_ENV, raising=False)
    monkeypatch.delenv(autonomic_runner.INBOX_ROLES_ENABLED_ENV, raising=False)
    monkeypatch.delenv(autonomic_runner.AUTONOMIC_CONFIG_ENV, raising=False)
    monkeypatch.delenv(autonomic_runner.SOMATIC_SCHEDULER_ENABLED_ENV, raising=False)
    monkeypatch.delenv(autonomic_runner.SOMATIC_SCHEDULER_TARGET_ENV, raising=False)
    monkeypatch.delenv(autonomic_runner.SOMATIC_SCHEDULER_INTERVAL_ENV, raising=False)
    monkeypatch.delenv(
        autonomic_runner.SOMATIC_SCHEDULER_STARTUP_DELAY_ENV, raising=False
    )
    monkeypatch.delenv(autonomic_runner.SOMATIC_SCHEDULER_TASK_ENV, raising=False)
    monkeypatch.delenv(autonomic_runner.SOMATIC_SCHEDULER_MCP_URL_ENV, raising=False)
    monkeypatch.delenv(autonomic_runner.AUTONOMIC_LOG_FILE_ENV, raising=False)
    monkeypatch.delenv("PRACTICE_AUTONOMIC_PROVIDER", raising=False)
    monkeypatch.delenv("PRACTICE_CODEX_MODEL", raising=False)
    monkeypatch.delenv("PRACTICE_CODEX_REASONING_EFFORT", raising=False)


def test_default_runs_inbox_roles_without_remsleep() -> None:
    # Judge + Smoother, no RemSleep.
    assert autonomic_runner._selected_roles() == (True, False)


def test_config_can_disable_inbox_roles(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(autonomic_runner.INBOX_ROLES_ENABLED_ENV, "0")
    assert autonomic_runner._selected_roles() == (False, False)


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


def test_remsleep_latency_guard_defaults() -> None:
    assert autonomic_runner._remsleep_startup_delay_seconds() == 300.0
    assert autonomic_runner._remsleep_max_autonomic_backlog() == 10
    assert autonomic_runner._remsleep_backlog_retry_seconds() == 300.0


def test_remsleep_latency_guard_env_overrides(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(autonomic_runner.REMSLEEP_STARTUP_DELAY_ENV, "30")
    monkeypatch.setenv(autonomic_runner.REMSLEEP_MAX_BACKLOG_ENV, "3")
    monkeypatch.setenv(autonomic_runner.REMSLEEP_BACKLOG_RETRY_ENV, "5")

    assert autonomic_runner._remsleep_startup_delay_seconds() == 30.0
    assert autonomic_runner._remsleep_max_autonomic_backlog() == 3
    assert autonomic_runner._remsleep_backlog_retry_seconds() == 10.0


def test_autonomic_inbox_backlog_combines_judge_and_smoother() -> None:
    class Store:
        def pending_judge_inbox_count(self) -> int:
            return 2

        def pending_smoother_inbox_count(self) -> int:
            return 7

    assert autonomic_runner._autonomic_inbox_backlog(Store()) == 9


def test_somatic_scheduler_defaults() -> None:
    assert not autonomic_runner._somatic_scheduler_enabled()
    assert autonomic_runner._somatic_scheduler_target() == "stock_investor"
    assert autonomic_runner._somatic_scheduler_interval_seconds() == 3600.0
    assert autonomic_runner._somatic_scheduler_startup_delay_seconds() == 60.0
    assert "stock_investor" in autonomic_runner._somatic_scheduler_task("stock_investor")
    assert (
        autonomic_runner._autonomic_log_file()
        == autonomic_runner.DEFAULT_AUTONOMIC_LOG_FILE
    )


def test_somatic_scheduler_env_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(autonomic_runner.SOMATIC_SCHEDULER_ENABLED_ENV, "1")
    monkeypatch.setenv(autonomic_runner.SOMATIC_SCHEDULER_TARGET_ENV, "reflection")
    monkeypatch.setenv(autonomic_runner.SOMATIC_SCHEDULER_INTERVAL_ENV, "30")
    monkeypatch.setenv(autonomic_runner.SOMATIC_SCHEDULER_STARTUP_DELAY_ENV, "0")
    monkeypatch.setenv(autonomic_runner.SOMATIC_SCHEDULER_TASK_ENV, "custom task")

    assert autonomic_runner._somatic_scheduler_enabled()
    assert autonomic_runner._somatic_scheduler_target() == "reflection"
    assert autonomic_runner._somatic_scheduler_interval_seconds() == 60.0
    assert autonomic_runner._somatic_scheduler_startup_delay_seconds() == 0.0
    assert autonomic_runner._somatic_scheduler_task("reflection") == "custom task"


def test_autonomic_log_file_env_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(autonomic_runner.AUTONOMIC_LOG_FILE_ENV, "logs/runner.log")
    log_file = autonomic_runner._autonomic_log_file()
    assert log_file is not None
    assert log_file.as_posix() == "logs/runner.log"

    monkeypatch.setenv(autonomic_runner.AUTONOMIC_LOG_FILE_ENV, "")
    assert autonomic_runner._autonomic_log_file() is None


def test_autonomic_config_maps_to_runtime_env(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    config = tmp_path / "scheduler.yaml"
    config.write_text(
        """
llm:
  provider: codex
  model: gpt-5.5
  reasoning_effort: high
runtime:
  inbox_roles_enabled: false
  log_file: data/test-scheduler.log
  otel_console: true
somatic_schedule:
  enabled: true
  practice: reflection
  interval_seconds: 120
  startup_delay_seconds: 0
  mcp_url: http://127.0.0.1:7180/mcp
  task: custom scheduled pass
""",
        encoding="utf-8",
    )
    monkeypatch.setenv(autonomic_runner.AUTONOMIC_CONFIG_ENV, str(config))

    autonomic_runner._apply_autonomic_config(autonomic_runner._load_autonomic_config())

    assert os.environ["PRACTICE_AUTONOMIC_PROVIDER"] == "codex"
    assert os.environ["PRACTICE_CODEX_MODEL"] == "gpt-5.5"
    assert os.environ["PRACTICE_CODEX_REASONING_EFFORT"] == "high"
    assert os.environ[autonomic_runner.INBOX_ROLES_ENABLED_ENV] == "0"
    assert os.environ[autonomic_runner.AUTONOMIC_LOG_FILE_ENV] == "data/test-scheduler.log"
    assert os.environ["PRACTICE_OTEL_CONSOLE"] == "1"
    assert autonomic_runner._somatic_scheduler_enabled()
    assert autonomic_runner._somatic_scheduler_target() == "reflection"
    assert autonomic_runner._somatic_scheduler_interval_seconds() == 120.0
    assert autonomic_runner._somatic_scheduler_startup_delay_seconds() == 0.0
    assert os.environ[autonomic_runner.SOMATIC_SCHEDULER_MCP_URL_ENV] == (
        "http://127.0.0.1:7180/mcp"
    )
    assert autonomic_runner._somatic_scheduler_task("reflection") == "custom scheduled pass"


def test_scheduled_practitioner_role_is_target_scoped() -> None:
    assert (
        autonomic_runner._scheduled_practitioner_role("stock_investor")
        == "stock_investor_practitioner"
    )


def test_scheduled_practitioner_adapter_uses_target_bundle() -> None:
    adapter = autonomic_runner._build_scheduled_practitioner_adapter(
        "codex", "stock_investor"
    )

    assert adapter.config.role == "stock_investor_practitioner"
    assert adapter.config.bundle_id == "stock_investor"
    assert adapter.config.mcp_mode == "somatic"
    assert "Stock Investor" in adapter.config.brief


@pytest.mark.parametrize(
    "kind",
    [
        "coverage_gap",
        "coverage_gap_noop",
        "coverage_report",
        "memory_coverage_gap",
        "no_op",
        "no_op_recall",
        "noop",
        "noop_review",
        "recall_blocked_noop",
        "source_basis_gap",
    ],
)
def test_diagnostic_memory_signals_do_not_need_consolidation_dispatch(
    kind: str,
) -> None:
    assert autonomic_runner._is_diagnostic_memory_signal({"kind": kind})


@pytest.mark.parametrize(
    "kind",
    [
        "memory_candidate",
        "memory_delta",
        "context_candidate_with_coverage_gap",
        "substrate_change_candidate_with_coverage_gap",
        "",
        None,
    ],
)
def test_candidate_memory_signals_still_go_to_consolidation(
    kind: object,
) -> None:
    assert not autonomic_runner._is_diagnostic_memory_signal({"kind": kind})
