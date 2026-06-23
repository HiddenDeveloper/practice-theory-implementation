"""Harness-agnostic error classification, the circuit breaker, and the stop.

These guard the 2026-06-04 failure mode: a Codex usage-limit returned
`turn.failed` on stdout while the adapter logged only the stderr banner, so the
loop spun 723 failed dispatches instead of stopping. The classifier must read
the real error off stdout JSONL; the breaker must trip on quota immediately and
on repeated model errors past the threshold.
"""

from __future__ import annotations

from practice_theory_implementation.harness_errors import (
    CircuitBreaker,
    ErrorKind,
    ModelError,
    StopDecision,
    classify_dispatch_error,
    classify_exception,
    clear_halt_cooldown,
    halt_cooldown_remaining,
    observe_dispatch,
    read_halt_cooldown,
    record_halt_cooldown,
    run_autonomic_stop,
)

# The real captured codex exec --json output for an exhausted subscription.
CODEX_QUOTA_STDOUT = "\n".join(
    [
        "Reading additional input from stdin...",
        '{"type":"thread.started","thread_id":"019e9101"}',
        '{"type":"turn.started"}',
        '{"type":"error","message":"You\'ve hit your usage limit. Visit '
        "https://chatgpt.com/codex/settings/usage to purchase more credits or "
        'try again at 2:26 PM."}',
        '{"type":"turn.failed","error":{"message":"You\'ve hit your usage limit. '
        'Visit https://chatgpt.com/codex/settings/usage or try again at 2:26 PM."}}',
    ]
)
CODEX_BANNER_STDERR = "Reading additional input from stdin..."


def test_codex_quota_classified_from_stdout() -> None:
    err = classify_dispatch_error("codex", 1, CODEX_QUOTA_STDOUT, CODEX_BANNER_STDERR)
    assert err is not None
    assert err.kind is ErrorKind.QUOTA_EXHAUSTED
    assert err.kind.trips_immediately
    assert err.retry_at is not None and "2:26" in err.retry_at
    # The classified message is the real cause, not the harmless stdin banner.
    assert "usage limit" in err.message.lower()


def test_codex_success_is_none() -> None:
    ok = '{"type":"turn.completed","usage":{"input_tokens":10,"output_tokens":2}}'
    assert classify_dispatch_error("codex", 0, ok, "") is None


def test_codex_nonzero_without_error_event_is_model_error() -> None:
    err = classify_dispatch_error("codex", 1, "", "segfault")
    assert err is not None and err.kind is ErrorKind.MODEL_ERROR


def test_claude_cli_rate_limit() -> None:
    err = classify_dispatch_error("anthropic_cli", 1, "", "Error: 429 rate_limit_error")
    assert err is not None and err.kind is ErrorKind.RATE_LIMIT


def test_generic_provider_fallback_quota() -> None:
    # A not-yet-registered harness (e.g. gemini/ollama) still classifies.
    err = classify_dispatch_error("gemini", 1, "", "RESOURCE_EXHAUSTED: quota exceeded")
    assert err is not None and err.kind is ErrorKind.QUOTA_EXHAUSTED
    assert err.provider == "gemini"


def test_classify_exception_maps_text() -> None:
    err = classify_exception("anthropic", RuntimeError("overloaded_error: 529"))
    assert err.kind is ErrorKind.RATE_LIMIT
    assert err.provider == "anthropic"


def test_breaker_quota_trips_immediately() -> None:
    breaker = CircuitBreaker()
    err = classify_dispatch_error("codex", 1, CODEX_QUOTA_STDOUT, "")
    decision = breaker.record_error(err)
    assert decision is not None
    assert decision.consecutive == 1
    assert "quota_exhausted" in decision.reason
    assert breaker.tripped


def test_breaker_repeated_model_error_trips_on_third() -> None:
    breaker = CircuitBreaker(error_threshold=2)
    err = ModelError(ErrorKind.MODEL_ERROR, "boom", "codex")
    assert breaker.record_error(err) is None  # 1
    assert breaker.record_error(err) is None  # 2
    decision = breaker.record_error(err)  # 3 > 2 -> trip
    assert decision is not None and decision.consecutive == 3


def test_breaker_resets_on_success() -> None:
    breaker = CircuitBreaker(error_threshold=2)
    err = ModelError(ErrorKind.MODEL_ERROR, "boom", "codex")
    breaker.record_error(err)
    breaker.record_error(err)
    breaker.record_success()
    assert breaker.record_error(err) is None  # counter was reset


def test_run_autonomic_stop_invokes_command(tmp_path, monkeypatch) -> None:
    marker = tmp_path / "stopped"
    monkeypatch.setenv(
        "PRACTICE_AUTONOMIC_STOP_CMD", f"touch {marker}"
    )
    assert run_autonomic_stop("test reason") is True
    assert marker.exists()


def test_observe_dispatch_trips_and_signals(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PRACTICE_AUTONOMIC_STOP_CMD", "true")
    monkeypatch.setenv(
        "PRACTICE_AUTONOMIC_HALT_FILE", str(tmp_path / "autonomic_halt.json")
    )
    signalled = {"stopped": False}

    breaker = CircuitBreaker()
    quota = ModelError(ErrorKind.QUOTA_EXHAUSTED, "usage limit", "codex", retry_at="2:26 PM")
    should_stop = observe_dispatch(
        breaker, quota, on_stop_signal=lambda: signalled.__setitem__("stopped", True)
    )
    assert should_stop is True
    assert signalled["stopped"] is True
    # A trip persists a cooldown so a restarted process backs off.
    assert halt_cooldown_remaining() > 0


def test_observe_dispatch_success_does_not_stop() -> None:
    breaker = CircuitBreaker()
    assert observe_dispatch(breaker, None) is False
    assert observe_dispatch(None, None) is False


# --- persistent halt cooldown ----------------------------------------------


def _decision() -> StopDecision:
    err = ModelError(
        ErrorKind.QUOTA_EXHAUSTED, "usage limit", "codex", retry_at="2:44 PM"
    )
    return StopDecision(reason="quota_exhausted: usage limit", error=err, consecutive=1)


def test_record_and_read_halt_cooldown(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv(
        "PRACTICE_AUTONOMIC_HALT_FILE", str(tmp_path / "autonomic_halt.json")
    )
    monkeypatch.setenv("PRACTICE_AUTONOMIC_HALT_COOLDOWN_SECONDS", "1800")
    until = record_halt_cooldown(_decision(), now=1000.0)
    assert until == 1000.0 + 1800.0
    payload = read_halt_cooldown()
    assert payload is not None
    assert payload["provider"] == "codex"
    assert payload["kind"] == "quota_exhausted"
    assert payload["retry_at"] == "2:44 PM"


def test_halt_cooldown_remaining_counts_down_and_expires(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv(
        "PRACTICE_AUTONOMIC_HALT_FILE", str(tmp_path / "autonomic_halt.json")
    )
    record_halt_cooldown(_decision(), now=1000.0, cooldown_seconds=600.0)
    assert halt_cooldown_remaining(now=1000.0) == 600.0
    assert halt_cooldown_remaining(now=1300.0) == 300.0
    # At/after the deadline it reads as expired, not negative.
    assert halt_cooldown_remaining(now=1600.0) == 0.0
    assert halt_cooldown_remaining(now=9999.0) == 0.0


def test_halt_cooldown_absent_is_zero_and_clear_is_safe(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv(
        "PRACTICE_AUTONOMIC_HALT_FILE", str(tmp_path / "autonomic_halt.json")
    )
    assert halt_cooldown_remaining() == 0.0
    assert read_halt_cooldown() is None
    clear_halt_cooldown()  # no file → no error
    record_halt_cooldown(_decision())
    assert read_halt_cooldown() is not None
    clear_halt_cooldown()
    assert read_halt_cooldown() is None
