"""Garmin materials for Activities Management."""

from __future__ import annotations

import os
from datetime import date
from typing import Any

from practice_theory_implementation.materials import garmin_live, garmin_mock


def _impl():
    source = os.environ.get("PRACTICE_GARMIN_SOURCE", "live").lower()
    return garmin_mock if source == "mock" else garmin_live


def garmin_list_activities(
    start_date: date | str,
    end_date: date | str,
    activity_type: str | None = None,
) -> list[dict[str, object]]:
    return _impl().garmin_list_activities(start_date, end_date, activity_type)


def garmin_get_activity(activity_id: str) -> dict[str, object]:
    return _impl().garmin_get_activity(activity_id)


def garmin_get_daily_summary(date: date | str) -> dict[str, object]:  # noqa: A002
    return _impl().garmin_get_daily_summary(date)


def garmin_get_user_stats(
    start_date: date | str,
    end_date: date | str,
) -> dict[str, object]:
    return _impl().garmin_get_user_stats(start_date, end_date)


def garmin_route_aware_iwt_analysis(
    start_date: date | str,
    end_date: date | str,
    normal_minutes: int = 3,
    fast_minutes: int = 3,
    repetitions: int = 5,
    activity_type: str = "walking",
) -> dict[str, object]:
    return _impl().garmin_route_aware_iwt_analysis(
        start_date,
        end_date,
        normal_minutes,
        fast_minutes,
        repetitions,
        activity_type,
    )


def garmin_render_activity_gps_shape(
    activity_id: str | None = None,
    garmin_id: str | None = None,
    start_date: date | str | None = None,
    end_date: date | str | None = None,
    activity_type: str | None = None,
    max_candidates: int = 20,
    show_tiles: bool = True,
    map_style: str = "osm",
) -> dict[str, Any]:
    """Render the GPS route-shape MCP App payload for Activities Management."""
    from practice_theory_implementation.visualizations import render_visualization

    args: dict[str, Any] = {
        "max_candidates": max_candidates,
        "show_tiles": show_tiles,
        "map_style": map_style,
    }
    if activity_id:
        args["activity_id"] = activity_id
    if garmin_id:
        args["garmin_id"] = garmin_id
    if start_date:
        args["start_date"] = (
            start_date.isoformat() if isinstance(start_date, date) else start_date
        )
    if end_date:
        args["end_date"] = (
            end_date.isoformat() if isinstance(end_date, date) else end_date
        )
    if activity_type:
        args["activity_type"] = activity_type
    result = render_visualization("activity_gps_shape", args)
    result["mcp_app"] = {
        "tool": "show_visualization",
        "name": "activity_gps_shape",
        "args": args,
    }
    return result


def garmin_render_activity_type_visualization(
    activity_type: str | None = None,
    start_date: date | str | None = None,
    end_date: date | str | None = None,
    max_per_type: int = 10,
    show_tiles: bool = True,
) -> dict[str, Any]:
    """Render the activity-type dashboard MCP App payload for Activities Management."""
    from practice_theory_implementation.visualizations import render_visualization

    args: dict[str, Any] = {
        "max_per_type": max_per_type,
        "show_tiles": show_tiles,
    }
    if activity_type:
        args["activity_type"] = activity_type
    if start_date:
        args["start_date"] = (
            start_date.isoformat() if isinstance(start_date, date) else start_date
        )
    if end_date:
        args["end_date"] = (
            end_date.isoformat() if isinstance(end_date, date) else end_date
        )
    result = render_visualization("activity_types", args)
    result["mcp_app"] = {
        "tool": "show_visualization",
        "name": "activity_types",
        "args": args,
    }
    return result
