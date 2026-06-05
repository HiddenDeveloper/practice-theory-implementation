"""Tiny HTTP server for the autonomic-loop status dashboard.

Serves a self-refreshing HTML page that reads the live trail on every request,
so the numbers are always current — open the URL once and leave it up. Read-only:
it renders the same view as the `render_status_dashboard` affordance, but live.

Run: `uv run python -m practice_theory_implementation.status_dashboard_server`
Env: PRACTICE_DASHBOARD_HOST (default 127.0.0.1),
     PRACTICE_DASHBOARD_PORT (default 7182),
     PRACTICE_DASHBOARD_REFRESH_SECONDS (default 10).
"""

from __future__ import annotations

import logging
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from practice_theory_implementation.materials.status_dashboard import (
    gather_dashboard_status,
    render_dashboard_html,
)

logger = logging.getLogger(__name__)

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 7182
DEFAULT_REFRESH_SECONDS = 10


def _refresh_seconds() -> int:
    raw = os.environ.get("PRACTICE_DASHBOARD_REFRESH_SECONDS", "").strip()
    try:
        return max(2, int(raw)) if raw else DEFAULT_REFRESH_SECONDS
    except ValueError:
        return DEFAULT_REFRESH_SECONDS


class _DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 (http.server API)
        if self.path not in ("/", "/index.html"):
            self.send_error(404, "Not found")
            return
        try:
            status = gather_dashboard_status()
            body = render_dashboard_html(
                status, refresh_seconds=_refresh_seconds()
            ).encode("utf-8")
        except Exception:
            logger.exception("dashboard render failed")
            self.send_error(500, "Dashboard render failed")
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        return  # keep the service log quiet


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    host = os.environ.get("PRACTICE_DASHBOARD_HOST", DEFAULT_HOST)
    port = int(os.environ.get("PRACTICE_DASHBOARD_PORT", str(DEFAULT_PORT)))
    server = ThreadingHTTPServer((host, port), _DashboardHandler)
    logger.info(
        "status dashboard on http://%s:%d/ (refresh %ds)",
        host,
        port,
        _refresh_seconds(),
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
