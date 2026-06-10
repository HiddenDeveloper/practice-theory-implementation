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
    assert "activity_gps_shape" in viz.list_visualizations()


def test_render_known_visualization(tmp_path: Path, monkeypatch) -> None:
    _empty_trail(tmp_path, monkeypatch)
    out = viz.render_visualization("status")
    assert out["name"] == "status"
    assert "error" not in out
    assert "Autonomic loop status" in out["html"]


def test_render_activity_gps_shape(monkeypatch) -> None:
    from practice_theory_implementation.materials import garmin

    def _activity(activity_id: str) -> dict[str, object]:
        return {
            "activity_id": activity_id,
            "name": "Morning Walk",
            "start_time_local": "2026-06-08T07:15:00",
            "distance_km": 3.6,
            "duration_min": 42,
            "route_summary": {"polyline_distance_km": 0.29},
            "route_points": [
                {"lat": 35.0, "lon": 139.0},
                {"lat": 35.001, "lon": 139.001},
                {"lat": 35.002, "lon": 139.002},
            ],
        }

    monkeypatch.setattr(garmin, "garmin_get_activity", _activity)

    out = viz.render_visualization("activity_gps_shape", {"activity_id": "42"})

    assert out["name"] == "activity_gps_shape"
    assert "error" not in out
    assert "Morning Walk" in out["html"]
    assert "GPS route map" in out["html"]
    assert "<image href=\"https://tile.openstreetmap.org/" in out["html"]
    assert "tile.openstreetmap.org" in out["html"]
    assert "OpenStreetMap contributors" in out["html"]
    assert "2026-06-08 07:15:00" in out["html"]
    assert "Date/Time" in out["html"]
    assert "3.6 km" in out["html"]


def test_render_activity_gps_shape_without_tiles(monkeypatch) -> None:
    from practice_theory_implementation.materials import garmin

    monkeypatch.setattr(
        garmin,
        "garmin_get_activity",
        lambda activity_id: {
            "activity_id": activity_id,
            "name": "Morning Walk",
            "route_points": [
                {"lat": 35.0, "lon": 139.0},
                {"lat": 35.001, "lon": 139.001},
            ],
        },
    )

    out = viz.render_visualization(
        "activity_gps_shape",
        {"activity_id": "42", "show_tiles": False},
    )

    assert out["name"] == "activity_gps_shape"
    assert "GPS route shape" in out["html"]
    assert "<path d=\"M" in out["html"]
    assert "tile.openstreetmap.org" not in out["html"]


def test_render_activity_gps_map_uses_route_first_aspect(monkeypatch) -> None:
    from practice_theory_implementation.materials import garmin

    monkeypatch.setattr(
        garmin,
        "garmin_get_activity",
        lambda activity_id: {
            "activity_id": activity_id,
            "name": "Tall Route",
            "route_points": [
                {"lat": 35.596, "lon": 139.660},
                {"lat": 35.603, "lon": 139.655},
                {"lat": 35.610, "lon": 139.658},
                {"lat": 35.616, "lon": 139.661},
            ],
        },
    )

    out = viz.render_visualization("activity_gps_shape", {"activity_id": "42"})

    assert 'viewBox="0 0 900 1200"' in out["html"]
    assert "height:calc(100vh - 44px)" in out["html"]
    assert "display:flex;justify-content:center" in out["html"]
    assert "height:100%;aspect-ratio:900/1200" in out["html"]
    assert "GPS route map" in out["html"]


def test_render_activity_gps_shape_without_points(monkeypatch) -> None:
    from practice_theory_implementation.materials import garmin

    monkeypatch.setattr(
        garmin,
        "garmin_get_activity",
        lambda activity_id: {"activity_id": activity_id, "name": "Treadmill"},
    )

    out = viz.render_visualization("activity_gps_shape", {"activity_id": "99"})

    assert out["name"] == "activity_gps_shape"
    assert "error" not in out
    assert "Treadmill" in out["html"]
    assert "No GPS route points" in out["html"]


def test_render_activity_gps_shape_lookup_error(monkeypatch) -> None:
    from practice_theory_implementation.materials import garmin

    def _missing(activity_id: str) -> dict[str, object]:
        raise RuntimeError(
            "API client error (404): Error in request: 404 Client Error: "
            f"Not Found for url: https://connectapi.garmin.com/activity-service/activity/{activity_id}"
        )

    monkeypatch.setattr(garmin, "garmin_get_activity", _missing)

    out = viz.render_visualization("activity_gps_shape", {"activity_id": "42"})

    assert out["name"] == "activity_gps_shape"
    assert "error" not in out
    assert "Garmin did not return this activity" in out["html"]
    assert "recent_activity" in out["html"]
    assert "activity-service/activity/42" in out["html"]


def test_render_activity_gps_shape_finds_recent_route(monkeypatch) -> None:
    from practice_theory_implementation.materials import garmin

    monkeypatch.setattr(
        garmin,
        "garmin_list_activities",
        lambda start_date, end_date, activity_type=None: [
            {"activity_id": "no-gps", "date": "2026-06-07"},
            {"activity_id": "gps", "date": "2026-06-08"},
        ],
    )

    def _detail(activity_id: str) -> dict[str, object]:
        if activity_id == "no-gps":
            return {"activity_id": activity_id, "name": "Indoor"}
        return {
            "activity_id": activity_id,
            "name": "Evening Run",
            "date": "2026-06-08",
            "route_points": [
                {"lat": 35.0, "lon": 139.0},
                {"lat": 35.001, "lon": 139.001},
            ],
        }

    monkeypatch.setattr(garmin, "garmin_get_activity", _detail)

    out = viz.render_visualization(
        "activity_gps_shape",
        {"start_date": "2026-06-01", "end_date": "2026-06-09"},
    )

    assert out["name"] == "activity_gps_shape"
    assert "error" not in out
    assert "Evening Run" in out["html"]
    assert "Activity gps" in out["html"]
    assert "2026-06-08" in out["html"]
    assert "GPS route map" in out["html"]


def test_render_activity_gps_shape_recent_route_not_found(monkeypatch) -> None:
    from practice_theory_implementation.materials import garmin

    monkeypatch.setattr(
        garmin,
        "garmin_list_activities",
        lambda start_date, end_date, activity_type=None: [
            {"activity_id": "a", "date": "2026-06-08"}
        ],
    )
    monkeypatch.setattr(
        garmin,
        "garmin_get_activity",
        lambda activity_id: {"activity_id": activity_id, "name": "Indoor"},
    )

    out = viz.render_visualization(
        "activity_gps_shape",
        {"start_date": "2026-06-01", "end_date": "2026-06-09"},
    )

    assert out["name"] == "activity_gps_shape"
    assert "error" not in out
    assert "No GPS activity found" in out["html"]
    assert "Checked 1 activities" in out["html"]


def test_garmin_activity_gps_shape_material_returns_app_payload(monkeypatch) -> None:
    from practice_theory_implementation.materials import garmin

    monkeypatch.setattr(
        garmin,
        "garmin_get_activity",
        lambda activity_id: {
            "activity_id": activity_id,
            "name": "Morning Walk",
            "route_points": [
                {"lat": 35.0, "lon": 139.0},
                {"lat": 35.001, "lon": 139.001},
            ],
        },
    )

    out = garmin.garmin_render_activity_gps_shape(activity_id="42")

    assert out["name"] == "activity_gps_shape"
    assert "Morning Walk" in out["html"]
    assert out["mcp_app"] == {
        "tool": "show_visualization",
        "name": "activity_gps_shape",
        "args": {
            "max_candidates": 20,
            "show_tiles": True,
            "map_style": "osm",
            "activity_id": "42",
        },
    }


def test_render_activity_types_dashboard(monkeypatch) -> None:
    from practice_theory_implementation.materials import garmin

    activities = [
        {
            "activity_id": "walk",
            "date": "2026-06-08",
            "name": "Setagaya Walk",
            "type": "walking",
            "duration_min": 60,
            "distance_km": 5.3,
        },
        {
            "activity_id": "bike",
            "date": "2026-06-07",
            "name": "River Ride",
            "type": "cycling",
            "duration_min": 45,
            "distance_km": 12.2,
        },
        {
            "activity_id": "strength",
            "date": "2026-06-06",
            "name": "Weights",
            "type": "strength_training",
            "duration_min": 35,
        },
        {
            "activity_id": "pilates",
            "date": "2026-06-05",
            "name": "Pilates",
            "type": "pilates",
            "duration_min": 40,
        },
        {
            "activity_id": "yoga",
            "date": "2026-06-04",
            "name": "Yoga",
            "type": "yoga",
            "duration_min": 25,
        },
    ]
    monkeypatch.setattr(
        garmin,
        "garmin_list_activities",
        lambda start_date, end_date, activity_type=None: activities,
    )
    monkeypatch.setattr(
        garmin,
        "garmin_get_activity",
        lambda activity_id: {
            **next(a for a in activities if a["activity_id"] == activity_id),
            "route_points": (
                [
                    {"lat": 35.0, "lon": 139.0},
                    {"lat": 35.001, "lon": 139.001},
                ]
                if activity_id in {"walk", "bike"}
                else None
            ),
        },
    )

    out = viz.render_visualization(
        "activity_types",
        {"start_date": "2026-06-01", "end_date": "2026-06-09"},
    )

    assert out["name"] == "activity_types"
    assert "Walking" in out["html"]
    assert "Cycling" in out["html"]
    assert "Strength Training" in out["html"]
    assert "Pilates" in out["html"]
    assert "Yoga" in out["html"]
    assert "Setagaya Walk" in out["html"]
    assert "River Ride" in out["html"]
    assert "GPS route map" in out["html"]


def test_render_activity_type_alias(monkeypatch) -> None:
    from practice_theory_implementation.materials import garmin

    monkeypatch.setattr(
        garmin,
        "garmin_list_activities",
        lambda start_date, end_date, activity_type=None: [
            {
                "activity_id": "walk",
                "date": "2026-06-08",
                "name": "Walk",
                "type": "walk",
                "duration_min": 30,
            },
            {
                "activity_id": "yoga",
                "date": "2026-06-07",
                "name": "Yoga",
                "type": "yoga",
                "duration_min": 20,
            },
        ],
    )
    monkeypatch.setattr(
        garmin,
        "garmin_get_activity",
        lambda activity_id: {
            "activity_id": activity_id,
            "name": activity_id,
            "type": activity_id,
        },
    )

    out = viz.render_visualization(
        "walking_activities",
        {"start_date": "2026-06-01", "end_date": "2026-06-09"},
    )

    assert out["name"] == "walking_activities"
    assert "Walking" in out["html"]
    assert "Walk" in out["html"]
    assert "Yoga</td>" not in out["html"]


def test_garmin_activity_type_material_returns_app_payload(monkeypatch) -> None:
    from practice_theory_implementation.materials import garmin

    monkeypatch.setattr(
        garmin,
        "garmin_list_activities",
        lambda start_date, end_date, activity_type=None: [
            {
                "activity_id": "yoga",
                "date": "2026-06-07",
                "name": "Yoga",
                "type": "yoga",
                "duration_min": 20,
            }
        ],
    )
    monkeypatch.setattr(
        garmin,
        "garmin_get_activity",
        lambda activity_id: {"activity_id": activity_id, "type": "yoga"},
    )

    out = garmin.garmin_render_activity_type_visualization(
        activity_type="yoga",
        start_date="2026-06-01",
        end_date="2026-06-09",
        show_tiles=False,
    )

    assert out["name"] == "activity_types"
    assert "Yoga" in out["html"]
    assert out["mcp_app"] == {
        "tool": "show_visualization",
        "name": "activity_types",
        "args": {
            "max_per_type": 10,
            "show_tiles": False,
            "activity_type": "yoga",
            "start_date": "2026-06-01",
            "end_date": "2026-06-09",
        },
    }


def test_render_activity_types_dashboard_with_empty_groups(monkeypatch) -> None:
    # A real window rarely covers every preset; empty groups must render as
    # "No recent activity" cards, not crash the whole dashboard.
    from practice_theory_implementation.materials import garmin

    monkeypatch.setattr(
        garmin,
        "garmin_list_activities",
        lambda start_date, end_date, activity_type=None: [
            {
                "activity_id": "walk",
                "date": "2026-06-08",
                "name": "Setagaya Walk",
                "type": "walking",
                "duration_min": 60,
            }
        ],
    )
    monkeypatch.setattr(
        garmin,
        "garmin_get_activity",
        lambda activity_id: {"activity_id": activity_id, "type": "walking"},
    )

    out = viz.render_visualization(
        "activity_types",
        {"start_date": "2026-06-01", "end_date": "2026-06-09"},
    )

    assert "error" not in out
    assert "Setagaya Walk" in out["html"]
    for label in ("Walking", "Cycling", "Strength Training", "Pilates", "Yoga"):
        assert label in out["html"]
    assert "No recent activity" in out["html"]


def test_render_activity_types_unsupported_type() -> None:
    out = viz.render_visualization("activity_types", {"activity_type": "running"})

    assert "error" not in out
    assert "Unsupported activity type" in out["html"]
    assert "running" in out["html"]


def test_render_activity_types_invalid_date_renders_fragment() -> None:
    out = viz.render_visualization("activity_types", {"start_date": "06/01/2026"})

    assert "error" not in out
    assert "Could not list recent activities" in out["html"]
    assert "06/01/2026" in out["html"]


def test_render_activity_gps_shape_invalid_date_renders_fragment() -> None:
    out = viz.render_visualization("activity_gps_shape", {"start_date": "06/01/2026"})

    assert "error" not in out
    assert "Could not list recent activities" in out["html"]
    assert "06/01/2026" in out["html"]


def test_render_activity_gps_shape_accepts_type_alias(monkeypatch) -> None:
    from practice_theory_implementation.materials import garmin

    monkeypatch.setattr(
        garmin,
        "garmin_list_activities",
        lambda start_date, end_date, activity_type=None: [
            {"activity_id": "walk", "date": "2026-06-08", "type": "walking"},
            {"activity_id": "ride", "date": "2026-06-07", "type": "cycling"},
        ],
    )
    monkeypatch.setattr(
        garmin,
        "garmin_get_activity",
        lambda activity_id: {
            "activity_id": activity_id,
            "name": "River Ride" if activity_id == "ride" else "Walk",
            "route_points": [
                {"lat": 35.0, "lon": 139.0},
                {"lat": 35.001, "lon": 139.001},
            ],
        },
    )

    out = viz.render_visualization(
        "activity_gps_shape",
        {"start_date": "2026-06-01", "end_date": "2026-06-09", "activity_type": "bike"},
    )

    assert "error" not in out
    # "bike" must reach the cycling activity, not be passed to Garmin verbatim
    # (where it matches nothing) and not fall through to the newer walk.
    assert "River Ride" in out["html"]


def test_gps_scan_skips_rows_flagged_without_gps(monkeypatch) -> None:
    from practice_theory_implementation.materials import garmin

    fetched: list[str] = []

    monkeypatch.setattr(
        garmin,
        "garmin_list_activities",
        lambda start_date, end_date, activity_type=None: [
            {"activity_id": "indoor", "date": "2026-06-08", "has_gps": False},
            {"activity_id": "outdoor", "date": "2026-06-07", "has_gps": True},
        ],
    )

    def _detail(activity_id: str) -> dict[str, object]:
        fetched.append(activity_id)
        return {
            "activity_id": activity_id,
            "name": "Evening Walk",
            "route_points": [
                {"lat": 35.0, "lon": 139.0},
                {"lat": 35.001, "lon": 139.001},
            ],
        }

    monkeypatch.setattr(garmin, "garmin_get_activity", _detail)

    out = viz.render_visualization(
        "activity_gps_shape",
        {"start_date": "2026-06-01", "end_date": "2026-06-09"},
    )

    assert "error" not in out
    assert "Evening Walk" in out["html"]
    assert fetched == ["outdoor"]  # the flagged row settles without a detail fetch


def test_error_results_echo_args() -> None:
    out = viz.render_visualization("does-not-exist", {"x": 1})
    assert out["args"] == {"x": 1}  # the shell's Refresh must be able to retry

    def _boom(args: dict) -> str:
        raise RuntimeError("kaboom")

    viz.register_visualization("boom-args", _boom)
    out = viz.render_visualization("boom-args", {"y": 2})
    assert "error" in out
    assert out["args"] == {"y": 2}


def test_material_enum_derives_from_presets() -> None:
    from practice_theory_implementation.material_surfaces import MATERIAL_SURFACES

    surface = MATERIAL_SURFACES["garmin_render_activity_type_visualization"]
    enum = surface.input_schema["properties"]["activity_type"]["enum"]
    assert enum == viz.activity_type_keys()


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
        "appInfo",  # the host SDK validates appInfo (not clientInfo)
        "ui/notifications/initialized",
        "ui/notifications/tool-result",
        "tools/call",
        "show_visualization",
        "2025-06-18",
    ):
        assert token in shell, f"shell missing {token!r}"
    assert "clientInfo" not in shell  # the spec doc's field name is wrong here
    assert "#viz { height:calc(100vh - var(--bar-height)); overflow:auto; }" in shell
    assert "html,body { margin:0; height:100%; overflow:hidden;" in shell
    assert "#viz { min-height:100vh; padding-bottom:44px; }" not in shell


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
