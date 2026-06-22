"""Secret provider — env-first, then Tailscale `setec`.

The narrow runtime config layer the secrets plan mandates: a long-lived
credential is resolved *here*, at the process edge that needs it, and never via
an LLM-facing tool or material. Resolution order for each lookup:

  1. process environment (``name`` then ``aliases``) — local dev + today's path
  2. a `setec` server, if ``PRACTICE_SETEC_URL`` is set (tries the same names)
  3. the supplied ``default`` (``None``)

So nothing changes while env vars are still set; as setec comes up the same call
transparently starts resolving from it, and a credential can be dropped from the
``.env`` once its setec path is verified.

Best-effort by construction: any setec error (unconfigured, unreachable, not
found, bad payload) falls through rather than raising, and secret *values* are
never logged. See docs/plans/setec-secrets-setup.md.
"""

from __future__ import annotations

import base64
import logging
import os
import threading

logger = logging.getLogger(__name__)

SETEC_URL_ENV = "PRACTICE_SETEC_URL"
# setec refuses requests that look browser-driven; every call to its API must
# carry this header (setec docs/api.md).
_SETEC_HEADERS = {"Sec-X-Tailscale-No-Browsers": "setec"}
_SETEC_TIMEOUT = 5.0

# Cache only the expensive path: successful setec fetches, keyed by secret name.
# Env reads stay live (cheap, and an exported var must always win); misses are
# not cached so a secret added to setec mid-run is picked up without a restart.
_setec_cache: dict[str, str] = {}
_cache_lock = threading.Lock()


def _from_env(names: tuple[str, ...]) -> str | None:
    for name in names:
        value = os.environ.get(name, "").strip()
        if value:
            return value
    return None


def _from_setec(name: str) -> str | None:
    """Fetch one secret's active version from the configured setec server.

    Returns the decoded value, or ``None`` for any failure/absence. Never raises,
    never logs the value."""
    base = os.environ.get(SETEC_URL_ENV, "").strip()
    if not base:
        return None
    with _cache_lock:
        cached = _setec_cache.get(name)
    if cached is not None:
        return cached
    try:
        import httpx

        resp = httpx.post(
            f"{base.rstrip('/')}/api/get",
            headers=_SETEC_HEADERS,
            json={"Name": name, "Version": 0},
            timeout=_SETEC_TIMEOUT,
        )
        if resp.status_code == 404:
            return None
        if resp.status_code != 200:
            logger.warning("[secret_provider] setec get %s -> HTTP %s", name, resp.status_code)
            return None
        encoded = resp.json().get("Value")
        if not isinstance(encoded, str):
            return None
        value = base64.b64decode(encoded).decode("utf-8")
    except Exception:
        # Transient (network, DNS, decode): fall through, do not cache.
        logger.warning("[secret_provider] setec fetch failed for %s", name, exc_info=True)
        return None
    with _cache_lock:
        _setec_cache[name] = value
    return value


def get_secret(
    name: str, *, aliases: tuple[str, ...] = (), default: str | None = None
) -> str | None:
    """Resolve a secret: env (``name`` + ``aliases``) → setec → ``default``.

    ``aliases`` are extra names checked after ``name`` in both env and setec, so a
    credential stored under a project-wide convention (e.g.
    ``LINE_CHANNEL_ACCESS_TOKEN``) is found when requested under the canonical
    name (``PRACTICE_LINE_TOKEN``)."""
    names = (name, *aliases)
    env_value = _from_env(names)
    if env_value is not None:
        return env_value
    if os.environ.get(SETEC_URL_ENV, "").strip():
        for candidate in names:
            value = _from_setec(candidate)
            if value is not None:
                return value
    return default


def clear_cache() -> None:
    """Drop the in-process setec cache — for tests and after a rotation."""
    with _cache_lock:
        _setec_cache.clear()
