"""Autonomic-loop status dashboard: gather counts + ages, render self-contained HTML."""

from __future__ import annotations

from pathlib import Path

from practice_theory_implementation import registry
from practice_theory_implementation.materials import status_dashboard as sd
from practice_theory_implementation.trail import EnactmentStore


def _seed(store: EnactmentStore) -> None:
    # One judge_inbox item: a closed somatic enactment with a step, routed.
    som = store.open_enactment("correspondent", mode="somatic")
    store.record_step(
        enactment_id=som,
        affordance_id="a",
        material_name="m",
        arguments={},
        result={"ok": True},
        started_at="2026-06-04T00:00:00+00:00",
        completed_at="2026-06-04T00:00:01+00:00",
        duration_ms=1,
    )
    store.close_enactment(som)
    store.route_closed_enactments_to_judge_inbox()
    # One smoother_inbox item: a recorded Friction, routed.
    store.record_friction(
        observing_enactment_id="judge:obs",
        target_enactment_id="t",
        kind="narrow_engagement",
        content="c",
    )
    store.route_friction_to_smoother_inbox()
    # One open enactment.
    store.open_enactment("judge", mode="autonomic")


def test_humanize_age_buckets() -> None:
    assert sd._humanize_age(5) == "5s"
    assert sd._humanize_age(90) == "1m 30s"
    assert sd._humanize_age(3 * 3600 + 200) == "3h 3m"
    assert sd._humanize_age(2 * 86400 + 3600) == "2d 1h"


def test_gather_reports_counts_and_open_enactments(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "trail.db"
    monkeypatch.setenv("PRACTICE_TRAIL_PATH", str(path))
    store = EnactmentStore(path)
    _seed(store)
    store.close()

    status = sd.gather_dashboard_status()

    assert status["judge_inbox"] == 1
    assert status["smoother_inbox"] == 1
    assert status["unaddressed_friction"] == 1
    assert status["open_enactment_count"] == 1
    assert len(status["open_enactments"]) == 1
    row = status["open_enactments"][0]
    assert row["practice_id"] == "judge"
    assert row["severity"] == "ok"  # just opened
    assert row["age_seconds"] >= 0


def test_render_html_contains_metrics_and_refresh() -> None:
    status = {
        "judge_inbox": 2,
        "smoother_inbox": 0,
        "open_enactment_count": 1,
        "unaddressed_friction": 5,
        "open_enactments": [
            {
                "id": "abcd1234-5678",
                "practice_id": "judge",
                "mode": "autonomic",
                "age_human": "22m 10s",
                "severity": "stale",
            }
        ],
        "generated_at": "2026-06-05T07:00:00+00:00",
    }
    doc = sd.render_dashboard_html(status, refresh_seconds=15)

    assert "<!doctype html>" in doc
    assert 'http-equiv="refresh" content="15"' in doc
    assert "Judge inbox" in doc and ">2<" in doc
    assert "Unaddressed frictions" in doc and ">5<" in doc
    assert "abcd1234" in doc and "22m 10s" in doc
    assert 'class="stale"' in doc  # the stale open enactment is flagged


def test_render_html_empty_state() -> None:
    status = {
        "judge_inbox": 0,
        "smoother_inbox": 0,
        "open_enactment_count": 0,
        "unaddressed_friction": 0,
        "open_enactments": [],
        "generated_at": "2026-06-05T07:00:00+00:00",
    }
    doc = sd.render_dashboard_html(status)
    assert "No open enactments" in doc


def test_render_status_dashboard_writes_file(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PRACTICE_TRAIL_PATH", str(tmp_path / "trail.db"))
    store = EnactmentStore(tmp_path / "trail.db")
    _seed(store)
    store.close()

    out = tmp_path / "status.html"
    result = sd.render_status_dashboard(refresh_seconds=10, write_path=str(out))

    assert out.exists()
    assert "<!doctype html>" in out.read_text(encoding="utf-8")
    assert result["judge_inbox"] == 1 and result["open_enactment_count"] == 1
    assert result["path"] == str(out)
    assert result["live_url"].startswith("http://127.0.0.1:")


def test_affordance_is_registered() -> None:
    fn = registry.resolve("render_status_dashboard")
    assert callable(fn)
