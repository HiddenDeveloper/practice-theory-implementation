from __future__ import annotations

from typing import Any

from practice_theory_implementation.materials import market_data


class _FakeResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return

    def json(self) -> dict[str, Any]:
        return self._payload


class _FakeClient:
    urls: list[str] = []

    def __init__(self, **_: object) -> None:
        self.urls = _FakeClient.urls

    def __enter__(self) -> _FakeClient:
        return self

    def __exit__(self, *_args: object) -> None:
        return

    def get(self, url: str) -> _FakeResponse:
        self.urls.append(url)
        return _FakeResponse(
            {
                "chart": {
                    "result": [
                        {
                            "meta": {
                                "symbol": "SPY",
                                "longName": "SPDR S&P 500 ETF Trust",
                                "instrumentType": "ETF",
                                "currency": "USD",
                                "regularMarketPrice": 750.0,
                                "chartPreviousClose": 735.0,
                                "regularMarketTime": 1781690400,
                                "marketState": "REGULAR",
                            },
                            "timestamp": [1781517600, 1781604000, 1781690400],
                            "indicators": {
                                "quote": [{"close": [730.0, 735.0, 750.0]}]
                            },
                        }
                    ]
                }
            }
        )


def test_market_fetch_snapshot_reads_quotes_and_history(
    monkeypatch,
) -> None:
    _FakeClient.urls = []
    monkeypatch.setattr(market_data.httpx, "Client", _FakeClient)

    result = market_data.market_fetch_snapshot(
        symbols=["SPY"],
        range="5d",
        interval="1d",
    )

    assert result["provider"] == "Yahoo Finance public chart endpoint"
    assert result["symbols"] == ["SPY"]
    assert result["quotes"][0]["symbol"] == "SPY"
    assert result["quotes"][0]["price"] == 750.0
    assert result["quotes"][0]["day_change_pct"] == 2.0408
    assert result["quotes"][0]["source_url"].startswith(
        "https://query1.finance.yahoo.com/v8/finance/chart/SPY"
    )
    assert result["history"]["SPY"]["points"][-1]["close"] == 750.0
    assert len(_FakeClient.urls) == 1
