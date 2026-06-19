"""Morning-briefing materials."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx
import yaml

DEFAULT_BROWSER_JIT_URL = "http://127.0.0.1:3019"
DEFAULT_SITE_LIST_PATH = "config/morning_briefing_sites.yaml"
MAX_SNAPSHOT_CHARS = 12_000


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _valid_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _tool_url(base_url: str, tool_name: str) -> str:
    return f"{base_url.rstrip('/')}/tools/{tool_name}"


def _post_tool(
    client: httpx.Client,
    base_url: str,
    tool_name: str,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    response = client.post(_tool_url(base_url, tool_name), json=arguments)
    response.raise_for_status()
    result = response.json()
    if isinstance(result, dict):
        return result
    return {"result": result}


def _content_text(result: dict[str, Any]) -> str:
    content = result.get("content")
    if not isinstance(content, list):
        return ""
    chunks: list[str] = []
    for block in content:
        if isinstance(block, dict) and block.get("type") == "text":
            text = block.get("text")
            if isinstance(text, str):
                chunks.append(text)
    return "\n".join(chunks)


def _headline_lines(text: str, limit: int) -> list[str]:
    lines: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith(("#", "-", "*")):
            line = line.lstrip("#-* ").strip()
        if line and line not in lines:
            lines.append(line[:240])
        if len(lines) >= limit:
            break
    return lines


def _site_from_raw(raw: object) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    site_id = raw.get("id")
    name = raw.get("name")
    url = raw.get("url")
    if not isinstance(site_id, str) or not site_id.strip():
        return None
    if not isinstance(name, str) or not name.strip():
        return None
    if not isinstance(url, str) or not _valid_url(url):
        return None
    enabled = raw.get("enabled", True)
    return {
        "id": site_id.strip(),
        "name": name.strip(),
        "url": url.strip(),
        "enabled": enabled if isinstance(enabled, bool) else True,
        "cadence": raw.get("cadence") if isinstance(raw.get("cadence"), str) else None,
        "section": raw.get("section") if isinstance(raw.get("section"), str) else None,
        "notes": raw.get("notes") if isinstance(raw.get("notes"), str) else None,
    }


def read_morning_briefing_sites(
    config_path: str = DEFAULT_SITE_LIST_PATH,
    include_disabled: bool = False,
) -> dict[str, Any]:
    """Read the local morning briefing site list from YAML."""
    path = Path(config_path).expanduser()
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except FileNotFoundError:
        return {
            "config_path": str(path),
            "sites": [],
            "count": 0,
            "access_gap": "morning briefing site list file not found",
        }
    except Exception as exc:
        return {
            "config_path": str(path),
            "sites": [],
            "count": 0,
            "access_gap": f"could not read morning briefing site list: {exc}",
        }

    raw_sites = payload.get("sites") if isinstance(payload, dict) else None
    if not isinstance(raw_sites, list):
        return {
            "config_path": str(path),
            "sites": [],
            "count": 0,
            "access_gap": "morning briefing site list has no `sites` array",
        }

    invalid_count = 0
    sites: list[dict[str, Any]] = []
    for raw in raw_sites:
        site = _site_from_raw(raw)
        if site is None:
            invalid_count += 1
            continue
        if site["enabled"] or include_disabled:
            sites.append(site)

    result: dict[str, Any] = {
        "config_path": str(path),
        "sites": sites,
        "count": len(sites),
        "invalid_count": invalid_count,
    }
    if invalid_count:
        result["source_notes"] = [
            f"{invalid_count} site entries were skipped because id, name, or "
            "valid http(s) URL was missing."
        ]
    return result


def morning_briefing_browser_site_check(
    site_name: str,
    url: str,
    checked_at: str | None = None,
    browser_jit_url: str = DEFAULT_BROWSER_JIT_URL,
    timeout_seconds: float = 90.0,
    headline_limit: int = 12,
) -> dict[str, Any]:
    """Check one recurring morning site through Cognabot's browser JIT proxy.

    The proxy is expected to be the host-native Cognabot JIT URL, which starts
    the browser Compose service on first request and forwards to the browser MCP
    bridge. Failures are returned as access gaps so the briefing can stay honest.
    """
    checked = checked_at or _now()
    if not _valid_url(url):
        return {
            "site_name": site_name,
            "url": url,
            "checked_at": checked,
            "access_gap": "invalid URL; expected http(s) URL with host",
            "provider": "Cognabot browser JIT",
        }

    base_url = browser_jit_url.rstrip("/")
    cleanup_warning: str | None = None
    try:
        with httpx.Client(timeout=timeout_seconds) as client:
            _post_tool(
                client,
                base_url,
                "new_page",
                {"url": url, "timeout": int(timeout_seconds * 1000)},
            )
            snapshot = _post_tool(client, base_url, "take_snapshot", {})
            try:
                _post_tool(client, base_url, "close_page", {})
            except Exception as exc:  # best-effort cleanup; do not hide the read.
                cleanup_warning = str(exc)
    except Exception as exc:
        return {
            "site_name": site_name,
            "url": url,
            "checked_at": checked,
            "access_gap": (
                "Cognabot browser JIT check failed; ensure `bun run jit:browser` "
                f"is running in apprenticeship-cognabot and Docker can start the browser: {exc}"
            ),
            "provider": "Cognabot browser JIT",
            "browser_jit_url": base_url,
        }

    snapshot_text = _content_text(snapshot)
    truncated = len(snapshot_text) > MAX_SNAPSHOT_CHARS
    source_notes = [
        "Read via Cognabot browser JIT proxy",
        "Snapshot is the browser accessibility-tree text returned by chrome-devtools-mcp",
    ]
    if cleanup_warning:
        source_notes.append(f"Page cleanup warning: {cleanup_warning}")
    return {
        "site_name": site_name,
        "url": url,
        "checked_at": checked,
        "provider": "Cognabot browser JIT",
        "browser_jit_url": base_url,
        "headline_items": _headline_lines(snapshot_text, max(1, min(headline_limit, 50))),
        "source_notes": source_notes,
        "snapshot_text": (
            snapshot_text[:MAX_SNAPSHOT_CHARS] if truncated else snapshot_text
        ),
        "snapshot_truncated": truncated,
    }
