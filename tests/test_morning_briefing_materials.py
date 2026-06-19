from __future__ import annotations

from typing import Any

from practice_theory_implementation.materials import morning_briefing


class _FakeResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return self.payload


class _FakeClient:
    def __init__(self, calls: list[tuple[str, dict[str, Any]]]) -> None:
        self.calls = calls

    def __enter__(self) -> _FakeClient:
        return self

    def __exit__(self, *_exc: object) -> None:
        return None

    def post(self, url: str, json: dict[str, Any]) -> _FakeResponse:
        self.calls.append((url, json))
        if url.endswith("/tools/take_snapshot"):
            return _FakeResponse(
                {
                    "content": [
                        {
                            "type": "text",
                            "text": "First headline\n\n- Second headline\n# Third headline",
                        }
                    ]
                }
            )
        return _FakeResponse({"content": [{"type": "text", "text": "ok"}]})


def test_browser_site_check_rejects_invalid_url() -> None:
    result = morning_briefing.morning_briefing_browser_site_check(
        "Example", "not-a-url", checked_at="2026-06-19T00:00:00+00:00"
    )

    assert result["access_gap"] == "invalid URL; expected http(s) URL with host"
    assert result["provider"] == "Cognabot browser JIT"


def test_browser_site_check_uses_cognabot_jit_proxy(monkeypatch) -> None:
    calls: list[tuple[str, dict[str, Any]]] = []
    fake_client = _FakeClient(calls)
    monkeypatch.setattr(morning_briefing.httpx, "Client", lambda timeout: fake_client)

    result = morning_briefing.morning_briefing_browser_site_check(
        "Example",
        "https://example.test/news",
        checked_at="2026-06-19T00:00:00+00:00",
        browser_jit_url="http://127.0.0.1:3019/",
        headline_limit=2,
    )

    assert [url for url, _payload in calls] == [
        "http://127.0.0.1:3019/tools/new_page",
        "http://127.0.0.1:3019/tools/take_snapshot",
        "http://127.0.0.1:3019/tools/close_page",
    ]
    assert calls[0][1] == {"url": "https://example.test/news", "timeout": 90000}
    assert result["headline_items"] == ["First headline", "Second headline"]
    assert result["snapshot_text"] == "First headline\n\n- Second headline\n# Third headline"
    assert result["snapshot_truncated"] is False


def test_read_morning_briefing_sites_reads_enabled_sites(tmp_path) -> None:
    config = tmp_path / "sites.yaml"
    config.write_text(
        """
sites:
  - id: guardian_uk
    name: Guardian UK
    url: https://www.theguardian.com/uk
    enabled: true
    cadence: daily
    section: news
    notes: UK homepage
  - id: disabled
    name: Disabled
    url: https://example.test
    enabled: false
  - id: broken
    name: Broken
    url: not-a-url
""",
        encoding="utf-8",
    )

    result = morning_briefing.read_morning_briefing_sites(str(config))

    assert result["count"] == 1
    assert result["invalid_count"] == 1
    assert result["sites"] == [
        {
            "id": "guardian_uk",
            "name": "Guardian UK",
            "url": "https://www.theguardian.com/uk",
            "enabled": True,
            "cadence": "daily",
            "section": "news",
            "notes": "UK homepage",
        }
    ]


def test_read_morning_briefing_sites_can_include_disabled(tmp_path) -> None:
    config = tmp_path / "sites.yaml"
    config.write_text(
        """
sites:
  - id: guardian_uk
    name: Guardian UK
    url: https://www.theguardian.com/uk
    enabled: false
""",
        encoding="utf-8",
    )

    result = morning_briefing.read_morning_briefing_sites(
        str(config), include_disabled=True
    )

    assert result["count"] == 1
    assert result["sites"][0]["enabled"] is False
