"""Gmail materials for Correspondent.

The substrate owns the practice framing; this module owns the concrete Gmail
surface. Account labels resolve to OAuth token cache files under
``~/.practice-projection/google-tokens/`` by default so this implementation can
reuse the older projection project's cached tokens. The labels are env-driven
so the substrate can say "user mailbox" or "test mailbox" without embedding an
address or credential identity in a public file.
"""

from __future__ import annotations

import argparse
import base64
import os
from email.message import EmailMessage
from pathlib import Path
from typing import Any, cast

import httpx
from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore[import-untyped]

GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1"
GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
]
TOKEN_CACHE_DIR = Path(
    os.environ.get("PRACTICE_GMAIL_TOKEN_CACHE_DIR")
    or Path.home() / ".practice-projection" / "google-tokens"
)
OAUTH_LOCAL_PORT = 8000
_HTTP_TIMEOUT = 60.0


def gmail_user_search_threads(
    query: str | None = None,
    max_results: int | None = None,
    page_token: str | None = None,
    include_spam_trash: bool = False,
) -> dict[str, Any]:
    return _safe_gmail_call(
        "user",
        _gmail_search_threads,
        query=query,
        max_results=max_results,
        page_token=page_token,
        include_spam_trash=include_spam_trash,
    )


def gmail_user_get_thread(thread_id: str, format: str = "full") -> dict[str, Any]:
    return _safe_gmail_call("user", _gmail_get_thread, thread_id=thread_id, format=format)


def gmail_user_list_drafts(
    query: str | None = None,
    max_results: int | None = None,
    page_token: str | None = None,
) -> dict[str, Any]:
    return _safe_gmail_call(
        "user", _gmail_list_drafts, query=query, max_results=max_results, page_token=page_token
    )


def gmail_user_create_draft(
    to: list[str],
    subject: str,
    body: str,
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    reply_to_thread_id: str | None = None,
    reply_to_message_id: str | None = None,
) -> dict[str, Any]:
    return _safe_gmail_call(
        "user",
        _gmail_create_draft,
        to=to,
        subject=subject,
        body=body,
        cc=cc,
        bcc=bcc,
        reply_to_thread_id=reply_to_thread_id,
        reply_to_message_id=reply_to_message_id,
    )


def gmail_user_update_draft(
    draft_id: str,
    to: list[str],
    subject: str,
    body: str,
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    reply_to_thread_id: str | None = None,
    reply_to_message_id: str | None = None,
) -> dict[str, Any]:
    return _safe_gmail_call(
        "user",
        _gmail_update_draft,
        draft_id=draft_id,
        to=to,
        subject=subject,
        body=body,
        cc=cc,
        bcc=bcc,
        reply_to_thread_id=reply_to_thread_id,
        reply_to_message_id=reply_to_message_id,
    )


def gmail_user_delete_draft(draft_id: str) -> dict[str, Any]:
    return _safe_gmail_call("user", _gmail_delete_draft, draft_id=draft_id)


def gmail_user_send_draft(draft_id: str) -> dict[str, Any]:
    return _safe_gmail_call("user", _gmail_send_draft, draft_id=draft_id)


def gmail_test_search_threads(
    query: str | None = None,
    max_results: int | None = None,
    page_token: str | None = None,
    include_spam_trash: bool = False,
) -> dict[str, Any]:
    return _safe_gmail_call(
        "test",
        _gmail_search_threads,
        query=query,
        max_results=max_results,
        page_token=page_token,
        include_spam_trash=include_spam_trash,
    )


def gmail_test_get_thread(thread_id: str, format: str = "full") -> dict[str, Any]:
    return _safe_gmail_call("test", _gmail_get_thread, thread_id=thread_id, format=format)


def gmail_test_list_drafts(
    query: str | None = None,
    max_results: int | None = None,
    page_token: str | None = None,
) -> dict[str, Any]:
    return _safe_gmail_call(
        "test", _gmail_list_drafts, query=query, max_results=max_results, page_token=page_token
    )


def gmail_test_create_draft(
    to: list[str],
    subject: str,
    body: str,
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    reply_to_thread_id: str | None = None,
    reply_to_message_id: str | None = None,
) -> dict[str, Any]:
    return _safe_gmail_call(
        "test",
        _gmail_create_draft,
        to=to,
        subject=subject,
        body=body,
        cc=cc,
        bcc=bcc,
        reply_to_thread_id=reply_to_thread_id,
        reply_to_message_id=reply_to_message_id,
    )


def gmail_test_update_draft(
    draft_id: str,
    to: list[str],
    subject: str,
    body: str,
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    reply_to_thread_id: str | None = None,
    reply_to_message_id: str | None = None,
) -> dict[str, Any]:
    return _safe_gmail_call(
        "test",
        _gmail_update_draft,
        draft_id=draft_id,
        to=to,
        subject=subject,
        body=body,
        cc=cc,
        bcc=bcc,
        reply_to_thread_id=reply_to_thread_id,
        reply_to_message_id=reply_to_message_id,
    )


def gmail_test_delete_draft(draft_id: str) -> dict[str, Any]:
    return _safe_gmail_call("test", _gmail_delete_draft, draft_id=draft_id)


def gmail_test_send_draft(draft_id: str) -> dict[str, Any]:
    return _safe_gmail_call("test", _gmail_send_draft, draft_id=draft_id)


def run_gmail_oauth(account: str = "user", login_hint: str | None = None) -> dict[str, Any]:
    """Run the Gmail OAuth dance and cache credentials for one account label."""
    label = _account_label(account)
    creds = _get_credentials(label, login_hint=login_hint)
    return {
        "cached": True,
        "account": account,
        "label": label,
        "cache_path": str(_token_cache_path(label)),
        "scopes": list(creds.scopes or GMAIL_SCOPES),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run Gmail OAuth and cache credentials for a practice mailbox label."
    )
    parser.add_argument("--account", choices=["user", "test"], default="user")
    parser.add_argument("--login-hint")
    args = parser.parse_args()
    result = run_gmail_oauth(account=args.account, login_hint=args.login_hint)
    print(
        "OK: cached Gmail credentials for "
        f"{result['account']} label {result['label']} at {result['cache_path']}"
    )


def _account_label(scope: str) -> str:
    if scope == "test":
        return os.environ.get("PRACTICE_GMAIL_TEST_ACCOUNT", "Mindy")
    return os.environ.get("PRACTICE_GMAIL_USER_ACCOUNT", "voyaging")


def _safe_gmail_call(scope: str, operation: Any, **kwargs: Any) -> dict[str, Any]:
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
    except (GoogleAuthError, RuntimeError, OSError) as exc:
        return {"error": "google_auth_error", "message": str(exc), "account": label}


def _client_config() -> dict[str, Any]:
    client_id = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise RuntimeError(
            "Set GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET before "
            "using Gmail materials."
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
    return TOKEN_CACHE_DIR / f"gmail-{account}.json"


def _get_credentials(account: str, login_hint: str | None = None) -> Credentials:
    cache_file = _token_cache_path(account)
    creds: Credentials | None = None
    if cache_file.exists():
        creds = cast(
            Credentials, Credentials.from_authorized_user_file(str(cache_file), GMAIL_SCOPES)
        )
    if creds and creds.valid:
        return creds
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(GoogleRequest())  # type: ignore[no-untyped-call]
    else:
        flow = InstalledAppFlow.from_client_config(_client_config(), GMAIL_SCOPES)
        kwargs: dict[str, Any] = {"port": OAUTH_LOCAL_PORT, "open_browser": True}
        if login_hint:
            kwargs["login_hint"] = login_hint
        creds = cast(Credentials, flow.run_local_server(**kwargs))
    TOKEN_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(creds.to_json(), encoding="utf-8")
    return creds


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
            headers={
                "Authorization": f"Bearer {creds.token}",
                "Accept": "application/json",
            },
        )
        response.raise_for_status()
        if response.content:
            return cast(dict[str, Any], response.json())
        return {}


def _build_rfc822(
    *,
    to: list[str],
    subject: str,
    body: str,
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    in_reply_to: str | None = None,
) -> str:
    msg = EmailMessage()
    msg["To"] = ", ".join(to)
    if cc:
        msg["Cc"] = ", ".join(cc)
    if bcc:
        msg["Bcc"] = ", ".join(bcc)
    msg["Subject"] = subject
    if in_reply_to:
        msg["In-Reply-To"] = in_reply_to
        msg["References"] = in_reply_to
    msg.set_content(body)
    return base64.urlsafe_b64encode(msg.as_bytes()).decode("ascii")


def _resolve_in_reply_to(creds: Credentials, reply_to_message_id: str | None) -> str | None:
    if not reply_to_message_id:
        return None
    msg = _google_api(
        creds,
        "GET",
        f"{GMAIL_API_BASE}/users/me/messages/{reply_to_message_id}",
        params={"format": "metadata", "metadataHeaders": "Message-ID"},
    )
    for header in msg.get("payload", {}).get("headers", []):
        if header.get("name", "").lower() == "message-id":
            value = header.get("value")
            if isinstance(value, str):
                return value
    return None


def _gmail_search_threads(
    account: str,
    *,
    query: str | None = None,
    max_results: int | None = None,
    page_token: str | None = None,
    include_spam_trash: bool = False,
) -> dict[str, Any]:
    creds = _get_credentials(account)
    params: dict[str, Any] = {}
    if query:
        params["q"] = query
    if max_results is not None:
        params["maxResults"] = max_results
    if page_token:
        params["pageToken"] = page_token
    if include_spam_trash:
        params["includeSpamTrash"] = "true"
    return _google_api(creds, "GET", f"{GMAIL_API_BASE}/users/me/threads", params=params)


def _gmail_get_thread(account: str, *, thread_id: str, format: str = "full") -> dict[str, Any]:
    creds = _get_credentials(account)
    return _google_api(
        creds,
        "GET",
        f"{GMAIL_API_BASE}/users/me/threads/{thread_id}",
        params={"format": format},
    )


def _gmail_list_drafts(
    account: str,
    *,
    query: str | None = None,
    max_results: int | None = None,
    page_token: str | None = None,
) -> dict[str, Any]:
    creds = _get_credentials(account)
    params: dict[str, Any] = {}
    if query:
        params["q"] = query
    if max_results is not None:
        params["maxResults"] = max_results
    if page_token:
        params["pageToken"] = page_token
    return _google_api(creds, "GET", f"{GMAIL_API_BASE}/users/me/drafts", params=params)


def _gmail_create_draft(
    account: str,
    *,
    to: list[str],
    subject: str,
    body: str,
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    reply_to_thread_id: str | None = None,
    reply_to_message_id: str | None = None,
) -> dict[str, Any]:
    creds = _get_credentials(account)
    raw = _build_rfc822(
        to=to,
        subject=subject,
        body=body,
        cc=cc,
        bcc=bcc,
        in_reply_to=_resolve_in_reply_to(creds, reply_to_message_id),
    )
    payload: dict[str, Any] = {"message": {"raw": raw}}
    if reply_to_thread_id:
        payload["message"]["threadId"] = reply_to_thread_id
    return _google_api(creds, "POST", f"{GMAIL_API_BASE}/users/me/drafts", json_body=payload)


def _gmail_update_draft(
    account: str,
    *,
    draft_id: str,
    to: list[str],
    subject: str,
    body: str,
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    reply_to_thread_id: str | None = None,
    reply_to_message_id: str | None = None,
) -> dict[str, Any]:
    creds = _get_credentials(account)
    raw = _build_rfc822(
        to=to,
        subject=subject,
        body=body,
        cc=cc,
        bcc=bcc,
        in_reply_to=_resolve_in_reply_to(creds, reply_to_message_id),
    )
    payload: dict[str, Any] = {"message": {"raw": raw}}
    if reply_to_thread_id:
        payload["message"]["threadId"] = reply_to_thread_id
    return _google_api(
        creds, "PUT", f"{GMAIL_API_BASE}/users/me/drafts/{draft_id}", json_body=payload
    )


def _gmail_delete_draft(account: str, *, draft_id: str) -> dict[str, Any]:
    creds = _get_credentials(account)
    return _google_api(creds, "DELETE", f"{GMAIL_API_BASE}/users/me/drafts/{draft_id}")


def _gmail_send_draft(account: str, *, draft_id: str) -> dict[str, Any]:
    creds = _get_credentials(account)
    return _google_api(
        creds,
        "POST",
        f"{GMAIL_API_BASE}/users/me/drafts/send",
        json_body={"id": draft_id},
    )


if __name__ == "__main__":
    main()
