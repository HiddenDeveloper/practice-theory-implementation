"""Garmin materials for Activities Management."""

from __future__ import annotations

import os
from datetime import date

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
