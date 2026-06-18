from __future__ import annotations

from datetime import UTC, datetime

import pytest

from practice_theory_implementation.material_surfaces import MATERIAL_SURFACES
from practice_theory_implementation.materials import paper_fund
from practice_theory_implementation.projection import project
from practice_theory_implementation.registry import FUNCTIONS
from practice_theory_implementation.substrate_loader import load_substrate
from practice_theory_implementation.trail import TRAIL_PATH_ENV, EnactmentStore


def test_stock_investor_projects_and_records_setup() -> None:
    loaded = load_substrate(material_surfaces=MATERIAL_SURFACES)
    assert loaded.errors == []

    practice = project(
        loaded.bundles["stock_investor"],
        loaded.substrate,
        FUNCTIONS,
        engagement=None,
    )

    affordance_ids = {aff.id for aff in practice.affordances}
    assert {
        "define_fund",
        "read_fund_state",
        "read_fund_follow_ups",
        "read_live_market_snapshot",
        "record_market_evidence",
        "record_investment_thesis",
        "record_trade_decision",
        "buy_stock",
        "sell_stock",
        "record_fund_follow_ups",
        "value_fund",
        "review_investor_practice",
    } <= affordance_ids

    assert any(
        understanding.id == "und_market_regimes_and_stock_types"
        for understanding in practice.understanding
    )
    assert any(
        rule.id == "rule_stock_investor_live_market_snapshot"
        for rule in practice.rules
    )
    assert any(
        rule.id == "rule_stock_investor_follow_up_register" for rule in practice.rules
    )
    assert any(
        rule.id == "rule_stock_investor_read_state_before_decision"
        for rule in practice.rules
    )

    result = practice.invoke(
        affordance_id="define_fund",
        material_name="fund_record_setup",
        arguments={
            "fund_id": "test_fund",
            "as_of": "2026-06-17T00:00:00+09:00",
            "starting_capital": 100000,
            "currency": "USD",
            "strategy": "Quality investor fund.",
            "benchmark": "SPY",
        },
    )

    assert result == {
        "arguments": {
            "fund_id": "test_fund",
            "as_of": "2026-06-17T00:00:00+09:00",
            "starting_capital": 100000,
            "currency": "USD",
            "strategy": "Quality investor fund.",
            "benchmark": "SPY",
        }
    }


def test_stock_order_materials_are_mocked_behind_neutral_affordances() -> None:
    loaded = load_substrate(material_surfaces=MATERIAL_SURFACES)
    assert loaded.errors == []

    practice = project(
        loaded.bundles["stock_investor"],
        loaded.substrate,
        FUNCTIONS,
        engagement=None,
    )

    result = practice.invoke(
        affordance_id="buy_stock",
        material_name="brokerage_submit_buy_order",
        arguments={
            "fund_id": "test_fund",
            "symbol": "BRK-B",
            "quantity": 1,
            "order_type": "market",
            "time_in_force": "day",
            "decision_id": "test-decision",
            "as_of": "2026-06-17T00:00:00+09:00",
            "estimated_price": 491.28,
        },
    )

    assert isinstance(result, dict)
    assert result["side"] == "buy"
    assert result["status"] == "filled"
    assert result["external_broker_order_submitted"] is False


def test_fund_follow_up_register_reads_prior_trail_records(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    trail_path = tmp_path / "trail.db"
    monkeypatch.setenv(TRAIL_PATH_ENV, str(trail_path))
    trail = EnactmentStore(trail_path)
    try:
        enactment_id = trail.open_enactment("stock_investor")
        now = datetime.now(UTC).isoformat(timespec="seconds")
        trail.record_step(
            enactment_id=enactment_id,
            affordance_id="record_fund_follow_ups",
            material_name="fund_record_follow_up_register",
            arguments={
                "fund_id": "test_fund",
                "as_of": now,
                "decision_id": "decision-1",
                "open_questions": ["Review latest filing."],
                "review_triggers": ["Position reaches 7.5%."],
            },
            result={"ok": True},
            started_at=now,
            completed_at=now,
            duration_ms=1,
        )
        trail.close_enactment(enactment_id)
    finally:
        trail.close()

    result = paper_fund.fund_read_follow_up_register("test_fund")

    assert result["fund_id"] == "test_fund"
    assert result["records"][0]["decision_id"] == "decision-1"
    assert result["records"][0]["open_questions"] == ["Review latest filing."]
    assert result["records"][0]["review_triggers"] == ["Position reaches 7.5%."]


def test_fund_state_reads_prior_mandate_order_and_valuation(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    trail_path = tmp_path / "trail.db"
    monkeypatch.setenv(TRAIL_PATH_ENV, str(trail_path))
    trail = EnactmentStore(trail_path)
    try:
        enactment_id = trail.open_enactment("stock_investor")
        now = datetime.now(UTC).isoformat(timespec="seconds")
        trail.record_step(
            enactment_id=enactment_id,
            affordance_id="define_fund",
            material_name="fund_record_setup",
            arguments={
                "fund_id": "test_fund",
                "as_of": now,
                "starting_capital": 100000,
                "currency": "USD",
                "strategy": "Quality investor fund.",
                "benchmark": "SPY",
            },
            result={"ok": True},
            started_at=now,
            completed_at=now,
            duration_ms=1,
        )
        trail.record_step(
            enactment_id=enactment_id,
            affordance_id="buy_stock",
            material_name="brokerage_submit_buy_order",
            arguments={
                "fund_id": "test_fund",
                "symbol": "BRK-B",
                "quantity": 10,
                "order_type": "market",
                "time_in_force": "day",
                "decision_id": "decision-1",
                "as_of": now,
                "estimated_price": 491.28,
            },
            result={
                "fund_id": "test_fund",
                "symbol": "BRK-B",
                "side": "buy",
                "filled_quantity": 10,
                "filled_price": 491.28,
                "status": "filled",
                "external_broker_order_submitted": False,
            },
            started_at=now,
            completed_at=now,
            duration_ms=1,
        )
        trail.record_step(
            enactment_id=enactment_id,
            affordance_id="value_fund",
            material_name="fund_record_valuation",
            arguments={
                "fund_id": "test_fund",
                "as_of": now,
                "cash": 95087.2,
                "currency": "USD",
                "positions": [
                    {
                        "symbol": "BRK-B",
                        "quantity": 10,
                        "price": 491.28,
                        "market_value": 4912.8,
                        "position_pct": 4.9128,
                        "price_as_of": now,
                    }
                ],
                "portfolio_value": 100000,
                "starting_capital": 100000,
                "absolute_return_pct": 0,
                "benchmark_symbol": "SPY",
            },
            result={"ok": True},
            started_at=now,
            completed_at=now,
            duration_ms=1,
        )
        trail.close_enactment(enactment_id)
    finally:
        trail.close()

    result = paper_fund.fund_read_state("test_fund")

    assert result["mandate"]["arguments"]["benchmark"] == "SPY"
    assert result["cash"] == 95087.2
    assert result["positions"] == [{"symbol": "BRK-B", "quantity": 10.0}]
    assert result["orders"][0]["result"]["external_broker_order_submitted"] is False
    assert result["latest_valuation"]["arguments"]["portfolio_value"] == 100000


def test_fund_state_warns_on_thesis_without_position(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A 'holding' thesis with no reconstructed position is drift and must warn."""
    trail_path = tmp_path / "trail.db"
    monkeypatch.setenv(TRAIL_PATH_ENV, str(trail_path))
    trail = EnactmentStore(trail_path)
    try:
        enactment_id = trail.open_enactment("stock_investor")
        now = datetime.now(UTC).isoformat(timespec="seconds")
        trail.record_step(
            enactment_id=enactment_id,
            affordance_id="define_fund",
            material_name="fund_record_setup",
            arguments={
                "fund_id": "drift_fund",
                "as_of": now,
                "starting_capital": 100000,
                "currency": "USD",
                "strategy": "Quality investor fund.",
                "benchmark": "SPY",
            },
            result={"ok": True},
            started_at=now,
            completed_at=now,
            duration_ms=1,
        )
        # A thesis claims SPY is held, but no buy order was ever submitted, so
        # no SPY position reconstructs from the order ledger.
        trail.record_step(
            enactment_id=enactment_id,
            affordance_id="record_investment_thesis",
            material_name="fund_record_thesis",
            arguments={
                "fund_id": "drift_fund",
                "symbol": "SPY",
                "as_of": now,
                "status": "holding",
                "facts": ["broad market exposure"],
                "assumptions": [],
                "risk_view": "market drawdown",
            },
            result={"ok": True},
            started_at=now,
            completed_at=now,
            duration_ms=1,
        )
        trail.close_enactment(enactment_id)
    finally:
        trail.close()

    result = paper_fund.fund_read_state("drift_fund")

    assert result["positions"] == []
    drift = [w for w in result["warnings"] if "Thesis/position drift" in w]
    assert any("SPY" in w and "holding" in w for w in drift), result["warnings"]


def test_fund_state_warns_on_decision_without_matching_order(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A buy/sell decision with no matching executed order is reconciliation drift."""
    trail_path = tmp_path / "trail.db"
    monkeypatch.setenv(TRAIL_PATH_ENV, str(trail_path))
    trail = EnactmentStore(trail_path)
    try:
        enactment_id = trail.open_enactment("stock_investor")
        now = datetime.now(UTC).isoformat(timespec="seconds")
        trail.record_step(
            enactment_id=enactment_id,
            affordance_id="define_fund",
            material_name="fund_record_setup",
            arguments={
                "fund_id": "exec_fund",
                "as_of": now,
                "starting_capital": 100000,
                "currency": "USD",
                "strategy": "Quality investor fund.",
                "benchmark": "SPY",
            },
            result={"ok": True},
            started_at=now,
            completed_at=now,
            duration_ms=1,
        )
        # A buy decision that never produced an order.
        trail.record_step(
            enactment_id=enactment_id,
            affordance_id="record_trade_decision",
            material_name="fund_record_trade_decision",
            arguments={
                "fund_id": "exec_fund",
                "decision_id": "dec-unexecuted",
                "as_of": now,
                "symbol": "SPY",
                "action": "buy",
            },
            result={"ok": True},
            started_at=now,
            completed_at=now,
            duration_ms=1,
        )
        # A buy decision that did produce a matching order (same decision_id).
        trail.record_step(
            enactment_id=enactment_id,
            affordance_id="record_trade_decision",
            material_name="fund_record_trade_decision",
            arguments={
                "fund_id": "exec_fund",
                "decision_id": "dec-executed",
                "as_of": now,
                "symbol": "BRK-B",
                "action": "buy",
            },
            result={"ok": True},
            started_at=now,
            completed_at=now,
            duration_ms=1,
        )
        trail.record_step(
            enactment_id=enactment_id,
            affordance_id="buy_stock",
            material_name="brokerage_submit_buy_order",
            arguments={
                "fund_id": "exec_fund",
                "symbol": "BRK-B",
                "quantity": 1,
                "order_type": "market",
                "time_in_force": "day",
                "decision_id": "dec-executed",
                "as_of": now,
                "estimated_price": 491.28,
            },
            result={
                "fund_id": "exec_fund",
                "symbol": "BRK-B",
                "side": "buy",
                "filled_quantity": 1,
                "filled_price": 491.28,
                "status": "filled",
                "external_broker_order_submitted": False,
            },
            started_at=now,
            completed_at=now,
            duration_ms=1,
        )
        trail.close_enactment(enactment_id)
    finally:
        trail.close()

    result = paper_fund.fund_read_state("exec_fund")

    drift = [w for w in result["warnings"] if "Decision/order drift" in w]
    assert len(drift) == 1, result["warnings"]
    assert "dec-unexecuted" in drift[0]
    # The executed decision must not be flagged.
    assert "dec-executed" not in drift[0]


def test_somatic_scheduler_projects_as_autonomic_boundary_practice() -> None:
    loaded = load_substrate(material_surfaces=MATERIAL_SURFACES)
    assert loaded.errors == []

    bundle = loaded.bundles["somatic_scheduler"]
    assert bundle.mode == "autonomic"

    practice = project(bundle, loaded.substrate, FUNCTIONS, engagement=None)

    assert practice.id == "somatic_scheduler"
    assert practice.affordances == ()
    assert any(rule.id == "rule_somatic_scheduler_target_authority" for rule in practice.rules)
