"""Tests for the env-first → setec secret provider (Phase 1a)."""

from __future__ import annotations

import base64
from typing import Any

import pytest

from practice_theory_implementation import secret_provider
from practice_theory_implementation.secret_provider import SETEC_URL_ENV, get_secret


@pytest.fixture(autouse=True)
def clean_state(monkeypatch: pytest.MonkeyPatch) -> None:
    """Each test starts with no setec configured and an empty cache."""
    monkeypatch.delenv(SETEC_URL_ENV, raising=False)
    secret_provider.clear_cache()


def _b64(value: str) -> str:
    return base64.b64encode(value.encode()).decode()


class _Resp:
    def __init__(self, status_code: int, value: str | None = None) -> None:
        self.status_code = status_code
        self._value = value

    def json(self) -> dict[str, Any]:
        return {"Value": _b64(self._value), "Version": 1} if self._value is not None else {}


def test_env_hit_returns_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PRACTICE_LINE_TOKEN", "from-env")
    assert get_secret("PRACTICE_LINE_TOKEN") == "from-env"


def test_env_hit_via_alias(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PRACTICE_LINE_TOKEN", raising=False)
    monkeypatch.setenv("LINE_CHANNEL_ACCESS_TOKEN", "shared")
    assert get_secret("PRACTICE_LINE_TOKEN", aliases=("LINE_CHANNEL_ACCESS_TOKEN",)) == "shared"


def test_both_unset_returns_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NOPE", raising=False)
    assert get_secret("NOPE") is None
    assert get_secret("NOPE", default="fallback") == "fallback"


def test_setec_hit_when_env_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SOME_KEY", raising=False)
    monkeypatch.setenv(SETEC_URL_ENV, "https://setec.tailnet.ts.net")
    calls: list[dict[str, Any]] = []

    def _post(url: str, headers: dict, json: dict, timeout: float) -> _Resp:
        calls.append({"url": url, "headers": headers, "json": json})
        return _Resp(200, "from-setec")

    import httpx

    monkeypatch.setattr(httpx, "post", _post)
    assert get_secret("SOME_KEY") == "from-setec"
    assert calls[0]["url"] == "https://setec.tailnet.ts.net/api/get"
    assert calls[0]["headers"]["Sec-X-Tailscale-No-Browsers"] == "setec"
    assert calls[0]["json"] == {"Name": "SOME_KEY", "Version": 0}


def test_env_beats_setec(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KEY", "env-wins")
    monkeypatch.setenv(SETEC_URL_ENV, "https://setec.tailnet.ts.net")

    def _post(*args: Any, **kwargs: Any) -> _Resp:  # pragma: no cover - must not run
        raise AssertionError("setec should not be consulted when env is set")

    import httpx

    monkeypatch.setattr(httpx, "post", _post)
    assert get_secret("KEY") == "env-wins"


def test_setec_via_alias_name(monkeypatch: pytest.MonkeyPatch) -> None:
    # Stored in setec under the project-wide name, requested under the canonical.
    monkeypatch.setenv(SETEC_URL_ENV, "https://setec.tailnet.ts.net")

    def _post(url: str, headers: dict, json: dict, timeout: float) -> _Resp:
        if json["Name"] == "LINE_CHANNEL_ACCESS_TOKEN":
            return _Resp(200, "tok")
        return _Resp(404)

    import httpx

    monkeypatch.setattr(httpx, "post", _post)
    assert get_secret("PRACTICE_LINE_TOKEN", aliases=("LINE_CHANNEL_ACCESS_TOKEN",)) == "tok"


def test_setec_not_found_falls_through_to_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(SETEC_URL_ENV, "https://setec.tailnet.ts.net")
    import httpx

    monkeypatch.setattr(httpx, "post", lambda *a, **kw: _Resp(404))
    assert get_secret("MISSING", default="d") == "d"


def test_setec_error_is_best_effort(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(SETEC_URL_ENV, "https://setec.tailnet.ts.net")

    def _boom(*args: Any, **kwargs: Any) -> _Resp:
        raise RuntimeError("unreachable")

    import httpx

    monkeypatch.setattr(httpx, "post", _boom)
    assert get_secret("KEY", default="safe") == "safe"


def test_setec_value_is_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(SETEC_URL_ENV, "https://setec.tailnet.ts.net")
    count = {"n": 0}

    def _post(*args: Any, **kwargs: Any) -> _Resp:
        count["n"] += 1
        return _Resp(200, "cached-val")

    import httpx

    monkeypatch.setattr(httpx, "post", _post)
    assert get_secret("KEY") == "cached-val"
    assert get_secret("KEY") == "cached-val"
    assert count["n"] == 1  # second call served from cache


def test_setec_miss_is_not_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    # A secret added to setec mid-run is picked up without restart.
    monkeypatch.setenv(SETEC_URL_ENV, "https://setec.tailnet.ts.net")
    state = {"present": False}

    def _post(*args: Any, **kwargs: Any) -> _Resp:
        return _Resp(200, "now-here") if state["present"] else _Resp(404)

    import httpx

    monkeypatch.setattr(httpx, "post", _post)
    assert get_secret("LATER") is None
    state["present"] = True
    assert get_secret("LATER") == "now-here"
