"""Escalate-when-unsure: the loop's tap-on-the-shoulder to the human.

Phase 1: surface the silent terminal states. The autonomic loop self-corrects
within bounds; this records an `Escalation` when those bounds are *hit* — it
gave up, it broke — and pushes the CRITICAL ones to the human's phone over LINE.
Quiet by default: one open escalation per `dedup_key`, never a stream; non-
critical severities are recorded for the dashboard/digest (later phases) and do
not push.

The whole module is best-effort: an escalation must never crash the loop it is
reporting on. Every public entry point swallows its own errors.

LINE config (env, like the other service creds): `PRACTICE_LINE_TOKEN` (channel
access token) + `PRACTICE_LINE_TO` (target user/group id). Unset → recorded but
not pushed (the mechanism is built; flip the creds on to go live).
"""

from __future__ import annotations

import contextlib
import logging
import os
from enum import StrEnum

from practice_theory_implementation.trail import EnactmentStore, EscalationRow

logger = logging.getLogger(__name__)

LINE_TOKEN_ENV = "PRACTICE_LINE_TOKEN"
LINE_TO_ENV = "PRACTICE_LINE_TO"
LINE_PUSH_URL = "https://api.line.me/v2/bot/message/push"


class Severity(StrEnum):
    CRITICAL = "critical"   # "it stopped" — push now, any hour
    ATTENTION = "attention"  # "I gave up / I'm unsure" — coalesce / digest
    FYI = "fyi"             # "for the record" — dashboard only, never pushes


def notify_line(text: str) -> bool:
    """Push one text message to the configured LINE target. Best-effort.

    Returns True only if the message was actually delivered. Unconfigured or
    failed pushes return False (the escalation stays recorded + un-notified, so a
    later pass / the dashboard still surfaces it)."""
    token = os.environ.get(LINE_TOKEN_ENV, "").strip()
    to = os.environ.get(LINE_TO_ENV, "").strip()
    if not token or not to:
        logger.info("[escalation] LINE not configured; recorded, not pushed")
        return False
    try:
        import httpx

        resp = httpx.post(
            LINE_PUSH_URL,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={"to": to, "messages": [{"type": "text", "text": text[:4900]}]},
            timeout=10.0,
        )
        resp.raise_for_status()
        return True
    except Exception:
        logger.exception("[escalation] LINE push failed")
        return False


def _format(row: EscalationRow) -> str:
    return f"⚠️ [{row.severity.upper()}] {row.kind}\n{row.content}"


def emit_escalation(
    *,
    kind: str,
    severity: str,
    source: str,
    dedup_key: str,
    content: str,
    evidence: object | None = None,
    store: EnactmentStore | None = None,
) -> int | None:
    """Record an escalation (idempotent on dedup_key) and, if CRITICAL, push it
    to LINE immediately — "it stopped" can't wait for a digest pass.

    Best-effort: returns the escalation id, or None if recording itself failed.
    Never raises — the loop being reported on must not be taken down by its own
    alarm."""
    owns_store = store is None
    s: EnactmentStore | None = None
    try:
        s = store or EnactmentStore()
        eid = s.record_escalation(
            kind=kind,
            severity=severity,
            source=source,
            dedup_key=dedup_key,
            content=content,
            evidence=evidence,
        )
        if severity == Severity.CRITICAL:
            row = next((r for r in s.open_escalations(limit=100) if r.id == eid), None)
            if row is not None and row.notified_at is None and notify_line(_format(row)):
                s.mark_escalation_notified(eid)
        return eid
    except Exception:
        logger.exception("[escalation] emit failed (non-fatal)")
        return None
    finally:
        if owns_store and s is not None:
            with contextlib.suppress(Exception):
                s.close()


def dispatch_unnotified(
    store: EnactmentStore, *, severities: tuple[str, ...] = (Severity.CRITICAL,)
) -> int:
    """Push any un-notified escalations of the given severities over LINE.

    Phase-1 policy is minimal: CRITICAL only (the rest wait for the digest loop
    in a later phase). Returns the number actually pushed."""
    pushed = 0
    for row in store.unnotified_escalations(limit=100):
        if row.severity not in severities:
            continue
        if notify_line(_format(row)):
            store.mark_escalation_notified(row.id)
            pushed += 1
    return pushed
