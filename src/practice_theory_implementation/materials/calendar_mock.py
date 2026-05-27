"""Calendar Stewardship mock materials — a Google-Calendar-shaped mock.

Holds a small in-process event store seeded with two canned events. Each
material accepts arguments shaped like the real Google Calendar API and
returns shapes that mirror it. The side effects that would happen against
the real API — notifications to attendees — are *printed* with a
`[CALENDAR MOCK]` prefix instead of leaving the process. The print is the
demonstration: the saved harm made visible.

This separates capture from execution as Step 1 named: the Calendar
Stewardship bundle does not change when these materials are swapped for a
real Google Calendar binding; only the prints would stop.
"""

from __future__ import annotations

import sys
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

# Seed a few events so the bundle has something to act on.
_today = datetime.now(UTC).replace(hour=14, minute=0, second=0, microsecond=0)

_EVENTS: dict[str, dict[str, Any]] = {
    "evt-customer-review": {
        "id": "evt-customer-review",
        "summary": "Customer review with Acme",
        "start": (_today + timedelta(days=2)).isoformat(),
        "end": (_today + timedelta(days=2, hours=1)).isoformat(),
        "attendees": [
            {"email": "alice@acme.example", "external": True},
            {"email": "bob@acme.example", "external": True},
            {"email": "carol@us.example", "external": False},
        ],
        "organizer": "monyet@us.example",
    },
    "evt-internal-standup": {
        "id": "evt-internal-standup",
        "summary": "Team standup",
        "start": (_today + timedelta(days=1)).isoformat(),
        "end": (_today + timedelta(days=1, minutes=15)).isoformat(),
        "attendees": [
            {"email": "dave@us.example", "external": False},
            {"email": "eve@us.example", "external": False},
        ],
        "organizer": "monyet@us.example",
    },
}

# Staged changes pending issue. staging_id -> {event_id, new_start, new_end, reason}.
_STAGED: dict[str, dict[str, Any]] = {}

# Stance requests recorded for the user's review (the act of asking, made visible).
_STANCE_REQUESTS: list[dict[str, Any]] = []


def _log(line: str) -> None:
    print(f"[CALENDAR MOCK] {line}", file=sys.stderr)


def cal_list_events(start_date: str, end_date: str) -> list[dict[str, Any]]:
    """Return upcoming events in the requested range.

    Date filtering is loose in the mock — returns everything seeded. The
    interface mirrors what a real Calendar list would expose: enough for the
    LLM to decide which event a reschedule applies to.
    """
    _ = (start_date, end_date)
    return [
        {
            "id": e["id"],
            "summary": e["summary"],
            "start": e["start"],
            "end": e["end"],
            "attendee_count": len(e["attendees"]),
            "has_external_attendees": any(a["external"] for a in e["attendees"]),
        }
        for e in _EVENTS.values()
    ]


def cal_propose_reschedule(
    event_id: str, new_start: str, new_end: str, reason: str
) -> dict[str, Any]:
    """Stage a reschedule — no attendees notified.

    Mirrors `update_event(send_updates='none')` on the real API: the change
    is recorded as a staging the user can review, but no calendar invites
    have moved and no notifications have been sent.
    """
    if event_id not in _EVENTS:
        return {"error": f"unknown event {event_id!r}"}
    staging_id = f"stg-{uuid.uuid4().hex[:8]}"
    _STAGED[staging_id] = {
        "event_id": event_id,
        "new_start": new_start,
        "new_end": new_end,
        "reason": reason,
    }
    event = _EVENTS[event_id]
    _log(
        f"STAGED reschedule of '{event['summary']}' "
        f"({event['start']} -> {new_start}); "
        f"send_updates='none' (0 attendees notified)"
    )
    return {
        "staging_id": staging_id,
        "event_id": event_id,
        "old_start": event["start"],
        "new_start": new_start,
        "send_updates": "none",
        "notified": [],
    }


def cal_invite_stance(question: str, options: list[str]) -> dict[str, Any]:
    """Record a question for the user — no commitment made on their behalf."""
    request = {
        "id": f"stance-{uuid.uuid4().hex[:8]}",
        "question": question,
        "options": options,
        "asked_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    _STANCE_REQUESTS.append(request)
    _log(f"STANCE REQUESTED: {question!r}; options={options}")
    return request


def cal_issue_reschedule(staging_id: str) -> dict[str, Any]:
    """Convert a staged reschedule into an issued change — notifications fly.

    Mirrors `update_event(send_updates='all')` on the real API. The mock
    prints `WOULD NOTIFY` with the attendee list rather than actually
    sending invites; the print is the demonstration of what is irreversibly
    on the wire once this is called for real.
    """
    if staging_id not in _STAGED:
        return {
            "error": (
                f"no staged change {staging_id!r}; "
                "issue requires a prior propose_reschedule on the same event"
            )
        }
    staged = _STAGED.pop(staging_id)
    event = _EVENTS[staged["event_id"]]
    notified = [a["email"] for a in event["attendees"]]
    event["start"] = staged["new_start"]
    event["end"] = staged["new_end"]
    _log(
        f"ISSUED reschedule of '{event['summary']}'; "
        f"send_updates='all'; WOULD NOTIFY: {notified}"
    )
    return {
        "event_id": event["id"],
        "new_start": event["start"],
        "send_updates": "all",
        "notified": notified,
    }
