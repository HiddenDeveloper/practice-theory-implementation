"""Live Garmin Connect materials for Activities Management.

Garmin is the source of truth for this practice. The materials return compact,
source-labeled shapes that match the existing affordances while keeping Garmin
authentication local to this repository. Mock output is still available only
when explicitly selected for verification/demo runs.
"""

from __future__ import annotations

import os
from datetime import date
from functools import lru_cache
from math import atan2, cos, degrees, radians, sin, sqrt
from pathlib import Path
from statistics import mean
from typing import Any, cast

_SOURCE = "garminconnect_live"
_TOKEN_ENV = "GARMINTOKENS"
_DEFAULT_TOKEN_PATH = "~/.garminconnect"
_EARTH_RADIUS_M = 6_371_000
_MAX_ROUTE_POINTS = 750
_BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)


def _as_date(value: date | str) -> date:
    if isinstance(value, date):
        return value
    return date.fromisoformat(value)


def _token_path() -> Path:
    return Path(os.path.expanduser(os.environ.get(_TOKEN_ENV, _DEFAULT_TOKEN_PATH)))


def _is_cn() -> bool:
    return os.environ.get("GARMIN_IS_CN", "").lower() in {"1", "true", "yes", "on"}


def _email() -> str | None:
    return os.environ.get("GARMIN_EMAIL") or os.environ.get("GARMIN_USER_NAME")


def _password() -> str | None:
    return os.environ.get("GARMIN_PASSWORD")


def _patch_garth_transport() -> None:
    """Apply the Garmin/garth Cloudflare workaround when dependencies exist."""
    try:
        import garth.http
        from curl_cffi import requests as cffi_requests
        from requests.adapters import HTTPAdapter
        from requests.models import Response
    except ImportError:
        return

    if vars(garth.http.client.sess).get("_practice_garmin_patched"):
        return

    class _ImpersonateAdapter(HTTPAdapter):
        def __init__(self) -> None:
            self._cffi = cffi_requests.Session()
            super().__init__()

        def send(self, request, **kwargs):  # type: ignore[no-untyped-def]
            raw = cast(
                Any,
                self._cffi.request(
                    method=request.method,
                    url=request.url,
                    headers=dict(request.headers),
                    data=request.body,
                    impersonate="chrome124",
                    allow_redirects=False,
                    timeout=kwargs.get("timeout") or 30,
                    verify=kwargs.get("verify", True),
                    proxies=kwargs.get("proxies") or None,
                ),
            )
            resp = Response()
            resp.status_code = raw.status_code
            resp._content = raw.content
            resp.headers.update(raw.headers)
            resp.url = raw.url
            resp.request = request
            for cookie in raw.cookies.jar:
                resp.cookies.set_cookie(cookie)
            return resp

    garth.http.USER_AGENT = {"User-Agent": _BROWSER_UA}
    adapter = _ImpersonateAdapter()
    garth.http.client.sess.mount("https://", adapter)
    garth.http.client.sess.mount("http://", adapter)
    vars(garth.http.client.sess)["_practice_garmin_patched"] = True


@lru_cache(maxsize=1)
def _client() -> Any:
    try:
        from garminconnect import Garmin
    except ImportError as exc:
        raise RuntimeError(
            "Install the 'garminconnect' dependency to use live Garmin data."
        ) from exc

    _patch_garth_transport()
    token_path = _token_path()

    if token_path.exists():
        garmin = Garmin(is_cn=_is_cn())
        garmin.login(str(token_path))
        return garmin

    email = _email()
    password = _password()
    if not email or not password:
        raise RuntimeError(
            f"No Garmin tokens found at {token_path}; set GARMIN_EMAIL/GARMIN_USER_NAME "
            "and GARMIN_PASSWORD once to create the token cache."
        )

    garmin = Garmin(email, password, is_cn=_is_cn())
    garmin.login()
    token_path.mkdir(parents=True, exist_ok=True)
    garmin.garth.dump(str(token_path))
    return garmin


def _clean(d: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None}


def _activity_type(activity: dict[str, Any]) -> str | None:
    kind = activity.get("activityType") or activity.get("activityTypeDTO") or {}
    if isinstance(kind, dict):
        return cast(str | None, kind.get("typeKey"))
    return None


def _activity_date(value: Any) -> str | None:
    if not value:
        return None
    return str(value).replace(" ", "T").split("T", 1)[0]


def _duration_minutes(*values: Any) -> float | None:
    for value in values:
        if value is not None:
            return round(float(value) / 60, 1)
    return None


def _distance_km(value: Any) -> float | None:
    if value is None:
        return None
    return round(float(value) / 1000, 2)


def _source_fields() -> dict[str, object]:
    return {"source": _SOURCE, "provider": "garmin"}


def _haversine_m(a: dict[str, float], b: dict[str, float]) -> float:
    lat1 = radians(a["lat"])
    lon1 = radians(a["lon"])
    lat2 = radians(b["lat"])
    lon2 = radians(b["lon"])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 2 * _EARTH_RADIUS_M * atan2(sqrt(h), sqrt(1 - h))


def _bearing_degrees(a: dict[str, float], b: dict[str, float]) -> float:
    lat1 = radians(a["lat"])
    lat2 = radians(b["lat"])
    dlon = radians(b["lon"] - a["lon"])
    y = sin(dlon) * cos(lat2)
    x = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(dlon)
    return (degrees(atan2(y, x)) + 360) % 360


def _angle_delta(a: float, b: float) -> float:
    return abs((b - a + 180) % 360 - 180)


def garmin_list_activities(
    start_date: date | str,
    end_date: date | str,
    activity_type: str | None = None,
) -> list[dict[str, object]]:
    start = _as_date(start_date).isoformat()
    end = _as_date(end_date).isoformat()
    activities = _client().get_activities_by_date(start, end, activity_type or "")

    out: list[dict[str, object]] = []
    for activity in activities or []:
        out.append(
            cast(
                dict[str, object],
                _clean(
                    {
                        "activity_id": str(activity.get("activityId")),
                        "garmin_id": str(activity.get("activityId")),
                        "date": _activity_date(activity.get("startTimeLocal")),
                        "name": activity.get("activityName"),
                        "type": _activity_type(activity),
                        "duration_min": _duration_minutes(
                            activity.get("movingDuration"),
                            activity.get("duration"),
                            activity.get("elapsedDuration"),
                        ),
                        "distance_km": _distance_km(activity.get("distance")),
                        "avg_hr": activity.get("averageHR"),
                        "max_hr": activity.get("maxHR"),
                        "steps": activity.get("steps"),
                        "calories": activity.get("calories"),
                        **_source_fields(),
                    }
                ),
            )
        )
    return out


def _activity_details(activity_id: int) -> dict[str, Any]:
    try:
        details = _client().get_activity_details(  # cspell:ignore maxchart maxpoly sess dlat dlon
            activity_id,
            maxchart=500,
            maxpoly=_MAX_ROUTE_POINTS,
        )
    except Exception:
        return {}
    return cast(dict[str, Any], details or {})


def _metric_samples(details: dict[str, Any]) -> list[dict[str, object]]:
    if not details:
        return []
    descriptors = details.get("metricDescriptors") or []
    rows = details.get("activityDetailMetrics") or []
    if not descriptors or not rows:
        return []

    index_to_key = {d.get("metricsIndex"): d.get("key") for d in descriptors}
    samples: list[dict[str, object]] = []
    for row in rows:
        metrics = row.get("metrics") or []
        sample: dict[str, object] = {}
        for idx, value in enumerate(metrics):
            key = index_to_key.get(idx)
            if key in {
                "directTimestamp",
                "directSpeed",
                "directDoubleCadence",
                "directHeartRate",
                "directElevation",
            }:
                sample[key] = value
        if sample:
            samples.append(sample)
    return samples


def _route_points(details: dict[str, Any]) -> list[dict[str, object]]:
    geo = details.get("geoPolylineDTO") or {}
    polyline = geo.get("polyline") or []
    points: list[dict[str, object]] = []
    for point in polyline:
        if not point.get("valid", True):
            continue
        lat = point.get("lat")
        lon = point.get("lon")
        if not isinstance(lat, int | float) or not isinstance(lon, int | float):
            continue
        points.append(
            _clean(
                {
                    "lat": round(float(lat), 7),
                    "lon": round(float(lon), 7),
                    "timestamp": point.get("time"),
                    "speed": point.get("speed"),
                    "altitude": point.get("altitude"),
                    "distance_m": point.get("distanceInMeters"),
                    "timer_start": point.get("timerStart") or None,
                    "timer_stop": point.get("timerStop") or None,
                }
            )
        )
    return points


def _route_summary(points: list[dict[str, object]]) -> dict[str, object] | None:
    numeric_points = [
        {"lat": cast(float, p["lat"]), "lon": cast(float, p["lon"])}
        for p in points
        if isinstance(p.get("lat"), int | float) and isinstance(p.get("lon"), int | float)
    ]
    if not numeric_points:
        return None

    distance_m = sum(
        _haversine_m(numeric_points[idx - 1], numeric_points[idx])
        for idx in range(1, len(numeric_points))
    )
    min_lat = min(p["lat"] for p in numeric_points)
    max_lat = max(p["lat"] for p in numeric_points)
    min_lon = min(p["lon"] for p in numeric_points)
    max_lon = max(p["lon"] for p in numeric_points)
    start = numeric_points[0]
    end = numeric_points[-1]

    return {
        "point_count": len(numeric_points),
        "polyline_distance_km": round(distance_m / 1000, 2),
        "start": start,
        "end": end,
        "start_end_distance_m": round(_haversine_m(start, end), 1),
        "bounding_box": {
            "min_lat": round(min_lat, 7),
            "max_lat": round(max_lat, 7),
            "min_lon": round(min_lon, 7),
            "max_lon": round(max_lon, 7),
        },
    }


def garmin_get_activity(activity_id: str) -> dict[str, object]:
    activity = _client().get_activity(int(activity_id))
    summary = activity.get("summaryDTO", {}) if activity else {}
    activity_type = activity.get("activityTypeDTO", {}) if activity else {}
    metadata = activity.get("metadataDTO", {}) if activity else {}
    details = _activity_details(int(activity_id))
    samples = _metric_samples(details)
    route_points = _route_points(details)

    return cast(
        dict[str, object],
        _clean(
            {
                "activity_id": str(activity.get("activityId") if activity else activity_id),
                "garmin_id": str(activity.get("activityId") if activity else activity_id),
                "name": activity.get("activityName") if activity else None,
                "type": activity_type.get("typeKey"),
                "start_time_local": summary.get("startTimeLocal"),
                "duration_min": _duration_minutes(
                    summary.get("movingDuration"),
                    summary.get("duration"),
                    summary.get("elapsedDuration"),
                ),
                "distance_km": _distance_km(summary.get("distance")),
                "avg_hr": summary.get("averageHR"),
                "max_hr": summary.get("maxHR"),
                "calories": summary.get("calories"),
                "steps": summary.get("steps"),
                "lap_count": metadata.get("lapCount"),
                "metric_samples": samples or None,
                "route_summary": _route_summary(route_points),
                "route_points": route_points or None,
                **_source_fields(),
            }
        ),
    )


def _sleep_hours_from_stats(stats: dict[str, Any]) -> float | None:
    seconds = stats.get("sleepingSeconds")
    if seconds is None:
        return None
    return round(float(seconds) / 3600, 2)


def _sleep_hours_from_sleep_data(sleep_data: dict[str, Any]) -> float | None:
    daily_sleep = sleep_data.get("dailySleepDTO") or {}
    for key in ("sleepTimeSeconds", "sleepSeconds", "durationInSeconds"):
        seconds = daily_sleep.get(key)
        if seconds is not None:
            return round(float(seconds) / 3600, 2)
    return None


def garmin_get_daily_summary(date: date | str) -> dict[str, object]:  # noqa: A002
    day = _as_date(date).isoformat()
    client = _client()
    stats = client.get_stats(day) or {}

    sleep_hours = _sleep_hours_from_stats(stats)
    if sleep_hours is None:
        try:
            sleep_hours = _sleep_hours_from_sleep_data(client.get_sleep_data(day) or {})
        except Exception:
            sleep_hours = None

    return cast(
        dict[str, object],
        _clean(
            {
                "date": stats.get("calendarDate") or day,
                "steps": stats.get("totalSteps"),
                "sleep_hours": sleep_hours,
                "stress_avg": stats.get("averageStressLevel"),
                "body_battery_end": stats.get("bodyBatteryMostRecentValue"),
                "body_battery_lowest": stats.get("bodyBatteryLowestValue"),
                "body_battery_highest": stats.get("bodyBatteryHighestValue"),
                "resting_heart_rate": stats.get("restingHeartRate"),
                "distance_km": _distance_km(stats.get("totalDistanceMeters")),
                "active_calories": stats.get("activeKilocalories"),
                **_source_fields(),
            }
        ),
    )


def _number(value: object | None) -> float:
    return float(value) if isinstance(value, int | float) else 0.0


def garmin_get_user_stats(
    start_date: date | str,
    end_date: date | str,
) -> dict[str, object]:
    start = _as_date(start_date)
    end = _as_date(end_date)
    activities = garmin_list_activities(start, end)
    by_type: dict[str, int] = {}
    for activity in activities:
        kind = str(activity.get("type", "unknown"))
        by_type[kind] = by_type.get(kind, 0) + 1
    return {
        "period": {
            "start": start.isoformat(),
            "end": end.isoformat(),
            "days": (end - start).days + 1,
        },
        "activity_count": len(activities),
        "total_minutes": round(sum(_number(a.get("duration_min")) for a in activities), 1),
        "total_distance_km": round(sum(_number(a.get("distance_km")) for a in activities), 2),
        "by_type": by_type,
        **_source_fields(),
    }


def _float_values(rows: list[dict[str, object]], key: str) -> list[float]:
    values: list[float] = []
    for row in rows:
        value = row.get(key)
        if isinstance(value, int | float):
            values.append(float(value))
    return values


def _elapsed_minutes(row: dict[str, object], timestamp_key: str, start_ms: float) -> float | None:
    timestamp = row.get(timestamp_key)
    if not isinstance(timestamp, int | float):
        return None
    return (float(timestamp) - start_ms) / 60_000


def _route_distance_km(points: list[dict[str, object]]) -> float:
    numeric_points = _numeric_route_points(points)
    return round(
        sum(
            _haversine_m(numeric_points[idx - 1], numeric_points[idx])
            for idx in range(1, len(numeric_points))
        )
        / 1000,
        3,
    )


def _turn_count(points: list[dict[str, object]]) -> int:
    numeric_points = _numeric_route_points(points)
    if len(numeric_points) < 3:
        return 0
    count = 0
    prev_bearing = _bearing_degrees(numeric_points[0], numeric_points[1])
    for idx in range(2, len(numeric_points)):
        bearing = _bearing_degrees(numeric_points[idx - 1], numeric_points[idx])
        if _angle_delta(prev_bearing, bearing) >= 45:
            count += 1
        prev_bearing = bearing
    return count


def _numeric_route_points(points: list[dict[str, object]]) -> list[dict[str, float]]:
    numeric_points: list[dict[str, float]] = []
    for point in points:
        lat = point.get("lat")
        lon = point.get("lon")
        if isinstance(lat, int | float) and isinstance(lon, int | float):
            numeric_points.append({"lat": float(lat), "lon": float(lon)})
    return numeric_points


def _segment_summary(
    *,
    label: str,
    index: int,
    start_minute: float,
    end_minute: float,
    metric_rows: list[dict[str, object]],
    route_rows: list[dict[str, object]],
    start_ms: float,
) -> dict[str, object]:
    metrics = [
        row
        for row in metric_rows
        if (elapsed := _elapsed_minutes(row, "directTimestamp", start_ms)) is not None
        and start_minute <= elapsed < end_minute
    ]
    route_points = [
        row
        for row in route_rows
        if (elapsed := _elapsed_minutes(row, "timestamp", start_ms)) is not None
        and start_minute <= elapsed < end_minute
    ]
    speeds = [value for value in _float_values(metrics, "directSpeed") if value > 0]
    cadences = [value for value in _float_values(metrics, "directDoubleCadence") if value > 0]
    elevations = _float_values(metrics, "directElevation")
    stop_samples = [value for value in _float_values(metrics, "directSpeed") if value <= 0.2]
    distance_km = _route_distance_km(route_points)
    turns = _turn_count(route_points)
    return _clean(
        {
            "index": index,
            "label": label,
            "start_minute": round(start_minute, 1),
            "end_minute": round(end_minute, 1),
            "sample_count": len(metrics),
            "route_point_count": len(route_points),
            "avg_speed_mps": round(mean(speeds), 3) if speeds else None,
            "avg_cadence_spm": round(mean(cadences), 1) if cadences else None,
            "elevation_delta_m": round(elevations[-1] - elevations[0], 1)
            if len(elevations) >= 2
            else None,
            "route_distance_km": distance_km if route_points else None,
            "turn_count": turns,
            "turns_per_km": round(turns / distance_km, 1) if distance_km else None,
            "stop_sample_count": len(stop_samples),
        }
    )


def _average_segment_value(segments: list[dict[str, object]], label: str, key: str) -> float | None:
    values: list[float] = []
    for segment in segments:
        value = segment.get(key)
        if segment.get("label") == label and isinstance(value, int | float):
            values.append(float(value))
    return round(mean(values), 3) if values else None


def _spread_m(points: list[dict[str, float]]) -> float | None:
    if not points:
        return None
    reference = points[0]
    return round(max(_haversine_m(reference, point) for point in points), 1)


def _duration_value(*values: object) -> float:
    for value in values:
        if isinstance(value, int | float):
            return float(value)
    return 0.0


def _route_endpoint(summary: dict[str, object], key: str) -> dict[str, float] | None:
    value = summary.get(key)
    if not isinstance(value, dict):
        return None
    lat = value.get("lat")
    lon = value.get("lon")
    if isinstance(lat, int | float) and isinstance(lon, int | float):
        return {"lat": float(lat), "lon": float(lon)}
    return None


def garmin_route_aware_iwt_analysis(
    start_date: date | str,
    end_date: date | str,
    normal_minutes: int = 3,
    fast_minutes: int = 3,
    repetitions: int = 5,
    activity_type: str = "walking",
) -> dict[str, object]:
    activities = garmin_list_activities(start_date, end_date, activity_type)
    walks = [activity for activity in activities if activity.get("type") == activity_type]
    segment_minutes = [normal_minutes, fast_minutes] * repetitions
    iwt_minutes = sum(segment_minutes)
    analyses: list[dict[str, object]] = []

    for activity in walks:
        detail = garmin_get_activity(str(activity["activity_id"]))
        metric_samples = cast(list[dict[str, object]], detail.get("metric_samples") or [])
        route_points = cast(list[dict[str, object]], detail.get("route_points") or [])
        timestamps = _float_values(metric_samples, "directTimestamp")
        if not timestamps:
            analyses.append(
                {
                    "activity_id": activity["activity_id"],
                    "date": activity.get("date"),
                    "name": activity.get("name"),
                    "status": "no_metric_samples",
                }
            )
            continue

        start_ms = min(timestamps)
        segments: list[dict[str, object]] = []
        cursor = 0.0
        for idx, minutes in enumerate(segment_minutes, start=1):
            label = "normal" if idx % 2 else "fast"
            segments.append(
                _segment_summary(
                    label=label,
                    index=idx,
                    start_minute=cursor,
                    end_minute=cursor + minutes,
                    metric_rows=metric_samples,
                    route_rows=route_points,
                    start_ms=start_ms,
                )
            )
            cursor += minutes

        relaxed_segment = _segment_summary(
            label="relaxed",
            index=len(segments) + 1,
            start_minute=float(iwt_minutes),
            end_minute=_duration_value(
                activity.get("duration_min"),
                detail.get("duration_min"),
                iwt_minutes,
            ),
            metric_rows=metric_samples,
            route_rows=route_points,
            start_ms=start_ms,
        )
        normal_speed = _average_segment_value(segments, "normal", "avg_speed_mps")
        fast_speed = _average_segment_value(segments, "fast", "avg_speed_mps")
        normal_cadence = _average_segment_value(segments, "normal", "avg_cadence_spm")
        fast_cadence = _average_segment_value(segments, "fast", "avg_cadence_spm")
        relaxed_speed = (
            float(relaxed_value)
            if isinstance((relaxed_value := relaxed_segment.get("avg_speed_mps")), int | float)
            else None
        )
        fast_lift_pct = (
            round((fast_speed / normal_speed - 1) * 100, 1)
            if fast_speed is not None and normal_speed
            else None
        )
        relaxed_drop_pct = (
            round((1 - relaxed_speed / fast_speed) * 100, 1)
            if relaxed_speed is not None and fast_speed
            else None
        )

        route_summary = cast(dict[str, object] | None, detail.get("route_summary"))
        analyses.append(
            _clean(
                {
                    "activity_id": activity["activity_id"],
                    "date": activity.get("date"),
                    "name": activity.get("name"),
                    "duration_min": activity.get("duration_min"),
                    "distance_km": activity.get("distance_km"),
                    "route_summary": route_summary,
                    "segments": segments,
                    "relaxed_segment": relaxed_segment,
                    "normal_speed_mps": normal_speed,
                    "fast_speed_mps": fast_speed,
                    "fast_vs_normal_speed_lift_pct": fast_lift_pct,
                    "normal_cadence_spm": normal_cadence,
                    "fast_cadence_spm": fast_cadence,
                    "fast_vs_normal_cadence_lift_pct": (
                        round((fast_cadence / normal_cadence - 1) * 100, 1)
                        if fast_cadence is not None and normal_cadence
                        else None
                    ),
                    "relaxed_speed_mps": relaxed_speed,
                    "relaxed_vs_fast_speed_drop_pct": relaxed_drop_pct,
                    "iwt_pattern_present": bool(
                        fast_lift_pct is not None
                        and fast_lift_pct >= 10
                        and relaxed_drop_pct is not None
                        and relaxed_drop_pct >= 10
                    ),
                }
            )
        )

    route_summaries = [
        cast(dict[str, object], analysis.get("route_summary"))
        for analysis in analyses
        if isinstance(analysis.get("route_summary"), dict)
    ]
    starts = [
        endpoint for summary in route_summaries if (endpoint := _route_endpoint(summary, "start"))
    ]
    ends = [
        endpoint for summary in route_summaries if (endpoint := _route_endpoint(summary, "end"))
    ]
    distances: list[float] = []
    for summary in route_summaries:
        distance = summary.get("polyline_distance_km")
        if isinstance(distance, int | float):
            distances.append(float(distance))
    present_count = sum(1 for analysis in analyses if analysis.get("iwt_pattern_present") is True)

    return {
        "period": {
            "start": _as_date(start_date).isoformat(),
            "end": _as_date(end_date).isoformat(),
        },
        "intended_pattern": {
            "normal_minutes": normal_minutes,
            "fast_minutes": fast_minutes,
            "repetitions": repetitions,
            "iwt_minutes": iwt_minutes,
            "post_iwt_expectation": "relaxed walking",
        },
        "activity_count": len(analyses),
        "iwt_pattern_present_count": present_count,
        "route_comparability": {
            "with_gps_count": len(route_summaries),
            "start_spread_m": _spread_m(starts),
            "end_spread_m": _spread_m(ends),
            "polyline_distance_min_km": round(min(distances), 2) if distances else None,
            "polyline_distance_max_km": round(max(distances), 2) if distances else None,
            "same_route_likely": bool(
                route_summaries
                and _spread_m(starts) is not None
                and _spread_m(ends) is not None
                and cast(float, _spread_m(starts)) <= 150
                and cast(float, _spread_m(ends)) <= 150
                and distances
                and max(distances) - min(distances) <= 0.6
            ),
        },
        "activities": analyses,
        **_source_fields(),
    }
