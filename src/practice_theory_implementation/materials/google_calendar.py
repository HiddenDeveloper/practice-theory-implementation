"""Google Calendar materials for Calendar Stewardship.

The deterministic Calendar mock remains the default staged/issue surface for
the verify harness. This module adds live Calendar access using the same OAuth
client and account-label convention as the Gmail materials.
"""

from __future__ import annotations

import argparse
import os
from datetime import UTC, date, datetime, time
from pathlib import Path
from typing import Any, cast
from urllib.parse import quote

import httpx
from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore[import-untyped]

CALENDAR_API_BASE = "https://www.googleapis.com/calendar/v3"
CALENDAR_SCOPES = ["https://www.googleapis.com/auth/calendar.events"]
TOKEN_CACHE_DIR = Path(
    os.environ.get("PRACTICE_GOOGLE_TOKEN_CACHE_DIR")
    or os.environ.get("PRACTICE_GMAIL_TOKEN_CACHE_DIR")
    or Path.home() / ".practice-projection" / "google-tokens"
)
OAUTH_LOCAL_PORT = int(os.environ.get("PRACTICE_GOOGLE_OAUTH_PORT", "8000"))
_HTTP_TIMEOUT = 60.0


def calendar_user_list_events(
    start_date: str,
    end_date: str,
    calendar_id: str = "primary",
    max_results: int | None = None,
    single_events: bool = True,
) -> dict[str, Any]:
    return _safe_calendar_call(
        "user",
        _calendar_list_events,
        start_date=start_date,
        end_date=end_date,
        calendar_id=calendar_id,
        max_results=max_results,
        single_events=single_events,
    )


def calendar_user_create_event(
    summary: str,
    start_datetime: str | None = None,
    end_datetime: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    calendar_id: str = "primary",
    description: str | None = None,
    location: str | None = None,
    attendees: list[str] | None = None,
    time_zone: str | None = None,
    send_updates: str = "none",
    transparency: str | None = None,
    visibility: str | None = None,
) -> dict[str, Any]:
    return _safe_calendar_call(
        "user",
        _calendar_create_event,
        summary=summary,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        start_date=start_date,
        end_date=end_date,
        calendar_id=calendar_id,
        description=description,
        location=location,
        attendees=attendees,
        time_zone=time_zone,
        send_updates=send_updates,
        transparency=transparency,
        visibility=visibility,
    )


def calendar_user_patch_event(
    event_id: str,
    summary: str | None = None,
    start_datetime: str | None = None,
    end_datetime: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    calendar_id: str = "primary",
    description: str | None = None,
    location: str | None = None,
    attendees: list[str] | None = None,
    time_zone: str | None = None,
    send_updates: str = "none",
    transparency: str | None = None,
    visibility: str | None = None,
) -> dict[str, Any]:
    return _safe_calendar_call(
        "user",
        _calendar_patch_event,
        event_id=event_id,
        summary=summary,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        start_date=start_date,
        end_date=end_date,
        calendar_id=calendar_id,
        description=description,
        location=location,
        attendees=attendees,
        time_zone=time_zone,
        send_updates=send_updates,
        transparency=transparency,
        visibility=visibility,
    )


def calendar_user_delete_event(
    event_id: str,
    calendar_id: str = "primary",
    send_updates: str = "none",
) -> dict[str, Any]:
    return _safe_calendar_call(
        "user",
        _calendar_delete_event,
        event_id=event_id,
        calendar_id=calendar_id,
        send_updates=send_updates,
    )


def calendar_user_respond_event(
    event_id: str,
    attendee_email: str,
    response_status: str,
    calendar_id: str = "primary",
    send_updates: str = "none",
) -> dict[str, Any]:
    return _safe_calendar_call(
        "user",
        _calendar_respond_event,
        event_id=event_id,
        attendee_email=attendee_email,
        response_status=response_status,
        calendar_id=calendar_id,
        send_updates=send_updates,
    )


def calendar_test_list_events(
    start_date: str,
    end_date: str,
    calendar_id: str = "primary",
    max_results: int | None = None,
    single_events: bool = True,
) -> dict[str, Any]:
    return _safe_calendar_call(
        "test",
        _calendar_list_events,
        start_date=start_date,
        end_date=end_date,
        calendar_id=calendar_id,
        max_results=max_results,
        single_events=single_events,
    )


def calendar_test_create_event(
    summary: str,
    start_datetime: str | None = None,
    end_datetime: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    calendar_id: str = "primary",
    description: str | None = None,
    location: str | None = None,
    attendees: list[str] | None = None,
    time_zone: str | None = None,
    send_updates: str = "none",
    transparency: str | None = None,
    visibility: str | None = None,
) -> dict[str, Any]:
    return _safe_calendar_call(
        "test",
        _calendar_create_event,
        summary=summary,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        start_date=start_date,
        end_date=end_date,
        calendar_id=calendar_id,
        description=description,
        location=location,
        attendees=attendees,
        time_zone=time_zone,
        send_updates=send_updates,
        transparency=transparency,
        visibility=visibility,
    )


def calendar_test_patch_event(
    event_id: str,
    summary: str | None = None,
    start_datetime: str | None = None,
    end_datetime: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    calendar_id: str = "primary",
    description: str | None = None,
    location: str | None = None,
    attendees: list[str] | None = None,
    time_zone: str | None = None,
    send_updates: str = "none",
    transparency: str | None = None,
    visibility: str | None = None,
) -> dict[str, Any]:
    return _safe_calendar_call(
        "test",
        _calendar_patch_event,
        event_id=event_id,
        summary=summary,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        start_date=start_date,
        end_date=end_date,
        calendar_id=calendar_id,
        description=description,
        location=location,
        attendees=attendees,
        time_zone=time_zone,
        send_updates=send_updates,
        transparency=transparency,
        visibility=visibility,
    )


def calendar_test_delete_event(
    event_id: str,
    calendar_id: str = "primary",
    send_updates: str = "none",
) -> dict[str, Any]:
    return _safe_calendar_call(
        "test",
        _calendar_delete_event,
        event_id=event_id,
        calendar_id=calendar_id,
        send_updates=send_updates,
    )


def calendar_test_respond_event(
    event_id: str,
    attendee_email: str,
    response_status: str,
    calendar_id: str = "primary",
    send_updates: str = "none",
) -> dict[str, Any]:
    return _safe_calendar_call(
        "test",
        _calendar_respond_event,
        event_id=event_id,
        attendee_email=attendee_email,
        response_status=response_status,
        calendar_id=calendar_id,
        send_updates=send_updates,
    )


def run_calendar_oauth(
    account: str = "user", login_hint: str | None = None, prompt_consent: bool = False
) -> dict[str, Any]:
    """Run Calendar OAuth and cache credentials for one account label."""
    label = _account_label(account)
    creds = _get_credentials(label, login_hint=login_hint, prompt_consent=prompt_consent)
    return {
        "cached": True,
        "account": account,
        "label": label,
        "cache_path": str(_token_cache_path(label)),
        "scopes": list(creds.scopes or CALENDAR_SCOPES),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run Google Calendar OAuth and cache credentials for a practice account label."
    )
    parser.add_argument("--account", choices=["user", "test"], default="user")
    parser.add_argument("--login-hint")
    parser.add_argument("--prompt-consent", action="store_true")
    args = parser.parse_args()
    result = run_calendar_oauth(
        account=args.account, login_hint=args.login_hint, prompt_consent=args.prompt_consent
    )
    print(
        "OK: cached Google Calendar credentials for "
        f"{result['account']} label {result['label']} at {result['cache_path']}"
    )


def _account_label(scope: str) -> str:
    if scope == "test":
        return os.environ.get("PRACTICE_GMAIL_TEST_ACCOUNT", "Mindy")
    return os.environ.get("PRACTICE_GMAIL_USER_ACCOUNT", "voyaging")


def _safe_calendar_call(scope: str, operation: Any, **kwargs: Any) -> dict[str, Any]:
    label = _account_label(scope)
    try:
        return operation(label, **kwargs)
    except httpx.HTTPStatusError as exc:
        return {
            "error": "google_api_error",
            "status_code": exc.response.status_code,
            "body": exc.response.text,
            "account": label,
        }
    except (GoogleAuthError, RuntimeError, OSError, ValueError) as exc:
        return {"error": "google_auth_error", "message": str(exc), "account": label}


def _client_config() -> dict[str, Any]:
    client_id = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise RuntimeError(
            "Set GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET before "
            "using Google Calendar materials."
        )
    return {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [f"http://localhost:{OAUTH_LOCAL_PORT}/"],
        }
    }


def _token_cache_path(account: str) -> Path:
    return TOKEN_CACHE_DIR / f"calendar-{account}.json"


def _get_credentials(
    account: str, login_hint: str | None = None, prompt_consent: bool = False
) -> Credentials:
    cache_file = _token_cache_path(account)
    creds: Credentials | None = None
    if cache_file.exists():
        creds = cast(
            Credentials, Credentials.from_authorized_user_file(str(cache_file), CALENDAR_SCOPES)
        )
        if not set(CALENDAR_SCOPES).issubset(set(creds.scopes or [])):
            creds = None
    if creds and creds.valid:
        return creds
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(GoogleRequest())  # type: ignore[no-untyped-call]
    else:
        flow = InstalledAppFlow.from_client_config(_client_config(), CALENDAR_SCOPES)
        kwargs: dict[str, Any] = {"port": OAUTH_LOCAL_PORT, "open_browser": True}
        if login_hint:
            kwargs["login_hint"] = login_hint
        if prompt_consent:
            kwargs["prompt"] = "consent"
        creds = cast(Credentials, flow.run_local_server(**kwargs))
    TOKEN_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(creds.to_json(), encoding="utf-8")
    return creds


def _calendar_list_events(
    account: str,
    *,
    start_date: str,
    end_date: str,
    calendar_id: str = "primary",
    max_results: int | None = None,
    single_events: bool = True,
) -> dict[str, Any]:
    creds = _get_credentials(account)
    time_min = _rfc3339_start(start_date)
    time_max = _rfc3339_end(end_date)
    params: dict[str, Any] = {
        "timeMin": time_min,
        "timeMax": time_max,
        "singleEvents": str(single_events).lower(),
        "orderBy": "startTime" if single_events else None,
    }
    if max_results:
        params["maxResults"] = max_results
    result = _google_api(
        creds,
        "GET",
        f"{CALENDAR_API_BASE}/calendars/{quote(calendar_id, safe='')}/events",
        params={k: v for k, v in params.items() if v is not None},
    )
    items = result.get("items", [])
    return {
        "account": account,
        "calendar_id": calendar_id,
        "time_min": time_min,
        "time_max": time_max,
        "events": [_summarize_event(event) for event in items],
        "nextPageToken": result.get("nextPageToken"),
        "nextSyncToken": result.get("nextSyncToken"),
    }


def _calendar_create_event(
    account: str,
    *,
    summary: str,
    start_datetime: str | None = None,
    end_datetime: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    calendar_id: str = "primary",
    description: str | None = None,
    location: str | None = None,
    attendees: list[str] | None = None,
    time_zone: str | None = None,
    send_updates: str = "none",
    transparency: str | None = None,
    visibility: str | None = None,
) -> dict[str, Any]:
    creds = _get_credentials(account)
    payload = _event_payload(
        summary=summary,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        start_date=start_date,
        end_date=end_date,
        description=description,
        location=location,
        attendees=attendees,
        time_zone=time_zone,
        transparency=transparency,
        visibility=visibility,
        require_time=True,
    )
    result = _google_api(
        creds,
        "POST",
        f"{CALENDAR_API_BASE}/calendars/{quote(calendar_id, safe='')}/events",
        params={"sendUpdates": _validate_send_updates(send_updates)},
        json_body=payload,
    )
    return {
        "account": account,
        "calendar_id": calendar_id,
        "send_updates": send_updates,
        "event": _summarize_event(result),
    }


def _calendar_patch_event(
    account: str,
    *,
    event_id: str,
    summary: str | None = None,
    start_datetime: str | None = None,
    end_datetime: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    calendar_id: str = "primary",
    description: str | None = None,
    location: str | None = None,
    attendees: list[str] | None = None,
    time_zone: str | None = None,
    send_updates: str = "none",
    transparency: str | None = None,
    visibility: str | None = None,
) -> dict[str, Any]:
    creds = _get_credentials(account)
    payload = _event_payload(
        summary=summary,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        start_date=start_date,
        end_date=end_date,
        description=description,
        location=location,
        attendees=attendees,
        time_zone=time_zone,
        transparency=transparency,
        visibility=visibility,
        require_time=False,
    )
    if not payload:
        raise ValueError("calendar patch requires at least one field to update")
    result = _google_api(
        creds,
        "PATCH",
        f"{CALENDAR_API_BASE}/calendars/{quote(calendar_id, safe='')}/events/"
        f"{quote(event_id, safe='')}",
        params={"sendUpdates": _validate_send_updates(send_updates)},
        json_body=payload,
    )
    return {
        "account": account,
        "calendar_id": calendar_id,
        "event_id": event_id,
        "send_updates": send_updates,
        "event": _summarize_event(result),
    }


def _calendar_delete_event(
    account: str,
    *,
    event_id: str,
    calendar_id: str = "primary",
    send_updates: str = "none",
) -> dict[str, Any]:
    creds = _get_credentials(account)
    result = _google_api(
        creds,
        "DELETE",
        f"{CALENDAR_API_BASE}/calendars/{quote(calendar_id, safe='')}/events/"
        f"{quote(event_id, safe='')}",
        params={"sendUpdates": _validate_send_updates(send_updates)},
    )
    return {
        "account": account,
        "calendar_id": calendar_id,
        "event_id": event_id,
        "deleted": True,
        "send_updates": send_updates,
        "api_result": result,
    }


def _calendar_respond_event(
    account: str,
    *,
    event_id: str,
    attendee_email: str,
    response_status: str,
    calendar_id: str = "primary",
    send_updates: str = "none",
) -> dict[str, Any]:
    creds = _get_credentials(account)
    event_url = (
        f"{CALENDAR_API_BASE}/calendars/{quote(calendar_id, safe='')}/events/"
        f"{quote(event_id, safe='')}"
    )
    event = _google_api(creds, "GET", event_url)
    attendees = event.get("attendees") or []
    target = attendee_email.lower()
    updated_attendees = []
    seen = False
    for attendee in attendees:
        if str(attendee.get("email", "")).lower() == target:
            attendee = {
                **attendee,
                "responseStatus": _validate_response_status(response_status),
            }
            seen = True
        updated_attendees.append(attendee)
    if not seen:
        updated_attendees.append(
            {
                "email": attendee_email,
                "responseStatus": _validate_response_status(response_status),
            }
        )
    result = _google_api(
        creds,
        "PATCH",
        event_url,
        params={"sendUpdates": _validate_send_updates(send_updates)},
        json_body={"attendees": updated_attendees},
    )
    return {
        "account": account,
        "calendar_id": calendar_id,
        "event_id": event_id,
        "attendee_email": attendee_email,
        "response_status": response_status,
        "send_updates": send_updates,
        "event": _summarize_event(result),
    }


def _google_api(
    creds: Credentials,
    method: str,
    url: str,
    *,
    params: dict[str, Any] | None = None,
    json_body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    with httpx.Client(timeout=_HTTP_TIMEOUT) as client:
        response = client.request(
            method,
            url,
            params=params,
            json=json_body,
            headers={"Authorization": f"Bearer {creds.token}"},
        )
        response.raise_for_status()
        if not response.content:
            return {}
        return cast(dict[str, Any], response.json())


def _rfc3339_start(value: str) -> str:
    return datetime.combine(date.fromisoformat(value), time.min, tzinfo=UTC).isoformat()


def _rfc3339_end(value: str) -> str:
    return datetime.combine(date.fromisoformat(value), time.max, tzinfo=UTC).isoformat()


def _summarize_event(event: dict[str, Any]) -> dict[str, Any]:
    attendees = event.get("attendees") or []
    organizer_email = (event.get("organizer") or {}).get("email")
    organizer_domain = _email_domain(organizer_email)
    return {
        "id": event.get("id"),
        "summary": event.get("summary"),
        "description": event.get("description"),
        "location": event.get("location"),
        "status": event.get("status"),
        "htmlLink": event.get("htmlLink"),
        "start": event.get("start"),
        "end": event.get("end"),
        "organizer": event.get("organizer"),
        "creator": event.get("creator"),
        "attendee_count": len(attendees),
        "has_external_attendees": any(
            _is_external_attendee(attendee, organizer_domain) for attendee in attendees
        ),
        "attendees": [
            {
                "email": attendee.get("email"),
                "displayName": attendee.get("displayName"),
                "responseStatus": attendee.get("responseStatus"),
                "optional": attendee.get("optional"),
                "organizer": attendee.get("organizer"),
            }
            for attendee in attendees
        ],
    }


def _event_payload(
    *,
    summary: str | None = None,
    start_datetime: str | None = None,
    end_datetime: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    description: str | None = None,
    location: str | None = None,
    attendees: list[str] | None = None,
    time_zone: str | None = None,
    transparency: str | None = None,
    visibility: str | None = None,
    require_time: bool,
) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if summary is not None:
        payload["summary"] = summary
    if description is not None:
        payload["description"] = description
    if location is not None:
        payload["location"] = location
    if attendees is not None:
        payload["attendees"] = [{"email": email} for email in attendees]
    if transparency is not None:
        payload["transparency"] = _validate_choice(
            "transparency", transparency, {"opaque", "transparent"}
        )
    if visibility is not None:
        payload["visibility"] = _validate_choice(
            "visibility", visibility, {"default", "public", "private", "confidential"}
        )

    uses_datetime = start_datetime is not None or end_datetime is not None
    uses_date = start_date is not None or end_date is not None
    if uses_datetime and uses_date:
        raise ValueError("use either start_datetime/end_datetime or start_date/end_date, not both")
    if uses_datetime:
        if not start_datetime or not end_datetime:
            raise ValueError("timed events require both start_datetime and end_datetime")
        payload["start"] = _event_time("dateTime", start_datetime, time_zone)
        payload["end"] = _event_time("dateTime", end_datetime, time_zone)
    elif uses_date:
        if not start_date or not end_date:
            raise ValueError("all-day events require both start_date and end_date")
        payload["start"] = {"date": start_date}
        payload["end"] = {"date": end_date}
    elif require_time:
        raise ValueError(
            "calendar event creation requires either start_datetime/end_datetime "
            "or start_date/end_date"
        )
    return payload


def _event_time(kind: str, value: str, time_zone: str | None) -> dict[str, str]:
    item = {kind: value}
    if time_zone:
        item["timeZone"] = time_zone
    return item


def _validate_send_updates(value: str) -> str:
    return _validate_choice("send_updates", value, {"all", "externalOnly", "none"})


def _validate_response_status(value: str) -> str:
    return _validate_choice(
        "response_status", value, {"accepted", "declined", "needsAction", "tentative"}
    )


def _validate_choice(name: str, value: str, allowed: set[str]) -> str:
    if value not in allowed:
        allowed_text = ", ".join(sorted(allowed))
        raise ValueError(f"{name} must be one of: {allowed_text}")
    return value


def _is_external_attendee(attendee: dict[str, Any], organizer_domain: str | None) -> bool:
    attendee_domain = _email_domain(attendee.get("email"))
    return bool(organizer_domain and attendee_domain and attendee_domain != organizer_domain)


def _email_domain(email: str | None) -> str | None:
    if not email or "@" not in email:
        return None
    return email.rsplit("@", 1)[1].lower()
