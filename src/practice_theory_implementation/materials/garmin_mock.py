"""Mock Garmin material functions for the Activities Management bundle.

Each function returns synthetic data parameterised by date so the focus stays
on the bundle shape rather than Garmin integration. The functions are defined
under names matching the bundle's material names; step 2's registry will pick
them up by name.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import cast


def _seeded(d: date) -> int:
    """Deterministic per-day seed so synthetic output is stable for a given date."""
    return (d.year * 10000 + d.month * 100 + d.day) % 997


def _as_date(value: date | str) -> date:
    """Accept either a date object (in-process call) or an ISO string (MCP wire)."""
    if isinstance(value, date):
        return value
    return date.fromisoformat(value)


def garmin_list_activities(
    start_date: date | str,
    end_date: date | str,
    activity_type: str | None = None,
) -> list[dict[str, object]]:
    start_date = _as_date(start_date)
    end_date = _as_date(end_date)
    out: list[dict[str, object]] = []
    day = start_date
    while day <= end_date:
        s = _seeded(day)
        if s % 3 == 0:
            kind = "walk"
            minutes = 30 + (s % 30)
            distance_km = round(2.0 + (s % 10) * 0.3, 2)
        elif s % 3 == 1:
            kind = "run"
            minutes = 25 + (s % 25)
            distance_km = round(4.0 + (s % 8) * 0.5, 2)
        else:
            kind = "cycle"
            minutes = 40 + (s % 40)
            distance_km = round(10.0 + (s % 20) * 0.7, 2)

        if activity_type is None or activity_type == kind:
            out.append(
                {
                    "activity_id": f"act-{day.isoformat()}-{s:03d}",
                    "date": day.isoformat(),
                    "type": kind,
                    "duration_min": minutes,
                    "distance_km": distance_km,
                    "avg_hr": 110 + (s % 50),
                }
            )
        day += timedelta(days=1)
    return out


def garmin_get_activity(activity_id: str) -> dict[str, object]:
    return {
        "activity_id": activity_id,
        "type": "walk",
        "duration_min": 42,
        "distance_km": 3.6,
        "avg_hr": 124,
        "splits": [
            {"km": 1, "pace_min_per_km": 11.4, "avg_hr": 118},
            {"km": 2, "pace_min_per_km": 11.0, "avg_hr": 125},
            {"km": 3, "pace_min_per_km": 10.9, "avg_hr": 130},
        ],
        "notes": "synthetic mock — fixed shape, varies only by activity_id",
    }


def garmin_get_daily_summary(date: date | str) -> dict[str, object]:  # noqa: A002
    d = _as_date(date)
    s = _seeded(d)
    return {
        "date": d.isoformat(),
        "steps": 5000 + (s * 13) % 8000,
        "sleep_hours": round(6.0 + (s % 30) * 0.1, 1),
        "stress_avg": 20 + (s % 60),
        "body_battery_end": 30 + (s % 70),
    }


def garmin_get_user_stats(
    start_date: date | str,
    end_date: date | str,
) -> dict[str, object]:
    start_date = _as_date(start_date)
    end_date = _as_date(end_date)
    days = (end_date - start_date).days + 1
    activities = garmin_list_activities(start_date, end_date)
    total_minutes = sum(cast(int, a["duration_min"]) for a in activities)
    total_distance = round(sum(cast(float, a["distance_km"]) for a in activities), 2)
    by_type: dict[str, int] = {}
    for a in activities:
        by_type[str(a["type"])] = by_type.get(str(a["type"]), 0) + 1
    return {
        "period": {"start": start_date.isoformat(), "end": end_date.isoformat(), "days": days},
        "activity_count": len(activities),
        "total_minutes": total_minutes,
        "total_distance_km": total_distance,
        "by_type": by_type,
    }


def garmin_route_aware_iwt_analysis(
    start_date: date | str,
    end_date: date | str,
    normal_minutes: int = 3,
    fast_minutes: int = 3,
    repetitions: int = 5,
    activity_type: str = "walking",
) -> dict[str, object]:
    start = _as_date(start_date)
    end = _as_date(end_date)
    return {
        "period": {"start": start.isoformat(), "end": end.isoformat()},
        "intended_pattern": {
            "normal_minutes": normal_minutes,
            "fast_minutes": fast_minutes,
            "repetitions": repetitions,
            "iwt_minutes": (normal_minutes + fast_minutes) * repetitions,
            "post_iwt_expectation": "relaxed walking",
        },
        "activity_count": 0,
        "iwt_pattern_present_count": 0,
        "route_comparability": {
            "with_gps_count": 0,
            "same_route_likely": False,
        },
        "activities": [],
        "source": "garmin_mock",
        "provider": "garmin",
        "notes": f"synthetic mock — no GPS route samples for {activity_type}",
    }
