"""Visualization registry + the generic MCP Apps shell.

One fixed `show_visualization(name, args)` tool dispatches to a registry of named
visualizations, mirroring how `invoke_affordance` dispatches to materials: the
surface stays minimal, growth happens in the registry. MCP Apps binds UI to a
*tool* via a static `_meta.ui.resourceUri`, so there is one generic shell
resource (`ui://viz/shell.html`); the `name` selects the visualization at runtime
from the tool result the host pushes into the iframe.

Render contract: server-rendered fragments. Each visualization is a
`(args) -> html` callable returning an embeddable HTML fragment (inline styles,
no document wrapper). The shell injects it and refreshes by calling the tool back.
Adding a visualization is a registry entry — no new tool, no surface change.
"""

from __future__ import annotations

import html as _html
import logging
from collections.abc import Callable
from datetime import date, timedelta
from math import cos, floor, log, pi, radians, tan
from typing import Any

logger = logging.getLogger(__name__)

VIZ_RESOURCE_URI = "ui://viz/shell.html"
VIZ_MIME_TYPE = "text/html;profile=mcp-app"

VizRenderer = Callable[[dict[str, Any]], str]
_REGISTRY: dict[str, VizRenderer] = {}


def register_visualization(name: str, renderer: VizRenderer) -> None:
    """Bind a name to a `(args) -> html fragment` renderer."""
    _REGISTRY[name] = renderer


def list_visualizations() -> list[str]:
    return sorted(_REGISTRY)


def _error_fragment(message: str) -> str:
    return (
        '<div style="font:14px ui-monospace,Menlo,monospace;color:#f85149;'
        'padding:24px;">'
        f"{_html.escape(message)}</div>"
    )


def render_visualization(name: str, args: dict[str, Any] | None = None) -> dict[str, Any]:
    """Render the named visualization to an HTML fragment.

    Returns `{name, html, args}` on success, or `{name, error, available, args,
    html}` when the name is unknown or the renderer raises — always with a
    displayable `html` so the shell can show the problem rather than going blank.
    The args echo lets the MCP App shell re-run the same view on Refresh —
    including retrying a failed render — rather than falling back to defaults.
    """
    renderer = _REGISTRY.get(name)
    if renderer is None:
        avail = list_visualizations()
        return {
            "name": name,
            "error": f"unknown visualization {name!r}",
            "available": avail,
            "args": args or {},
            "html": _error_fragment(
                f"Unknown visualization {name!r}. Available: {', '.join(avail) or '(none)'}"
            ),
        }
    try:
        html = renderer(args or {})
    except Exception as exc:  # noqa: BLE001 — a viz error must render, not crash the tool
        logger.exception("visualization %r failed", name)
        return {
            "name": name,
            "error": f"{type(exc).__name__}: {exc}",
            "args": args or {},
            "html": _error_fragment(f"Visualization {name!r} failed: {exc}"),
        }
    return {"name": name, "html": html, "args": args or {}}


# --- the generic shell -----------------------------------------------------
# Self-contained: implements the MCP Apps ui/ postMessage handshake in vanilla
# JS, so no bundler/Node dependency. It is static — the visualization payload
# arrives via ui/notifications/tool-result and refreshes via a tools/call back.

_SHELL_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Visualization</title>
<style>
  :root { --bar-height:44px; }
  html,body { margin:0; height:100%; overflow:hidden; background:#0d1117; color:#e6edf3;
    font:14px ui-monospace,Menlo,Consolas,monospace; }
  #viz { height:calc(100vh - var(--bar-height)); overflow:auto; }
  #loading { padding:48px; text-align:center; color:#7d8590; }
  #bar { position:fixed; bottom:0; left:0; right:0; display:flex; gap:10px;
    align-items:center; box-sizing:border-box; height:var(--bar-height);
    padding:7px 14px; background:#161b22;
    border-top:1px solid #21262d; font-size:12px; color:#7d8590; }
  #bar button { background:#21262d; color:#e6edf3; border:1px solid #30363d;
    border-radius:6px; padding:4px 12px; cursor:pointer; font:inherit; }
  #bar button:hover { background:#30363d; }
  #name { color:#e6edf3; }
</style>
</head>
<body>
<div id="viz"><div id="loading">Connecting to host…</div></div>
<div id="bar">
  <button id="refresh">Refresh</button>
  <span id="name"></span><span id="status"></span>
</div>
<script>
(function () {
  var PROTOCOL = "2025-06-18";
  var pending = {}, nextId = 1, currentName = null, currentArgs = {};
  var vizEl = document.getElementById("viz");
  var nameEl = document.getElementById("name");
  var statusEl = document.getElementById("status");

  function post(m) { window.parent.postMessage(m, "*"); }
  function request(method, params) {
    var id = nextId++;
    post({ jsonrpc: "2.0", id: id, method: method, params: params || {} });
    return new Promise(function (res, rej) { pending[id] = { res: res, rej: rej }; });
  }
  function notify(method, params) {
    post({ jsonrpc: "2.0", method: method, params: params || {} });
  }

  function renderResult(result) {
    if (!result) return;
    var html = null, name = null, args = null;
    var data = result.structuredContent;
    if (data) { html = data.html; name = data.name; args = data.args; }
    if (html == null && result.content) {
      var t = result.content.filter(function (c) { return c.type === "text"; })[0];
      if (t) {
        try { var p = JSON.parse(t.text); html = p.html; name = p.name; args = p.args; }
        catch (e) { html = t.text; }
      }
    }
    if (name) { currentName = name; nameEl.textContent = name; }
    if (args && typeof args === "object") { currentArgs = args; }
    if (html != null) {
      vizEl.innerHTML = html;
      statusEl.textContent = "· updated " + new Date().toLocaleTimeString();
    }
  }

  window.addEventListener("message", function (ev) {
    var m = ev.data;
    if (!m || m.jsonrpc !== "2.0") return;
    if (m.id != null && pending[m.id]) {
      var p = pending[m.id]; delete pending[m.id];
      if (m.error) p.rej(m.error); else p.res(m.result);
      return;
    }
    if (m.method === "ui/notifications/tool-result") {
      renderResult(m.params && m.params.result ? m.params.result : m.params);
    }
  });

  function refresh() {
    statusEl.textContent = "· refreshing…";
    request("tools/call", { name: "show_visualization",
      arguments: { name: currentName || "status", args: currentArgs } })
      .then(renderResult)
      .catch(function (e) {
        statusEl.textContent = "· error: " + (e && e.message ? e.message : e);
      });
  }
  document.getElementById("refresh").addEventListener("click", refresh);

  request("ui/initialize", {
    appCapabilities: {}, protocolVersion: PROTOCOL,
    appInfo: { name: "practice-viz-shell", version: "1.0.0" }
  }).then(function () {
    notify("ui/notifications/initialized", {});
    var l = document.getElementById("loading");
    if (l) l.textContent = "Waiting for data…";
  }).catch(function (e) {
    var msg = e && e.message ? e.message : e;
    vizEl.innerHTML = '<div id="loading">Host handshake failed: ' + msg + "</div>";
  });
})();
</script>
</body>
</html>
"""


def render_viz_shell_html() -> str:
    """The static generic shell served as the `ui://viz/shell.html` resource."""
    return _SHELL_HTML


# --- built-in visualizations ----------------------------------------------


def _status_renderer(args: dict[str, Any]) -> str:
    from practice_theory_implementation.materials.status_dashboard import (
        gather_dashboard_status,
        render_dashboard_fragment,
    )

    return render_dashboard_fragment(gather_dashboard_status())


register_visualization("status", _status_renderer)

_ACTIVITY_TYPE_PRESETS: dict[str, dict[str, object]] = {
    "walking": {
        "label": "Walking",
        "aliases": {"walk", "walking", "hiking", "street_running"},
        "color": "#bf3989",
    },
    "cycling": {
        "label": "Cycling",
        "aliases": {
            "bike",
            "biking",
            "cycle",
            "cycling",
            "road_biking",
            "mountain_biking",
            "gravel_cycling",
            "indoor_cycling",
        },
        "color": "#0969da",
    },
    "strength_training": {
        "label": "Strength Training",
        "aliases": {"strength", "strength_training", "strengthtraining", "training"},
        "color": "#9a6700",
    },
    "pilates": {
        "label": "Pilates",
        "aliases": {"pilates"},
        "color": "#8250df",
    },
    "yoga": {
        "label": "Yoga",
        "aliases": {"yoga"},
        "color": "#1a7f37",
    },
}


def activity_type_keys() -> list[str]:
    """The supported activity-type preset keys, in display order.

    The material surface derives its `activity_type` enum from this, so adding
    a preset here is the only change needed to support a new type end to end.
    """
    return list(_ACTIVITY_TYPE_PRESETS)


def _coerce_route_points(value: Any) -> list[dict[str, float]]:
    points: list[dict[str, float]] = []
    if not isinstance(value, list):
        return points
    for item in value:
        if not isinstance(item, dict):
            continue
        lat = item.get("lat")
        lon = item.get("lon")
        if not isinstance(lat, int | float) or not isinstance(lon, int | float):
            continue
        points.append({"lat": float(lat), "lon": float(lon)})
    return points


def _activity_label(detail: dict[str, Any], activity_id: str) -> str:
    name = detail.get("name")
    if isinstance(name, str) and name:
        return name
    return f"Activity {activity_id}"


def _activity_when(detail: dict[str, object]) -> str | None:
    for key in ("start_time_local", "start_time_gmt", "date"):
        value = detail.get(key)
        if isinstance(value, str) and value:
            return value.replace("T", " ")
    return None


def _activity_lookup_fragment(activity_id: str, message: str) -> str:
    escaped_id = _html.escape(activity_id)
    escaped_message = _html.escape(message)
    return (
        '<section style="min-height:100%;box-sizing:border-box;padding:28px;'
        'background:#0d1117;color:#e6edf3;font:14px ui-sans-serif,system-ui;">'
        '<h1 style="margin:0 0 8px;font-size:22px;font-weight:650;">'
        f"Activity {escaped_id}</h1>"
        '<p style="margin:0 0 14px;color:#8b949e;">Garmin did not return this '
        "activity. Use an activity_id from recent_activity or activity_detail.</p>"
        '<pre style="white-space:pre-wrap;margin:0;padding:12px;background:#161b22;'
        'border:1px solid #30363d;border-radius:8px;color:#c9d1d9;">'
        f"{escaped_message}</pre></section>"
    )


def _activity_scan_fragment(start_date: str, end_date: str, examined: int) -> str:
    return (
        '<section style="min-height:100%;box-sizing:border-box;padding:28px;'
        'background:#0d1117;color:#e6edf3;font:14px ui-sans-serif,system-ui;">'
        '<h1 style="margin:0 0 8px;font-size:22px;font-weight:650;">'
        "No GPS activity found</h1>"
        f'<p style="margin:0;color:#8b949e;">Checked {examined} activities from '
        f"{_html.escape(start_date)} to {_html.escape(end_date)}, but none exposed "
        "GPS route points.</p></section>"
    )


def _activity_scan_error_fragment(start_date: str, end_date: str, message: str) -> str:
    return (
        '<section style="min-height:100%;box-sizing:border-box;padding:28px;'
        'background:#0d1117;color:#e6edf3;font:14px ui-sans-serif,system-ui;">'
        '<h1 style="margin:0 0 8px;font-size:22px;font-weight:650;">'
        "Could not list recent activities</h1>"
        f'<p style="margin:0 0 14px;color:#8b949e;">Date range: {_html.escape(start_date)} '
        f"to {_html.escape(end_date)}</p>"
        '<pre style="white-space:pre-wrap;margin:0;padding:12px;background:#161b22;'
        'border:1px solid #30363d;border-radius:8px;color:#c9d1d9;">'
        f"{_html.escape(message)}</pre></section>"
    )


def _activity_type_key(value: Any) -> str:
    return str(value or "").strip().lower().replace(" ", "_").replace("-", "_")


def _activity_type_from_args(args: dict[str, Any]) -> str | None:
    raw = args.get("activity_type") or args.get("type")
    if not isinstance(raw, str) or not raw.strip():
        return None
    key = _activity_type_key(raw)
    if key in _ACTIVITY_TYPE_PRESETS:
        return key
    for preset_key, preset in _ACTIVITY_TYPE_PRESETS.items():
        aliases = preset["aliases"]
        if isinstance(aliases, set) and key in aliases:
            return preset_key
    return key


def _activity_matches_type(activity: dict[str, object], preset_key: str) -> bool:
    preset = _ACTIVITY_TYPE_PRESETS[preset_key]
    aliases = preset["aliases"]
    activity_type = _activity_type_key(activity.get("type"))
    return isinstance(aliases, set) and activity_type in aliases


def _number_value(activity: dict[str, object], key: str) -> float | None:
    value = activity.get(key)
    if isinstance(value, int | float):
        return float(value)
    return None


def _fmt_num(value: float | None, suffix: str) -> str:
    if value is None:
        return "n/a"
    if value.is_integer():
        return f"{int(value)} {suffix}"
    return f"{value:.1f} {suffix}"


def _truthy_arg(value: Any, *, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _date_arg(args: dict[str, Any], key: str, default: date) -> date:
    value = args.get(key)
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value:
        return date.fromisoformat(value)
    return default


def _candidate_activity_id(activity: dict[str, object]) -> str | None:
    for key in ("activity_id", "garmin_id"):
        value = activity.get(key)
        if isinstance(value, str) and value:
            return value
        if isinstance(value, int):
            return str(value)
    return None


def _web_mercator_world_px(point: dict[str, float], zoom: int) -> tuple[float, float]:
    tile_size = 256
    n = 2**zoom
    lat = max(min(point["lat"], 85.05112878), -85.05112878)
    lat_rad = radians(lat)
    x = (point["lon"] + 180) / 360 * n * tile_size
    y = (1 - log(tan(lat_rad) + 1 / cos(lat_rad)) / pi) / 2 * n * tile_size
    return (x, y)


def _choose_tile_zoom(points: list[dict[str, float]], width: int, height: int, pad: int) -> int:
    for zoom in range(18, 2, -1):
        world = [_web_mercator_world_px(point, zoom) for point in points]
        span_x = max(x for x, _ in world) - min(x for x, _ in world)
        span_y = max(y for _, y in world) - min(y for _, y in world)
        if span_x <= width - pad * 2 and span_y <= height - pad * 2:
            return zoom
    return 2


def _route_map_dimensions(points: list[dict[str, float]]) -> tuple[int, int]:
    width = 900
    world = [_web_mercator_world_px(point, 18) for point in points]
    span_x = max(x for x, _ in world) - min(x for x, _ in world)
    span_y = max(y for _, y in world) - min(y for _, y in world)
    aspect = span_x / max(span_y, 0.000001)
    # Keep the map route-first: avoid the forced landscape viewport that made
    # north/south routes look zoomed out, but do not make very narrow routes unusable.
    aspect = min(max(aspect, 0.75), 1.15)
    return width, round(width / aspect)


def _render_route_map(
    points: list[dict[str, float]],
    *,
    pad: int,
) -> str:
    width, height = _route_map_dimensions(points)
    zoom = _choose_tile_zoom(points, width, height, pad)
    world = [_web_mercator_world_px(point, zoom) for point in points]
    min_x = min(x for x, _ in world)
    max_x = max(x for x, _ in world)
    min_y = min(y for _, y in world)
    max_y = max(y for _, y in world)
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    left = center_x - width / 2
    top = center_y - height / 2
    n = 2**zoom

    tile_min_x = floor(left / 256)
    tile_max_x = floor((left + width) / 256)
    tile_min_y = max(0, floor(top / 256))
    tile_max_y = min(n - 1, floor((top + height) / 256))
    tiles: list[str] = []
    for tile_y in range(tile_min_y, tile_max_y + 1):
        for tile_x in range(tile_min_x, tile_max_x + 1):
            wrapped_x = tile_x % n
            x = tile_x * 256 - left
            y = tile_y * 256 - top
            url = f"https://tile.openstreetmap.org/{zoom}/{wrapped_x}/{tile_y}.png"
            tiles.append(
                f'<image href="{url}" x="{x:.1f}" y="{y:.1f}" width="256" height="256" '
                'preserveAspectRatio="none" referrerpolicy="no-referrer"></image>'
            )
    tile_html = "".join(tiles)
    route_points = [
        f"{x - left:.1f},{y - top:.1f}"
        for x, y in world
    ]
    start_x, start_y = world[0][0] - left, world[0][1] - top
    end_x, end_y = world[-1][0] - left, world[-1][1] - top
    return f"""
  <div style="flex:1;min-height:0;display:flex;justify-content:center;align-items:stretch;">
    <div style="position:relative;overflow:hidden;height:100%;aspect-ratio:{width}/{height};
      max-width:100%;background:#d8dee4;border:1px solid #30363d;border-radius:8px;">
      <svg viewBox="0 0 {width} {height}" role="img" aria-label="GPS route map"
        style="display:block;width:100%;height:100%;background:#d8dee4;">
        {tile_html}
        <polyline points="{" ".join(route_points)}" fill="none" stroke="#0969da"
          stroke-width="9" stroke-linecap="round" stroke-linejoin="round" opacity="0.30"></polyline>
        <polyline points="{" ".join(route_points)}" fill="none" stroke="#bf3989"
          stroke-width="4" stroke-linecap="round" stroke-linejoin="round"></polyline>
        <circle cx="{start_x:.1f}" cy="{start_y:.1f}" r="9" fill="#1a7f37"
          stroke="#ffffff" stroke-width="3"></circle>
        <circle cx="{end_x:.1f}" cy="{end_y:.1f}" r="9" fill="#cf222e"
          stroke="#ffffff" stroke-width="3"></circle>
      </svg>
      <div style="position:absolute;right:8px;bottom:7px;padding:3px 6px;
        background:rgba(255,255,255,.88);color:#24292f;border-radius:4px;font-size:11px;">
        Map tiles &copy; OpenStreetMap contributors
      </div>
    </div>
  </div>
"""


def _find_recent_gps_activity(
    args: dict[str, Any],
    start: date,
    end: date,
) -> tuple[dict[str, object] | None, int]:
    from practice_theory_implementation.materials.garmin import (
        garmin_get_activity,
        garmin_list_activities,
    )

    selected_type = _activity_type_from_args(args)
    max_candidates = args.get("max_candidates", 20)
    if not isinstance(max_candidates, int):
        max_candidates = 20
    max_candidates = min(max(max_candidates, 1), 50)

    activities = garmin_list_activities(start, end)
    if selected_type is not None:
        # Filter locally so the documented aliases ("bike" → cycling) work here
        # exactly as in the activity-types dashboard, instead of passing a
        # non-typeKey to Garmin's server-side filter and matching nothing.
        # Non-preset keys still match their literal Garmin typeKey.
        if selected_type in _ACTIVITY_TYPE_PRESETS:
            activities = [
                a for a in activities if _activity_matches_type(a, selected_type)
            ]
        else:
            activities = [
                a
                for a in activities
                if _activity_type_key(a.get("type")) == selected_type
            ]
    candidates = sorted(
        activities,
        key=lambda a: str(a.get("date") or a.get("start_time_local") or ""),
        reverse=True,
    )
    examined = 0
    for activity in candidates[:max_candidates]:
        activity_id = _candidate_activity_id(activity)
        if activity_id is None:
            continue
        examined += 1
        # The list row's has_gps flag (Garmin's hasPolyline) settles non-GPS
        # candidates without the two-request detail fetch; absent flag → probe.
        if activity.get("has_gps") is False:
            continue
        try:
            detail = garmin_get_activity(activity_id)
        except Exception:  # noqa: BLE001 - skip details Garmin cannot return
            continue
        if _coerce_route_points(detail.get("route_points")):
            if "date" not in detail and isinstance(activity.get("date"), str):
                detail["date"] = activity["date"]
            return detail, examined
    return None, examined


def _activity_gps_shape_renderer(args: dict[str, Any]) -> str:
    from practice_theory_implementation.materials.garmin import garmin_get_activity

    activity_id = args.get("activity_id") or args.get("garmin_id")
    if isinstance(activity_id, int):
        activity_id = str(activity_id)
    if isinstance(activity_id, str) and activity_id.strip():
        activity_id = activity_id.strip()
        try:
            detail = garmin_get_activity(activity_id)
        except Exception as exc:  # noqa: BLE001 - unavailable activity should still render
            return _activity_lookup_fragment(activity_id, str(exc))
    else:
        try:
            end = _date_arg(args, "end_date", date.today())
            start = _date_arg(args, "start_date", end - timedelta(days=30))
        except ValueError as exc:
            # Malformed dates must render too — re-parsing them in an error
            # handler would just re-raise past the friendly fragment.
            return _activity_scan_error_fragment(
                str(args.get("start_date") or ""), str(args.get("end_date") or ""), str(exc)
            )
        try:
            recent_detail, examined = _find_recent_gps_activity(args, start, end)
        except Exception as exc:  # noqa: BLE001 - unavailable list should still render
            return _activity_scan_error_fragment(start.isoformat(), end.isoformat(), str(exc))
        if recent_detail is None:
            return _activity_scan_fragment(start.isoformat(), end.isoformat(), examined)
        detail = recent_detail
        detail_activity_id = detail.get("activity_id") or detail.get("garmin_id")
        activity_id = str(detail_activity_id) if detail_activity_id is not None else "recent"
    points = _coerce_route_points(detail.get("route_points"))
    label = _html.escape(_activity_label(detail, activity_id))
    route_summary = detail.get("route_summary")
    show_tiles = _truthy_arg(args.get("show_tiles"), default=True)
    map_style = args.get("map_style")
    if not isinstance(map_style, str):
        map_style = "osm"

    if not points:
        return (
            '<section style="min-height:100%;box-sizing:border-box;padding:28px;'
            'background:#0d1117;color:#e6edf3;font:14px ui-sans-serif,system-ui;">'
            f'<h1 style="margin:0 0 8px;font-size:22px;font-weight:650;">{label}</h1>'
            '<p style="margin:0;color:#8b949e;">No GPS route points were exposed for '
            "this activity.</p></section>"
        )

    width = 900
    height = 620
    pad = 44
    min_lat = min(p["lat"] for p in points)
    max_lat = max(p["lat"] for p in points)
    min_lon = min(p["lon"] for p in points)
    max_lon = max(p["lon"] for p in points)
    mid_lat = (min_lat + max_lat) / 2
    lon_scale = max(cos(radians(mid_lat)), 0.2)
    min_x = min_lon * lon_scale
    max_x = max_lon * lon_scale
    dx = max(max_x - min_x, 0.000001)
    dy = max(max_lat - min_lat, 0.000001)
    scale = min((width - pad * 2) / dx, (height - pad * 2) / dy)

    def xy(point: dict[str, float]) -> tuple[float, float]:
        x = pad + ((point["lon"] * lon_scale - min_x) * scale)
        y = height - pad - ((point["lat"] - min_lat) * scale)
        return (x, y)

    path_parts = []
    for idx, point in enumerate(points):
        x, y = xy(point)
        cmd = "M" if idx == 0 else "L"
        path_parts.append(f"{cmd}{x:.1f},{y:.1f}")
    path_data = " ".join(path_parts)
    start_x, start_y = xy(points[0])
    end_x, end_y = xy(points[-1])

    distance = detail.get("distance_km")
    duration = detail.get("duration_min")
    activity_when = _activity_when(detail)
    point_count = len(points)
    polyline_distance = (
        route_summary.get("polyline_distance_km")
        if isinstance(route_summary, dict)
        else None
    )
    stats = [
        ("Date/Time", activity_when),
        ("Distance", f"{distance} km" if isinstance(distance, int | float) else None),
        ("Duration", f"{duration} min" if isinstance(duration, int | float) else None),
        (
            "GPS Path",
            f"{polyline_distance} km"
            if isinstance(polyline_distance, int | float)
            else None,
        ),
        ("Points", str(point_count)),
    ]
    stat_html = "".join(
        '<div style="min-width:104px;">'
        f'<div style="color:#8b949e;font-size:11px;text-transform:uppercase;">{name}</div>'
        f'<div style="font-size:18px;font-weight:650;">{_html.escape(value)}</div>'
        "</div>"
        for name, value in stats
        if value is not None
    )
    route_display = (
        _render_route_map(points, pad=pad)
        if show_tiles and map_style == "osm"
        else f"""
  <svg viewBox="0 0 {width} {height}" role="img" aria-label="GPS route shape"
    style="display:block;width:100%;height:auto;max-height:calc(100vh - 170px);
    background:#161b22;border:1px solid #30363d;border-radius:8px;">
    <defs>
      <filter id="route-glow" x="-20%" y="-20%" width="140%" height="140%">
        <feGaussianBlur stdDeviation="3" result="blur"></feGaussianBlur>
        <feMerge>
          <feMergeNode in="blur"></feMergeNode>
          <feMergeNode in="SourceGraphic"></feMergeNode>
        </feMerge>
      </filter>
    </defs>
    <path d="{path_data}" fill="none" stroke="#2f81f7" stroke-width="14"
      stroke-linecap="round" stroke-linejoin="round" opacity="0.18"></path>
    <path d="{path_data}" fill="none" stroke="#58a6ff" stroke-width="4.5"
      stroke-linecap="round" stroke-linejoin="round" filter="url(#route-glow)"></path>
    <circle cx="{start_x:.1f}" cy="{start_y:.1f}" r="9" fill="#3fb950" stroke="#0d1117"
      stroke-width="3"></circle>
    <circle cx="{end_x:.1f}" cy="{end_y:.1f}" r="9" fill="#f85149" stroke="#0d1117"
      stroke-width="3"></circle>
  </svg>
"""
    )

    return f"""
<section style="height:calc(100vh - 44px);box-sizing:border-box;padding:18px;
  overflow:hidden;background:#0d1117;color:#e6edf3;
  font:14px ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont;
  display:flex;flex-direction:column;">
  <div style="display:flex;justify-content:space-between;gap:18px;align-items:flex-start;
    margin-bottom:16px;flex-wrap:wrap;">
    <div>
      <h1 style="margin:0 0 6px;font-size:24px;line-height:1.18;font-weight:680;">{label}</h1>
      <div style="color:#8b949e;">Activity {_html.escape(activity_id)}
        {(" &middot; " + _html.escape(activity_when)) if activity_when else ""}</div>
    </div>
    <div style="display:flex;gap:18px;flex-wrap:wrap;text-align:right;">{stat_html}</div>
  </div>
  {route_display}
</section>
"""


register_visualization("activity_gps_shape", _activity_gps_shape_renderer)


def _activity_type_empty_fragment(start: str, end: str) -> str:
    types = ", ".join(
        str(preset["label"]) for preset in _ACTIVITY_TYPE_PRESETS.values()
    )
    return (
        '<section style="min-height:100%;box-sizing:border-box;padding:24px;'
        'background:#0d1117;color:#e6edf3;font:14px ui-sans-serif,system-ui;">'
        '<h1 style="margin:0 0 8px;font-size:24px;">Activity Types</h1>'
        f'<p style="margin:0;color:#8b949e;">No matching activities from {_html.escape(start)} '
        f"to {_html.escape(end)}. Types: {_html.escape(types)}.</p></section>"
    )


def _activity_type_unsupported_fragment(requested: str) -> str:
    types = ", ".join(
        str(preset["label"]) for preset in _ACTIVITY_TYPE_PRESETS.values()
    )
    return (
        '<section style="min-height:100%;box-sizing:border-box;padding:24px;'
        'background:#0d1117;color:#e6edf3;font:14px ui-sans-serif,system-ui;">'
        '<h1 style="margin:0 0 8px;font-size:24px;">Unsupported activity type</h1>'
        f'<p style="margin:0;color:#8b949e;">No dashboard preset for '
        f"&ldquo;{_html.escape(requested)}&rdquo;. Supported types: {_html.escape(types)} "
        "(common aliases like &ldquo;bike&rdquo; are accepted).</p></section>"
    )


def _activity_type_card(
    preset_key: str,
    activities: list[dict[str, object]],
    *,
    show_tiles: bool,
) -> str:
    preset = _ACTIVITY_TYPE_PRESETS[preset_key]
    label = str(preset["label"])
    color = str(preset["color"])
    count = len(activities)
    total_minutes = sum(_number_value(activity, "duration_min") or 0 for activity in activities)
    distance_values = [
        value
        for activity in activities
        if (value := _number_value(activity, "distance_km")) is not None
    ]
    total_distance = sum(distance_values) if distance_values else None
    latest = activities[0] if activities else None
    latest_name = (
        _html.escape(str(latest.get("name") or "No recent activity"))
        if latest
        else "None"
    )
    latest_date = (
        _html.escape(str(latest.get("date") or latest.get("start_time_local") or ""))
        if latest
        else ""
    )
    latest_id = _html.escape(str(latest.get("activity_id") or "")) if latest else ""
    rows = "".join(
        "<tr>"
        "<td>"
        f"{_html.escape(str(activity.get('date') or activity.get('start_time_local') or ''))}"
        "</td>"
        "<td>"
        f"{_html.escape(str(activity.get('name') or activity.get('activity_id') or 'Activity'))}"
        "</td>"
        f"<td>{_html.escape(_fmt_num(_number_value(activity, 'duration_min'), 'min'))}</td>"
        f"<td>{_html.escape(_fmt_num(_number_value(activity, 'distance_km'), 'km'))}</td>"
        "</tr>"
        for activity in activities[:5]
    )
    preview = ""
    route_points = _coerce_route_points(latest.get("route_points")) if latest else []
    if route_points:
        preview = (
            _render_route_map(route_points, pad=34)
            if show_tiles
            else '<div style="height:100%;display:grid;place-items:center;color:#8b949e;">'
            "GPS route available</div>"
        )
    elif count:
        preview = (
            '<div style="height:100%;display:grid;place-items:center;text-align:center;'
            'padding:18px;color:#8b949e;">No GPS route points for latest activity.</div>'
        )
    else:
        preview = (
            '<div style="height:100%;display:grid;place-items:center;color:#8b949e;">'
            "No recent activity.</div>"
        )

    return f"""
    <section style="display:grid;grid-template-columns:minmax(220px,320px) minmax(0,1fr);
      gap:16px;min-height:310px;border:1px solid #30363d;border-radius:8px;padding:14px;
      background:#0d1117;">
      <div style="display:flex;flex-direction:column;gap:12px;">
        <div>
          <h2 style="margin:0 0 4px;font-size:20px;line-height:1.2;">{_html.escape(label)}</h2>
          <div style="height:3px;width:48px;background:{color};border-radius:4px;"></div>
        </div>
        <div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;">
          <div><div style="color:#8b949e;font-size:11px;text-transform:uppercase;">Count</div>
            <div style="font-size:20px;font-weight:700;">{count}</div></div>
          <div><div style="color:#8b949e;font-size:11px;text-transform:uppercase;">Minutes</div>
            <div style="font-size:20px;font-weight:700;">{total_minutes:.0f}</div></div>
          <div><div style="color:#8b949e;font-size:11px;text-transform:uppercase;">Distance</div>
            <div style="font-size:20px;font-weight:700;">
              {_html.escape(_fmt_num(total_distance, 'km'))}
            </div></div>
        </div>
        <div>
          <div style="color:#8b949e;font-size:11px;text-transform:uppercase;">Latest</div>
          <div style="font-weight:700;">{latest_name}</div>
          <div style="color:#8b949e;font-size:12px;">{latest_date} {latest_id}</div>
        </div>
        <table style="width:100%;border-collapse:collapse;font-size:12px;color:#c9d1d9;">
          <tbody>{rows}</tbody>
        </table>
      </div>
      <div style="min-height:280px;display:flex;">{preview}</div>
    </section>
"""


def _activity_type_dashboard_renderer(args: dict[str, Any]) -> str:
    from practice_theory_implementation.materials.garmin import (
        garmin_get_activity,
        garmin_list_activities,
    )

    try:
        end = _date_arg(args, "end_date", date.today())
        start = _date_arg(args, "start_date", end - timedelta(days=30))
    except ValueError as exc:
        # Malformed dates must render too, like every other failure here.
        return _activity_scan_error_fragment(
            str(args.get("start_date") or ""), str(args.get("end_date") or ""), str(exc)
        )
    selected_type = _activity_type_from_args(args)
    if selected_type is not None and selected_type not in _ACTIVITY_TYPE_PRESETS:
        # Say so rather than silently rendering the all-types dashboard as if
        # the requested filter had been applied.
        raw = args.get("activity_type") or args.get("type") or selected_type
        return _activity_type_unsupported_fragment(str(raw))
    show_tiles = _truthy_arg(args.get("show_tiles"), default=True)
    max_per_type = args.get("max_per_type", 10)
    if not isinstance(max_per_type, int):
        max_per_type = 10
    max_per_type = min(max(max_per_type, 1), 25)

    try:
        listed = garmin_list_activities(start, end)
    except Exception as exc:  # noqa: BLE001 - visualization should render the failure
        return _activity_scan_error_fragment(start.isoformat(), end.isoformat(), str(exc))

    preset_keys = (
        [selected_type]
        if selected_type in _ACTIVITY_TYPE_PRESETS
        else list(_ACTIVITY_TYPE_PRESETS)
    )
    grouped: dict[str, list[dict[str, object]]] = {key: [] for key in preset_keys}
    for activity in listed:
        for preset_key in preset_keys:
            if _activity_matches_type(activity, preset_key):
                grouped[preset_key].append(dict(activity))

    for activities in grouped.values():
        activities.sort(
            key=lambda a: str(a.get("date") or a.get("start_time_local") or ""),
            reverse=True,
        )
        del activities[max_per_type:]
        # Only the latest activity of each type gets a GPS-route preview; the rows
        # render from list-level fields the list call already returned. Fetch detail
        # for the latest alone rather than a Garmin detail round-trip per listed
        # activity — an N+1 against the live API for data the cards never read.
        if not activities:
            continue
        latest_id = _candidate_activity_id(activities[0])
        if latest_id is None:
            continue
        if activities[0].get("has_gps") is False:
            continue  # the list row already says no route — skip the detail fetch
        try:
            detail = garmin_get_activity(latest_id)
        except Exception:  # noqa: BLE001 - keep list row if detail fails
            continue
        detail.update({k: v for k, v in activities[0].items() if k not in detail})
        activities[0] = detail

    if not any(grouped.values()):
        return _activity_type_empty_fragment(start.isoformat(), end.isoformat())

    title = (
        str(_ACTIVITY_TYPE_PRESETS[selected_type]["label"])
        if selected_type in _ACTIVITY_TYPE_PRESETS
        else "Activity Types"
    )
    type_legend = " · ".join(
        str(preset["label"]) for preset in _ACTIVITY_TYPE_PRESETS.values()
    )
    cards = "".join(
        _activity_type_card(key, grouped[key], show_tiles=show_tiles)
        for key in preset_keys
    )
    return f"""
<section style="box-sizing:border-box;min-height:100%;padding:18px;background:#0d1117;
  color:#e6edf3;font:14px ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont;">
  <div style="display:flex;justify-content:space-between;gap:16px;align-items:flex-end;
    margin-bottom:16px;flex-wrap:wrap;">
    <div>
      <h1 style="margin:0 0 5px;font-size:24px;line-height:1.15;">{_html.escape(title)}</h1>
      <div style="color:#8b949e;">
        {_html.escape(start.isoformat())} to {_html.escape(end.isoformat())}
      </div>
    </div>
    <div style="color:#8b949e;">{_html.escape(type_legend)}</div>
  </div>
  <div style="display:grid;gap:14px;">{cards}</div>
</section>
"""


register_visualization("activity_types", _activity_type_dashboard_renderer)
for _activity_type_name in _ACTIVITY_TYPE_PRESETS:
    register_visualization(
        f"{_activity_type_name}_activities",
        lambda args, _name=_activity_type_name: _activity_type_dashboard_renderer(
            {**args, "activity_type": _name}
        ),
    )
