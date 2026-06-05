"""Autonomic-loop status dashboard: gather live counts, render self-contained HTML.

A read-only visual surface over the trail — Judge inbox, Smoother inbox, open
enactments (with age), and unaddressed Frictions. The counts reuse
`read_system_observability`; the open-enactment ages are read here so each row
can be surfaced individually (an enactment open far longer than any dispatch
runs is the leak signal). The HTML is fully self-contained (inline CSS, no
external assets) so it can be served by a bare HTTP handler or written to a file.
"""

from __future__ import annotations

import html as _html
from datetime import UTC, datetime
from typing import Any

from practice_theory_implementation.materials.operational_observability import (
    read_system_observability,
)
from practice_theory_implementation.trail import EnactmentStore

# An open enactment older than this is almost certainly stranded: no dispatch
# runs anywhere near this long, so it reads as a leak, not live work.
STALE_OPEN_ENACTMENT_SECONDS = 15 * 60
WARN_OPEN_ENACTMENT_SECONDS = 5 * 60


def _humanize_age(seconds: float) -> str:
    s = int(max(0, seconds))
    if s < 60:
        return f"{s}s"
    if s < 3600:
        return f"{s // 60}m {s % 60}s"
    if s < 86400:
        return f"{s // 3600}h {(s % 3600) // 60}m"
    return f"{s // 86400}d {(s % 86400) // 3600}h"


def gather_dashboard_status() -> dict[str, Any]:
    """Live snapshot: the four headline counts plus per-open-enactment ages."""
    obs = read_system_observability(limit=1)
    counts = obs["trail"]["counts"]

    store = EnactmentStore()
    try:
        with store._cursor() as cur:
            cur.execute(
                "SELECT id, practice_id, mode, opened_at FROM enactments "
                "WHERE closed_at IS NULL ORDER BY opened_at"
            )
            open_rows = [dict(r) for r in cur.fetchall()]
    finally:
        store.close()

    now = datetime.now(UTC)
    open_enactments: list[dict[str, Any]] = []
    for row in open_rows:
        try:
            age = (now - datetime.fromisoformat(row["opened_at"])).total_seconds()
        except (ValueError, TypeError):
            age = 0.0
        severity = (
            "stale"
            if age >= STALE_OPEN_ENACTMENT_SECONDS
            else "warn"
            if age >= WARN_OPEN_ENACTMENT_SECONDS
            else "ok"
        )
        open_enactments.append(
            {
                "id": row["id"],
                "practice_id": row["practice_id"],
                "mode": row["mode"],
                "opened_at": row["opened_at"],
                "age_seconds": age,
                "age_human": _humanize_age(age),
                "severity": severity,
            }
        )

    return {
        "judge_inbox": int(counts.get("pending_judge_inbox", 0)),
        "smoother_inbox": int(counts.get("pending_smoother_inbox", 0)),
        "open_enactment_count": int(counts.get("open_enactments", 0)),
        "unaddressed_friction": int(counts.get("unaddressed_friction", 0)),
        "open_enactments": open_enactments,
        "generated_at": now.isoformat(timespec="seconds"),
    }


def _metric_severity(count: int, *, warn_at: int = 1) -> str:
    return "ok" if count == 0 else "warn" if count < warn_at + 9 else "stale"


def _metric_card(label: str, value: int, severity: str, sub: str) -> str:
    return (
        f'<div class="card {severity}">'
        f'<div class="value">{value}</div>'
        f'<div class="label">{_html.escape(label)}</div>'
        f'<div class="sub">{_html.escape(sub)}</div>'
        f"</div>"
    )


def render_status_dashboard(
    refresh_seconds: int = 10, write_path: str | None = None
) -> dict[str, Any]:
    """Affordance: render the live status dashboard to an HTML file.

    Reads the trail, writes a self-contained HTML snapshot (default
    `data/status.html`), and returns the path, the live-server URL hint, and the
    headline counts. Read-only over the trail; writes only the HTML artifact.
    """
    import os
    from pathlib import Path

    status = gather_dashboard_status()
    html_doc = render_dashboard_html(status, refresh_seconds=refresh_seconds)
    path = Path(write_path) if write_path else Path("data") / "status.html"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html_doc, encoding="utf-8")

    port = os.environ.get("PRACTICE_DASHBOARD_PORT", "7182")
    return {
        "path": str(path),
        "live_url": f"http://127.0.0.1:{port}/",
        "judge_inbox": status["judge_inbox"],
        "smoother_inbox": status["smoother_inbox"],
        "open_enactment_count": status["open_enactment_count"],
        "unaddressed_friction": status["unaddressed_friction"],
        "generated_at": status["generated_at"],
    }


# Inline CSS shared by the full-page renderer and the embeddable fragment. Kept
# as a plain string (single braces) so it can be dropped into an f-string via a
# variable without brace-escaping.
_DASHBOARD_CSS = """
  :root {
    --bg:#0d1117; --panel:#161b22; --line:#21262d; --text:#e6edf3;
    --muted:#7d8590; --ok:#2ea043; --warn:#d29922; --stale:#f85149;
  }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--bg); color:var(--text);
    font:15px/1.5 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; }
  .wrap { max-width:920px; margin:0 auto; padding:32px 20px; }
  header { display:flex; align-items:baseline; justify-content:space-between;
    border-bottom:1px solid var(--line); padding-bottom:14px; margin-bottom:24px; }
  h1 { font-size:19px; margin:0; letter-spacing:.3px; }
  .meta { color:var(--muted); font-size:12px; }
  .dot { display:inline-block; width:7px; height:7px; border-radius:50%;
    background:var(--ok); margin-right:6px; vertical-align:middle;
    animation:pulse 2s infinite; }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.35} }
  .cards { display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin-bottom:28px; }
  .card { background:var(--panel); border:1px solid var(--line);
    border-radius:10px; padding:18px 16px; border-top:3px solid var(--line); }
  .card .value { font-size:40px; font-weight:600; line-height:1; }
  .card .label { color:var(--text); font-size:13px; margin-top:8px; }
  .card .sub { color:var(--muted); font-size:11px; margin-top:2px; }
  .card.ok { border-top-color:var(--ok); }
  .card.warn { border-top-color:var(--warn); }
  .card.warn .value { color:var(--warn); }
  .card.stale { border-top-color:var(--stale); }
  .card.stale .value { color:var(--stale); }
  h2 { font-size:13px; color:var(--muted); text-transform:uppercase;
    letter-spacing:1px; margin:0 0 10px; }
  table { width:100%; border-collapse:collapse; background:var(--panel);
    border:1px solid var(--line); border-radius:10px; overflow:hidden; }
  th,td { text-align:left; padding:9px 14px; border-bottom:1px solid var(--line); }
  th { color:var(--muted); font-weight:500; font-size:12px; }
  tr:last-child td { border-bottom:none; }
  td.mono { color:var(--muted); }
  td.age { text-align:right; }
  tr.warn td.age { color:var(--warn); }
  tr.stale td.age { color:var(--stale); font-weight:600; }
  .empty { background:var(--panel); border:1px solid var(--line); border-radius:10px;
    padding:22px; text-align:center; color:var(--ok); }
  @media (max-width:640px) { .cards { grid-template-columns:repeat(2,1fr); } }
"""


def _dashboard_body(status: dict[str, Any], *, refresh_note: str) -> str:
    """The styled `.wrap` content (header + cards + table), shared by both renders."""
    j = status["judge_inbox"]
    sm = status["smoother_inbox"]
    oe = status["open_enactment_count"]
    fr = status["unaddressed_friction"]
    rows = status["open_enactments"]

    cards = "".join(
        [
            _metric_card("Judge inbox", j, _metric_severity(j), "pending"),
            _metric_card("Smoother inbox", sm, _metric_severity(sm), "pending"),
            _metric_card(
                "Open enactments",
                oe,
                "ok"
                if oe == 0
                else ("stale" if any(r["severity"] == "stale" for r in rows) else "warn"),
                "in flight / leaked",
            ),
            _metric_card("Unaddressed frictions", fr, _metric_severity(fr), "open"),
        ]
    )

    if rows:
        body_rows = "".join(
            f'<tr class="{r["severity"]}">'
            f'<td class="mono">{_html.escape(r["id"][:8])}</td>'
            f"<td>{_html.escape(r['practice_id'])}</td>"
            f"<td>{_html.escape(r['mode'])}</td>"
            f'<td class="age">{_html.escape(r["age_human"])}</td>'
            f"</tr>"
            for r in rows
        )
        table = (
            "<table><thead><tr><th>id</th><th>bundle</th><th>mode</th>"
            f"<th>age</th></tr></thead><tbody>{body_rows}</tbody></table>"
        )
    else:
        table = '<div class="empty">No open enactments — clean.</div>'

    generated = _html.escape(status["generated_at"])
    count_note = f" ({len(rows)})" if rows else ""
    return (
        f'<div class="wrap"><header><h1>Autonomic loop status</h1>'
        f'<div class="meta"><span class="dot"></span>updated {generated} '
        f"&middot; {_html.escape(refresh_note)}</div></header>"
        f'<div class="cards">{cards}</div>'
        f"<h2>Open enactments{count_note}</h2>{table}</div>"
    )


def render_dashboard_fragment(status: dict[str, Any]) -> str:
    """Embeddable fragment (inline `<style>` + content), no document wrapper and
    no meta-refresh — for hosting inside the MCP Apps shell, which owns the
    refresh lifecycle. See `visualizations`."""
    return f"<style>{_DASHBOARD_CSS}</style>\n{_dashboard_body(status, refresh_note='live')}"


def render_dashboard_html(status: dict[str, Any], *, refresh_seconds: int = 10) -> str:
    """Render the snapshot as a self-contained HTML page (inline CSS, meta-refresh)."""
    body = _dashboard_body(status, refresh_note=f"auto-refresh {int(refresh_seconds)}s")
    return (
        '<!doctype html>\n<html lang="en">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f'<meta http-equiv="refresh" content="{int(refresh_seconds)}">\n'
        "<title>Autonomic loop status</title>\n"
        f"<style>{_DASHBOARD_CSS}</style>\n</head>\n<body>\n{body}\n</body>\n</html>"
    )
