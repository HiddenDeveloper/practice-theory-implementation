"""Harness-agnostic model-error classification, circuit-breaker, and the
deterministic autonomic stop.

The autonomic loop drives a model through one of several harnesses (codex
`codex exec`, Claude `claude -p`, the Anthropic SDK today; gemini/ollama
later). When the model itself fails — usage quota exhausted, rate limited,
auth gone, or a repeated provider error — the loop must not keep spinning
failed dispatches: a quota-failed dispatch produces no enactment, so its
inbox row is never consumed and the inbox can only grow (the 2026-06-04
incident). Detection and the stop are *deterministic* — no LLM is involved in
deciding to halt.

Three pieces:

- `classify_dispatch_error` turns a finished harness invocation (return code +
  captured stdout/stderr) into a `ModelError | None`. Per-provider classifiers
  live in a registry so a new harness only has to `register_classifier`.
- `CircuitBreaker` accumulates errors and decides when to trip: quota/auth trip
  immediately; any other model error trips once it repeats past a threshold
  (default 2 → trips on the 3rd consecutive).
- `run_autonomic_stop` shells out to the operator's stop command
  (`make autonomic-stop` by default) to actually halt the autonomic processes.
"""

from __future__ import annotations

import contextlib
import json
import logging
import os
import re
import shlex
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

logger = logging.getLogger(__name__)

ERROR_THRESHOLD_ENV = "PRACTICE_AUTONOMIC_ERROR_THRESHOLD"
STOP_CMD_ENV = "PRACTICE_AUTONOMIC_STOP_CMD"
DEFAULT_STOP_CMD = "make autonomic-stop"
DEFAULT_ERROR_THRESHOLD = 2

# Persistent halt cooldown. The CircuitBreaker is in-memory, so a quota/auth
# halt that exits the process is defeated the moment a supervisor (pm2) restarts
# it: the fresh process starts with empty counters and re-dispatches at once,
# re-tripping every cycle (the 2026-06-21 restart storm — 2459 restarts, because
# each ~20s crash cycle exceeded pm2's min_uptime and reset its backoff). On a
# trip we write the cooldown to disk; a restarted process reads it and backs off
# until it expires instead of hammering the exhausted provider.
HALT_COOLDOWN_FILE_ENV = "PRACTICE_AUTONOMIC_HALT_FILE"
HALT_COOLDOWN_SECONDS_ENV = "PRACTICE_AUTONOMIC_HALT_COOLDOWN_SECONDS"
DEFAULT_HALT_COOLDOWN_FILE = Path("data/autonomic_halt.json")
DEFAULT_HALT_COOLDOWN_SECONDS = 3600.0

# Material name of the system-recorded step that marks a dispatch which failed
# after its subprocess had opened a consumer enactment. The runner writes it
# (carrying the classified error kind + message) and closes the enactment;
# triage recognises it to clear the enactment deterministically rather than
# routing an environmental failure to the Judge.
DISPATCH_FAILED_MATERIAL = "system_dispatch_failed"


class ErrorKind(StrEnum):
    """Why a model dispatch failed, classified harness-agnostically."""

    QUOTA_EXHAUSTED = "quota_exhausted"
    RATE_LIMIT = "rate_limit"
    AUTH = "auth"
    MODEL_ERROR = "model_error"
    UNKNOWN = "unknown"

    @property
    def trips_immediately(self) -> bool:
        """Quota and auth do not recover by retrying — stop on the first."""
        return self in (ErrorKind.QUOTA_EXHAUSTED, ErrorKind.AUTH)


@dataclass(frozen=True, slots=True)
class ModelError:
    """A classified harness/model failure. Deterministic — built from output."""

    kind: ErrorKind
    message: str
    provider: str
    retry_at: str | None = None
    raw: str = ""


# Substring patterns matched case-insensitively against harness output. Kept
# broad and provider-neutral so the same table classifies codex, claude, and
# future harnesses; order of checks (quota → auth → rate) is set in _match_kind.
_QUOTA_PATTERNS = (
    "usage limit",
    "out of codex messages",
    "out of messages",
    "quota",
    "insufficient_quota",
    "purchase more credits",
    "credit balance is too low",
    "exceeded your current quota",
    "billing",
)
_AUTH_PATTERNS = (
    "not logged in",
    "unauthorized",
    "401",
    "invalid api key",
    "authentication",
    "please run codex login",
    "please run /login",
    "please log in",
)
_RATE_PATTERNS = (
    "rate limit",
    "rate_limit",
    "429",
    "too many requests",
    "overloaded",
    "529",
)

_RETRY_AT_RE = re.compile(r"try again at ([^.\n]+)", re.IGNORECASE)


def _first_line(text: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line:
            return line
    return text.strip()


def _match_kind(text: str) -> ErrorKind | None:
    low = text.lower()
    if any(p in low for p in _QUOTA_PATTERNS):
        return ErrorKind.QUOTA_EXHAUSTED
    if any(p in low for p in _AUTH_PATTERNS):
        return ErrorKind.AUTH
    if any(p in low for p in _RATE_PATTERNS):
        return ErrorKind.RATE_LIMIT
    return None


def _retry_at(text: str) -> str | None:
    m = _RETRY_AT_RE.search(text)
    return m.group(1).strip() if m else None


def _model_error(kind: ErrorKind, text: str, provider: str) -> ModelError:
    return ModelError(
        kind=kind,
        message=_first_line(text)[:500] or kind.value,
        provider=provider,
        retry_at=_retry_at(text),
        raw=text[:2000],
    )


# --- per-harness classifiers ----------------------------------------------

Classifier = Callable[[int, str, str], "ModelError | None"]


def _codex_error_text(stdout: str) -> str | None:
    """Pull error message(s) from `codex exec --json` JSONL.

    The real failure (e.g. the usage-limit message) rides stdout as
    `{"type":"error","message":...}` / `{"type":"turn.failed","error":{...}}`
    events — NOT stderr, which only carries the harmless
    "Reading additional input from stdin..." banner. Returns None when no
    error event is present.
    """
    import json as _json

    msgs: list[str] = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            ev = _json.loads(line)
        except (ValueError, TypeError):
            continue
        if not isinstance(ev, dict):
            continue
        kind = ev.get("type")
        if kind == "error":
            m = ev.get("message")
            if isinstance(m, str):
                msgs.append(m)
        elif kind == "turn.failed":
            err = ev.get("error")
            m = err.get("message") if isinstance(err, dict) else None
            if isinstance(m, str):
                msgs.append(m)
    return " | ".join(msgs) if msgs else None


def _classify_codex(returncode: int, stdout: str, stderr: str) -> ModelError | None:
    err_text = _codex_error_text(stdout)
    if err_text is None and returncode == 0:
        return None
    text = err_text or stderr.strip() or stdout.strip()
    kind = _match_kind(text) or ErrorKind.MODEL_ERROR
    return _model_error(kind, text, "codex")


def _classify_claude_cli(
    returncode: int, stdout: str, stderr: str
) -> ModelError | None:
    combined = f"{stderr}\n{stdout}"
    kind = _match_kind(combined)
    if kind is None:
        if returncode == 0:
            return None
        kind = ErrorKind.MODEL_ERROR
    text = stderr.strip() or stdout.strip() or combined
    return _model_error(kind, text, "anthropic_cli")


def _classify_generic(provider: str) -> Classifier:
    def _classify(returncode: int, stdout: str, stderr: str) -> ModelError | None:
        if returncode == 0:
            return None
        text = stderr.strip() or stdout.strip() or f"exit {returncode}"
        kind = _match_kind(text) or ErrorKind.MODEL_ERROR
        return _model_error(kind, text, provider)

    return _classify


_CLASSIFIERS: dict[str, Classifier] = {
    "codex": _classify_codex,
    "anthropic_cli": _classify_claude_cli,
    "anthropic": _classify_claude_cli,
}


def register_classifier(provider: str, classifier: Classifier) -> None:
    """Register a harness classifier (e.g. for gemini/ollama expansion)."""
    _CLASSIFIERS[provider] = classifier


def classify_dispatch_error(
    provider: str, returncode: int, stdout: str | None, stderr: str | None
) -> ModelError | None:
    """Classify a finished subprocess dispatch. None means success."""
    classifier = _CLASSIFIERS.get(provider) or _classify_generic(provider)
    return classifier(returncode, stdout or "", stderr or "")


def classify_exception(provider: str, exc: BaseException) -> ModelError:
    """Classify a raised harness/SDK error (e.g. the Anthropic SDK path)."""
    text = f"{type(exc).__name__}: {exc}"
    kind = _match_kind(text) or ErrorKind.MODEL_ERROR
    return _model_error(kind, text, provider)


# --- circuit breaker -------------------------------------------------------


@dataclass(frozen=True, slots=True)
class StopDecision:
    """The breaker's decision to halt, with a deterministic reason string."""

    reason: str
    error: ModelError
    consecutive: int


def _env_threshold() -> int:
    raw = os.environ.get(ERROR_THRESHOLD_ENV, "").strip()
    if not raw:
        return DEFAULT_ERROR_THRESHOLD
    try:
        return max(1, int(raw))
    except ValueError:
        logger.warning(
            "invalid %s=%r, falling back to %d",
            ERROR_THRESHOLD_ENV,
            raw,
            DEFAULT_ERROR_THRESHOLD,
        )
        return DEFAULT_ERROR_THRESHOLD


class CircuitBreaker:
    """Accumulates model errors and decides when to halt the autonomic loop.

    Process-global: one instance is shared across the Judge, Smoother, and
    memory loops so a quota outage seen by any worker stops them all. Counts
    are per `(provider, kind)` and reset on any success — the threshold is for
    *consecutive* failures of the same kind, not a lifetime total.
    """

    def __init__(self, *, error_threshold: int | None = None) -> None:
        self._threshold = (
            error_threshold if error_threshold is not None else _env_threshold()
        )
        self._counts: dict[tuple[str, str], int] = {}
        self._tripped = False

    def record_success(self) -> None:
        self._counts.clear()

    def record_error(self, err: ModelError | None) -> StopDecision | None:
        """Record one dispatch outcome. Returns a StopDecision if it trips.

        `None` is a success and resets the consecutive counters.
        """
        if err is None:
            self.record_success()
            return None
        key = (err.provider, err.kind.value)
        count = self._counts.get(key, 0) + 1
        self._counts[key] = count
        if err.kind.trips_immediately:
            return self._trip(err, count, immediate=True)
        if count > self._threshold:
            return self._trip(err, count, immediate=False)
        return None

    def _trip(self, err: ModelError, count: int, *, immediate: bool) -> StopDecision:
        self._tripped = True
        if immediate:
            reason = f"{err.kind.value}: {err.message}"
        else:
            reason = f"{err.kind.value} repeated {count}x: {err.message}"
        if err.retry_at:
            reason += f" (retry at {err.retry_at})"
        return StopDecision(reason=reason, error=err, consecutive=count)

    @property
    def tripped(self) -> bool:
        return self._tripped


# --- persistent halt cooldown ----------------------------------------------


def _halt_cooldown_file() -> Path:
    raw = os.environ.get(HALT_COOLDOWN_FILE_ENV, "").strip()
    return Path(raw) if raw else DEFAULT_HALT_COOLDOWN_FILE


def _halt_cooldown_seconds() -> float:
    raw = os.environ.get(HALT_COOLDOWN_SECONDS_ENV, "").strip()
    if not raw:
        return DEFAULT_HALT_COOLDOWN_SECONDS
    try:
        return max(0.0, float(raw))
    except ValueError:
        logger.warning(
            "invalid %s=%r, falling back to %s",
            HALT_COOLDOWN_SECONDS_ENV,
            raw,
            DEFAULT_HALT_COOLDOWN_SECONDS,
        )
        return DEFAULT_HALT_COOLDOWN_SECONDS


def record_halt_cooldown(
    decision: StopDecision,
    *,
    now: float | None = None,
    cooldown_seconds: float | None = None,
) -> float:
    """Persist a halt cooldown so a restarted process backs off on boot.

    Written when the breaker trips. Carries the absolute ``until`` epoch
    timestamp plus the classified cause for operator visibility. The duration is
    a fixed cooldown (``PRACTICE_AUTONOMIC_HALT_COOLDOWN_SECONDS``, default 1h)
    rather than the parsed ``retry_at`` string, which is a bare local-time hint
    ("2:44 PM") with no date/zone to anchor it. Best-effort; returns the
    ``until`` timestamp written (or that would have been written on failure).
    """
    now = time.time() if now is None else now
    cooldown = _halt_cooldown_seconds() if cooldown_seconds is None else cooldown_seconds
    until = now + cooldown
    payload = {
        "until": until,
        "provider": decision.error.provider,
        "kind": decision.error.kind.value,
        "reason": decision.reason,
        "retry_at": decision.error.retry_at,
        "recorded_at": now,
    }
    path = _halt_cooldown_file()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    except OSError:
        logger.exception("failed to persist halt cooldown to %s", path)
    return until


def read_halt_cooldown() -> dict[str, object] | None:
    """Read the persisted halt cooldown payload, or None if absent/unreadable."""
    path = _halt_cooldown_file()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError, OSError):
        return None
    return payload if isinstance(payload, dict) else None


def halt_cooldown_remaining(*, now: float | None = None) -> float:
    """Seconds left on a persisted halt cooldown; 0.0 if none or expired."""
    payload = read_halt_cooldown()
    if payload is None:
        return 0.0
    until = payload.get("until")
    if not isinstance(until, (int, float)):
        return 0.0
    now = time.time() if now is None else now
    return max(0.0, float(until) - now)


def clear_halt_cooldown() -> None:
    """Remove the persisted halt cooldown (after it has been waited out)."""
    with contextlib.suppress(FileNotFoundError, OSError):
        _halt_cooldown_file().unlink()


# --- deterministic stop ----------------------------------------------------


def run_autonomic_stop(reason: str, *, timeout: float = 60.0) -> bool:
    """Halt the autonomic processes deterministically (no LLM).

    Runs the operator's stop command — `make autonomic-stop` by default, which
    takes down both the autonomic HTTP MCP server and the keeper — overridable
    via PRACTICE_AUTONOMIC_STOP_CMD. The keeper may be killed mid-call (it is
    deleting itself); callers should set their stop event *before* invoking
    this so the rest of the loop unwinds cleanly. Best-effort; returns whether
    the command exited 0.
    """
    cmd = os.environ.get(STOP_CMD_ENV, "").strip() or DEFAULT_STOP_CMD
    logger.warning("AUTONOMIC HALT — running deterministic stop (%s): %s", cmd, reason)
    try:
        result = subprocess.run(  # noqa: S603 - operator-configured command
            shlex.split(cmd),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except Exception:
        logger.exception("autonomic stop command failed to run: %s", cmd)
        return False
    if result.returncode != 0:
        logger.error(
            "autonomic stop command exited %d: %s",
            result.returncode,
            (result.stderr or "").strip()[:500],
        )
        return False
    return True


def trip_and_stop(
    decision: StopDecision, *, on_stop_signal: Callable[[], None] | None = None
) -> None:
    """The full deterministic halt: OTEL notification → local stop → stop command.

    `on_stop_signal` (e.g. an asyncio.Event.set) is invoked before the stop
    command so in-process loops unwind even though `run_autonomic_stop` may kill
    the process. No LLM is involved.
    """
    from practice_theory_implementation.observability import emit_autonomic_event

    err = decision.error
    notification = (
        f"AUTONOMIC HALT: {err.provider} {err.kind.value} — running autonomic-stop. "
        f"{decision.reason}"
    )
    with contextlib.suppress(Exception):
        emit_autonomic_event(
            name="autonomic.halt",
            notification=notification,
            attributes={
                "practice.halt.kind": err.kind.value,
                "practice.halt.provider": err.provider,
                "practice.halt.reason": decision.reason,
                "practice.halt.retry_at": err.retry_at,
                "practice.halt.consecutive": decision.consecutive,
            },
        )
    logger.error("%s", notification)
    # Escalate-when-unsure: the loop is going DOWN — tap the human now (CRITICAL).
    with contextlib.suppress(Exception):
        from practice_theory_implementation.escalation import Severity, emit_escalation

        emit_escalation(
            kind="autonomic_halt",
            severity=Severity.CRITICAL,
            source="circuit_breaker",
            dedup_key=f"autonomic_halt:{err.provider}:{err.kind.value}",
            content=(
                f"The autonomic loop halted: {err.provider} {err.kind.value}. "
                f"{decision.reason}"
            ),
            evidence={
                "kind": err.kind.value,
                "provider": err.provider,
                "reason": decision.reason,
                "retry_at": err.retry_at,
                "consecutive": decision.consecutive,
            },
        )
    # Persist the cooldown BEFORE the stop command (which may kill this process)
    # so a supervisor restart honours the back-off instead of re-dispatching at
    # once and re-tripping — the in-memory breaker alone cannot survive that.
    record_halt_cooldown(decision)
    if on_stop_signal is not None:
        with contextlib.suppress(Exception):
            on_stop_signal()
    run_autonomic_stop(decision.reason)


def observe_dispatch(
    breaker: CircuitBreaker | None,
    last_error: ModelError | None,
    *,
    on_stop_signal: Callable[[], None] | None = None,
) -> bool:
    """Feed one dispatch's outcome to the breaker; halt if it trips.

    `last_error` is the adapter's `last_error` (None = success → resets the
    breaker's consecutive counters). Returns True when the loop should stop.
    """
    if breaker is None:
        return False
    decision = breaker.record_error(last_error)
    if decision is None:
        return False
    trip_and_stop(decision, on_stop_signal=on_stop_signal)
    return True
