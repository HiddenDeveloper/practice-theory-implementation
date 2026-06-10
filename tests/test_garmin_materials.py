from __future__ import annotations

from typing import Any, cast

from practice_theory_implementation.materials import garmin, garmin_live


class _FakeGarminClient:
    def get_stats(self, day: str) -> dict[str, object]:
        return {
            "calendarDate": day,
            "totalSteps": 1234,
            "sleepingSeconds": None,
            "averageStressLevel": 7,
            "bodyBatteryMostRecentValue": 55,
            "restingHeartRate": 61,
            "totalDistanceMeters": 2500,
            "activeKilocalories": 120,
        }

    def get_sleep_data(self, day: str) -> dict[str, object]:
        return {"dailySleepDTO": {"sleepTimeSeconds": 25200}}

    def get_activities_by_date(
        self, start_date: str, end_date: str, activity_type: str
    ) -> list[dict[str, object]]:
        return [
            {
                "activityId": 42,
                "activityName": "Morning Walk",
                "activityType": {"typeKey": activity_type or "walking"},
                "hasPolyline": True,
                "startTimeLocal": f"{start_date} 07:15:00",
                "movingDuration": 1800,
                "distance": 3200,
                "averageHR": 118,
                "maxHR": 135,
                "steps": 4100,
                "calories": 140,
            }
        ]

    def get_activity(self, activity_id: int) -> dict[str, object]:
        return {
            "activityId": activity_id,
            "activityName": "Morning Walk",
            "activityTypeDTO": {"typeKey": "walking"},
            "summaryDTO": {
                "startTimeLocal": "2026-06-07 07:15:00",
                "movingDuration": 1800,
                "distance": 3200,
                "steps": 4100,
            },
            "metadataDTO": {"lapCount": 1},
        }

    def get_activity_details(
        self, activity_id: int, maxchart: int, maxpoly: int  # cspell:ignore maxchart maxpoly
    ) -> dict[str, object]:
        return {
            "metricDescriptors": [
                {"metricsIndex": 0, "key": "directTimestamp"},
                {"metricsIndex": 1, "key": "directSpeed"},
                {"metricsIndex": 2, "key": "directDoubleCadence"},
            ],
            "activityDetailMetrics": [
                {"metrics": [1_780_000_000_000, 1.5, 112]},
                {"metrics": [1_780_000_060_000, 1.9, 138]},
                {"metrics": [1_780_000_180_000, 1.5, 110]},
            ],
            "geoPolylineDTO": {
                "polyline": [
                    {
                        "lat": 35.0,
                        "lon": 139.0,
                        "time": 1_780_000_000_000,
                        "speed": 0.0,
                        "valid": True,
                    },
                    {
                        "lat": 35.001,
                        "lon": 139.001,
                        "time": 1_780_000_060_000,
                        "speed": 1.8,
                        "valid": True,
                    },
                    {
                        "lat": 35.002,
                        "lon": 139.002,
                        "time": 1_780_000_180_000,
                        "speed": 1.5,
                        "valid": True,
                    },
                ]
            },
        }


def test_garmin_defaults_to_live_source(monkeypatch) -> None:
    garmin_live._client.cache_clear()
    monkeypatch.delenv("PRACTICE_GARMIN_SOURCE", raising=False)
    monkeypatch.setattr(garmin_live, "_client", lambda: _FakeGarminClient())

    summary = garmin.garmin_get_daily_summary("2026-06-07")
    activities = garmin.garmin_list_activities("2026-06-07", "2026-06-07")

    assert summary["source"] == "garminconnect_live"
    assert summary["sleep_hours"] == 7.0
    assert activities[0]["activity_id"] == "42"
    assert activities[0]["provider"] == "garmin"
    assert activities[0]["has_gps"] is True


def test_garmin_activity_detail_includes_route_data(monkeypatch) -> None:
    garmin_live._client.cache_clear()
    monkeypatch.delenv("PRACTICE_GARMIN_SOURCE", raising=False)
    monkeypatch.setattr(garmin_live, "_client", lambda: _FakeGarminClient())

    detail = garmin.garmin_get_activity("42")

    assert detail["source"] == "garminconnect_live"
    assert detail["metric_samples"] == [
        {
            "directTimestamp": 1_780_000_000_000,
            "directSpeed": 1.5,
            "directDoubleCadence": 112,
        },
        {
            "directTimestamp": 1_780_000_060_000,
            "directSpeed": 1.9,
            "directDoubleCadence": 138,
        },
        {
            "directTimestamp": 1_780_000_180_000,
            "directSpeed": 1.5,
            "directDoubleCadence": 110,
        },
    ]
    assert detail["route_summary"] == {
        "point_count": 3,
        "polyline_distance_km": 0.29,
        "start": {"lat": 35.0, "lon": 139.0},
        "end": {"lat": 35.002, "lon": 139.002},
        "start_end_distance_m": 287.5,
        "bounding_box": {
            "min_lat": 35.0,
            "max_lat": 35.002,
            "min_lon": 139.0,
            "max_lon": 139.002,
        },
    }
    assert detail["route_points"] == [
        {"lat": 35.0, "lon": 139.0, "timestamp": 1_780_000_000_000, "speed": 0.0},
        {"lat": 35.001, "lon": 139.001, "timestamp": 1_780_000_060_000, "speed": 1.8},
        {"lat": 35.002, "lon": 139.002, "timestamp": 1_780_000_180_000, "speed": 1.5},
    ]


def test_garmin_route_aware_iwt_analysis(monkeypatch) -> None:
    garmin_live._client.cache_clear()
    monkeypatch.delenv("PRACTICE_GARMIN_SOURCE", raising=False)
    monkeypatch.setattr(garmin_live, "_client", lambda: _FakeGarminClient())

    analysis = garmin.garmin_route_aware_iwt_analysis(
        "2026-06-07",
        "2026-06-07",
        normal_minutes=1,
        fast_minutes=1,
        repetitions=1,
    )

    assert analysis["source"] == "garminconnect_live"
    assert analysis["activity_count"] == 1
    assert analysis["iwt_pattern_present_count"] == 1
    assert analysis["route_comparability"] == {
        "with_gps_count": 1,
        "start_spread_m": 0.0,
        "end_spread_m": 0.0,
        "polyline_distance_min_km": 0.29,
        "polyline_distance_max_km": 0.29,
        "same_route_likely": True,
    }
    activities = cast(list[dict[str, Any]], analysis["activities"])
    activity = activities[0]
    assert activity["fast_vs_normal_speed_lift_pct"] == 26.7
    assert activity["relaxed_vs_fast_speed_drop_pct"] == 21.1
    assert activity["iwt_pattern_present"] is True
    assert activity["segments"][0]["label"] == "normal"
    assert activity["segments"][1]["label"] == "fast"


def test_garmin_mock_requires_explicit_source(monkeypatch) -> None:
    monkeypatch.setenv("PRACTICE_GARMIN_SOURCE", "mock")

    summary = garmin.garmin_get_daily_summary("2026-06-07")

    assert summary == {
        "date": "2026-06-07",
        "steps": 12410,
        "sleep_hours": 6.0,
        "stress_avg": 50,
        "body_battery_end": 40,
    }
