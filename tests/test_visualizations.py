"""Visualization registry + generic MCP Apps shell (server-rendered fragments)."""

from __future__ import annotations

from pathlib import Path

from practice_theory_implementation import visualizations as viz
from practice_theory_implementation.materials import status_dashboard as sd
from practice_theory_implementation.trail import EnactmentStore


def _empty_trail(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "trail.db"
    monkeypatch.setenv("PRACTICE_TRAIL_PATH", str(path))
    EnactmentStore(path).close()


def test_status_visualization_is_registered() -> None:
    assert "status" in viz.list_visualizations()


def test_render_known_visualization(tmp_path: Path, monkeypatch) -> None:
    _empty_trail(tmp_path, monkeypatch)
    out = viz.render_visualization("status")
    assert out["name"] == "status"
    assert "error" not in out
    assert "Autonomic loop status" in out["html"]


def test_unknown_visualization_returns_error_fragment() -> None:
    out = viz.render_visualization("does-not-exist")
    assert "error" in out
    assert "status" in out["available"]
    assert "Unknown visualization" in out["html"]  # displayable, not blank


def test_renderer_exception_is_contained() -> None:
    def _boom(args: dict) -> str:
        raise RuntimeError("kaboom")

    viz.register_visualization("boom", _boom)
    out = viz.render_visualization("boom")
    assert "error" in out and "kaboom" in out["error"]
    assert "boom" in out["html"]  # still renders a message


def test_shell_implements_the_apps_handshake() -> None:
    shell = viz.render_viz_shell_html()
    for token in (
        "ui/initialize",
        "ui/notifications/initialized",
        "ui/notifications/tool-result",
        "tools/call",
        "show_visualization",
        "2025-06-18",
    ):
        assert token in shell, f"shell missing {token!r}"


def test_shell_resource_constants() -> None:
    assert viz.VIZ_RESOURCE_URI == "ui://viz/shell.html"
    assert viz.VIZ_MIME_TYPE == "text/html;profile=mcp-app"


def test_fragment_is_embeddable_not_a_full_document(
    tmp_path: Path, monkeypatch
) -> None:
    _empty_trail(tmp_path, monkeypatch)
    frag = sd.render_dashboard_fragment(sd.gather_dashboard_status())
    assert "<!doctype" not in frag.lower()
    assert 'http-equiv="refresh"' not in frag  # the shell owns refresh, not meta
    assert "<style>" in frag and "Autonomic loop status" in frag


def test_full_html_still_renders_with_meta_refresh(
    tmp_path: Path, monkeypatch
) -> None:
    _empty_trail(tmp_path, monkeypatch)
    doc = sd.render_dashboard_html(sd.gather_dashboard_status(), refresh_seconds=12)
    assert doc.startswith("<!doctype html>")
    assert 'http-equiv="refresh" content="12"' in doc
