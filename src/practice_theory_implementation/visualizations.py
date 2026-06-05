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

    Returns `{name, html}` on success, or `{name, error, available, html}` when
    the name is unknown or the renderer raises — always with a displayable `html`
    so the shell can show the problem rather than going blank.
    """
    renderer = _REGISTRY.get(name)
    if renderer is None:
        avail = list_visualizations()
        return {
            "name": name,
            "error": f"unknown visualization {name!r}",
            "available": avail,
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
            "html": _error_fragment(f"Visualization {name!r} failed: {exc}"),
        }
    return {"name": name, "html": html}


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
  html,body { margin:0; background:#0d1117; color:#e6edf3;
    font:14px ui-monospace,Menlo,Consolas,monospace; }
  #viz { min-height:100vh; padding-bottom:44px; }
  #loading { padding:48px; text-align:center; color:#7d8590; }
  #bar { position:fixed; bottom:0; left:0; right:0; display:flex; gap:10px;
    align-items:center; padding:7px 14px; background:#161b22;
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
    var html = null, name = null;
    var data = result.structuredContent;
    if (data) { html = data.html; name = data.name; }
    if (html == null && result.content) {
      var t = result.content.filter(function (c) { return c.type === "text"; })[0];
      if (t) {
        try { var p = JSON.parse(t.text); html = p.html; name = p.name; }
        catch (e) { html = t.text; }
      }
    }
    if (name) { currentName = name; nameEl.textContent = name; }
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
    clientInfo: { name: "practice-viz-shell", version: "1.0.0" }
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
