"""Read-only market data materials for stock investing."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from urllib.parse import quote

import httpx

DEFAULT_MARKET_SYMBOLS = (
    "SPY",
    "QQQ",
    "IWM",
    "DIA",
    "TLT",
    "SHY",
    "UUP",
    "^VIX",
    "XLK",
    "XLF",
    "XLE",
    "XLU",
    "XLV",
    "XLP",
    "XLY",
    "XLI",
    "XLB",
    "XLRE",
    "XLC",
)


def _symbol_list(symbols: object) -> list[str]:
    if not isinstance(symbols, list) or not symbols:
        return list(DEFAULT_MARKET_SYMBOLS)
    out: list[str] = []
    for symbol in symbols:
        if isinstance(symbol, str) and symbol.strip():
            out.append(symbol.strip().upper())
    return out or list(DEFAULT_MARKET_SYMBOLS)


def _num(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    return None


def _pct_change(current: float | None, previous: float | None) -> float | None:
    if current is None or previous in (None, 0):
        return None
    return round(((current - previous) / previous) * 100.0, 4)


def _iso_from_epoch(value: object) -> str | None:
    if not isinstance(value, int | float):
        return None
    return datetime.fromtimestamp(value, UTC).isoformat(timespec="seconds")


def _chart_url(symbol: str, *, range_: str, interval: str) -> str:
    encoded = quote(symbol, safe="")
    return (
        f"https://query1.finance.yahoo.com/v8/finance/chart/{encoded}"
        f"?range={quote(range_)}&interval={quote(interval)}"
    )


def _chart_snapshot(
    client: httpx.Client,
    symbol: str,
    *,
    range_: str,
    interval: str,
) -> dict[str, Any]:
    url = _chart_url(symbol, range_=range_, interval=interval)
    response = client.get(url)
    response.raise_for_status()
    chart = response.json().get("chart", {})
    error = chart.get("error")
    if error:
        return {"symbol": symbol, "error": error, "source_url": url}
    result = (chart.get("result") or [{}])[0]
    meta = result.get("meta") or {}
    timestamps = result.get("timestamp") or []
    quote_data = ((result.get("indicators") or {}).get("quote") or [{}])[0]
    closes = quote_data.get("close") or []
    points: list[dict[str, Any]] = []
    for ts, close in zip(timestamps, closes, strict=False):
        value = _num(close)
        if value is None:
            continue
        points.append(
            {
                "as_of": _iso_from_epoch(ts),
                "close": value,
            }
        )
    price = _num(meta.get("regularMarketPrice"))
    previous_close = _num(meta.get("chartPreviousClose"))
    if previous_close is None and len(points) >= 2:
        previous_close = _num(points[-2].get("close"))
    return {
        "symbol": str(meta.get("symbol") or symbol).upper(),
        "short_name": meta.get("longName") or meta.get("shortName"),
        "quote_type": meta.get("instrumentType"),
        "currency": meta.get("currency"),
        "exchange": meta.get("fullExchangeName") or meta.get("exchangeName"),
        "market_state": meta.get("marketState"),
        "price": price,
        "previous_close": previous_close,
        "day_change_pct": _pct_change(price, previous_close),
        "fifty_two_week_high": _num(meta.get("fiftyTwoWeekHigh")),
        "fifty_two_week_low": _num(meta.get("fiftyTwoWeekLow")),
        "regular_market_time": _iso_from_epoch(meta.get("regularMarketTime")),
        "source": "Yahoo Finance public chart endpoint",
        "source_url": url,
        "points": points[-10:],
    }


def market_fetch_snapshot(
    symbols: list[str] | None = None,
    *,
    range: str = "1mo",  # noqa: A002 - schema-facing name
    interval: str = "1d",
    include_history: bool = True,
    timeout_seconds: float = 10.0,
) -> dict[str, Any]:
    """Fetch a near-live read-only market snapshot for investment analysis.

    Data is read from Yahoo Finance public endpoints. It is suitable as evidence
    for the stock-investor practice, but it is not a trading execution feed.
    """
    clean_symbols = _symbol_list(symbols)
    retrieved_at = datetime.now(UTC).isoformat(timespec="seconds")
    with httpx.Client(
        timeout=timeout_seconds,
        headers={"User-Agent": "practice-theory-stock-investor/0.1"},
    ) as client:
        quotes: list[dict[str, Any]] = []
        history: dict[str, Any] = {}
        for symbol in clean_symbols:
            try:
                snapshot = _chart_snapshot(
                    client,
                    symbol,
                    range_=range,
                    interval=interval,
                )
                points = snapshot.pop("points", [])
                quotes.append(snapshot)
                if include_history:
                    history[symbol] = {
                        "source_url": snapshot.get("source_url"),
                        "points": points,
                    }
            except Exception as exc:  # keep the whole snapshot useful
                source_url = _chart_url(symbol, range_=range, interval=interval)
                quotes.append({"symbol": symbol, "error": str(exc), "source_url": source_url})
                if include_history:
                    history[symbol] = {"error": str(exc), "source_url": source_url}
    return {
        "retrieved_at": retrieved_at,
        "provider": "Yahoo Finance public chart endpoint",
        "symbols": clean_symbols,
        "quotes": quotes,
        "history_range": range if include_history else None,
        "history_interval": interval if include_history else None,
        "history": history,
        "limitations": [
            "Public finance endpoint data can be delayed, revised, or temporarily unavailable.",
            "Use for fund evidence and market interpretation only, not execution.",
            "The practitioner must preserve source timestamps and record gaps rather than invent missing data.",
        ],
    }
