"""Fund materials that create durable local artifacts."""

from __future__ import annotations

import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from practice_theory_implementation.trail import EnactmentStore

REPORT_DIR = Path("data/paper_stock_reports")
INVESTOR_PRACTICE_IDS = ("stock_investor", "paper_stock_investor")

# Operator-authorized decision reconciliations. This append-only JSONL ledger
# retires a trade decision that the trail recorded but never executed — a
# starter intent re-recorded under a settled decision_id, leaving the original
# as superseded drift. It is kept OUT of the immutable trail (which records only
# what the practitioner actually did) and read alongside it, so the
# deterministic state reconstruction stops re-flagging a decision a human has
# already resolved. Override the path with FUND_RECONCILIATION_PATH (tests).
RECONCILIATION_PATH_ENV = "FUND_RECONCILIATION_PATH"
DEFAULT_RECONCILIATION_PATH = Path("data/fund_decision_reconciliations.jsonl")


def _safe_stem(value: object) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[^a-z0-9._-]+", "-", text)
    text = text.strip(".-")
    return text or "paper-stock-report"


def _lines(items: object) -> list[str]:
    if not isinstance(items, list):
        return []
    out: list[str] = []
    for item in items:
        text = str(item).strip()
        if text:
            out.append(text)
    return out


def _section(title: str, body: object) -> str:
    text = str(body or "").strip()
    if not text:
        return ""
    return f"\n## {title}\n\n{text}\n"


def _bullet_section(title: str, items: object) -> str:
    lines = _lines(items)
    if not lines:
        return ""
    body = "\n".join(f"- {line}" for line in lines)
    return f"\n## {title}\n\n{body}\n"


def _json_object(text: str) -> dict[str, Any] | None:
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def _num(value: object, default: float = 0.0) -> float:
    if isinstance(value, int | float):
        return float(value)
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return default


def _bounded(value: int, minimum: int = 1, maximum: int = 100) -> int:
    return max(minimum, min(value, maximum))


def paper_fund_write_decision_report(
    fund_id: str,
    report_id: str,
    as_of: str,
    decision_id: str,
    action: str,
    title: str,
    summary: str,
    decision_rationale: str,
    risk_basis: str,
    *,
    symbol: str | None = None,
    market_regime: str | None = None,
    action_recorded: str | None = None,
    expected_portfolio_effect: str | None = None,
    evidence_basis: list[str] | None = None,
    open_questions: list[str] | None = None,
    next_review_triggers: list[str] | None = None,
    source_citations: list[str] | None = None,
) -> dict[str, Any]:
    """Write a concise Markdown decision report for a fund action."""
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    stem = _safe_stem(report_id or decision_id)
    path = REPORT_DIR / f"{stem}.md"
    created_at = datetime.now(UTC).isoformat(timespec="seconds")
    heading = title.strip() or f"{fund_id} decision report"
    target = f"{symbol} / {action}" if symbol else action
    markdown = (
        f"# {heading}\n\n"
        f"- Fund: `{fund_id}`\n"
        f"- Decision: `{decision_id}`\n"
        f"- Action: `{target}`\n"
        f"- As of: `{as_of}`\n"
        f"- Created at: `{created_at}`\n"
        + _section("Summary", summary)
        + _section("Market Regime", market_regime)
        + _bullet_section("Evidence Basis", evidence_basis)
        + _section("Decision Rationale", decision_rationale)
        + _section("Risk Basis", risk_basis)
        + _section("Action Recorded", action_recorded)
        + _section("Expected Portfolio Effect", expected_portfolio_effect)
        + _bullet_section("Open Questions", open_questions)
        + _bullet_section("Next Review Triggers", next_review_triggers)
        + _bullet_section("Sources", source_citations)
    )
    path.write_text(markdown, encoding="utf-8")
    return {
        "report_path": str(path),
        "fund_id": fund_id,
        "decision_id": decision_id,
        "action": action,
        "symbol": symbol,
        "as_of": as_of,
        "created_at": created_at,
        "open_questions": open_questions or [],
        "next_review_triggers": next_review_triggers or [],
    }


def fund_write_decision_report(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return paper_fund_write_decision_report(*args, **kwargs)


def _brokerage_order(
    *,
    side: str,
    fund_id: str,
    symbol: str,
    quantity: float,
    order_type: str,
    time_in_force: str,
    decision_id: str,
    as_of: str,
    limit_price: float | None = None,
    estimated_price: float | None = None,
    rationale: str | None = None,
) -> dict[str, Any]:
    created_at = datetime.now(UTC).isoformat(timespec="seconds")
    order_key = _safe_stem(f"{fund_id}-{decision_id}-{side}-{symbol}-{created_at}")
    return {
        "order_id": f"practice-{order_key}",
        "fund_id": fund_id,
        "symbol": symbol,
        "side": side,
        "quantity": quantity,
        "order_type": order_type,
        "time_in_force": time_in_force,
        "decision_id": decision_id,
        "as_of": as_of,
        "limit_price": limit_price,
        "estimated_price": estimated_price,
        "status": "filled",
        "filled_quantity": quantity,
        "filled_price": estimated_price if estimated_price is not None else limit_price,
        "created_at": created_at,
        "rationale": rationale,
        "external_broker_order_submitted": False,
    }


def brokerage_submit_buy_order(
    fund_id: str,
    symbol: str,
    quantity: float,
    order_type: str,
    time_in_force: str,
    decision_id: str,
    as_of: str,
    *,
    limit_price: float | None = None,
    estimated_price: float | None = None,
    rationale: str | None = None,
) -> dict[str, Any]:
    return _brokerage_order(
        side="buy",
        fund_id=fund_id,
        symbol=symbol,
        quantity=quantity,
        order_type=order_type,
        time_in_force=time_in_force,
        decision_id=decision_id,
        as_of=as_of,
        limit_price=limit_price,
        estimated_price=estimated_price,
        rationale=rationale,
    )


def brokerage_submit_sell_order(
    fund_id: str,
    symbol: str,
    quantity: float,
    order_type: str,
    time_in_force: str,
    decision_id: str,
    as_of: str,
    *,
    limit_price: float | None = None,
    estimated_price: float | None = None,
    rationale: str | None = None,
) -> dict[str, Any]:
    return _brokerage_order(
        side="sell",
        fund_id=fund_id,
        symbol=symbol,
        quantity=quantity,
        order_type=order_type,
        time_in_force=time_in_force,
        decision_id=decision_id,
        as_of=as_of,
        limit_price=limit_price,
        estimated_price=estimated_price,
        rationale=rationale,
    )


def fund_record_follow_up_register(
    fund_id: str,
    as_of: str,
    decision_id: str,
    *,
    open_questions: list[str] | None = None,
    review_triggers: list[str] | None = None,
    prior_items_addressed: list[str] | None = None,
    carried_forward: list[str] | None = None,
    next_review_intent: str | None = None,
) -> dict[str, Any]:
    """Record structured follow-ups created or carried by a fund decision."""
    return {
        "fund_id": fund_id,
        "as_of": as_of,
        "decision_id": decision_id,
        "open_questions": open_questions or [],
        "review_triggers": review_triggers or [],
        "prior_items_addressed": prior_items_addressed or [],
        "carried_forward": carried_forward or [],
        "next_review_intent": next_review_intent,
        "recorded_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }


def fund_read_follow_up_register(
    fund_id: str,
    *,
    limit: int = 10,
    include_closed: bool = False,
) -> dict[str, Any]:
    """Read recent structured follow-up records for a fund from the trail."""
    trail = EnactmentStore()
    try:
        enactments = []
        for practice_id in INVESTOR_PRACTICE_IDS:
            enactments.extend(
                trail.recent_enactments(
                    limit=max(1, min(limit, 50)), practice_id=practice_id
                )
            )
        enactments.sort(key=lambda row: row.opened_at, reverse=True)
        records: list[dict[str, Any]] = []
        for enactment in enactments:
            for step in trail.steps_for(enactment.id):
                if step.material_name != "fund_record_follow_up_register":
                    continue
                try:
                    args = json.loads(step.arguments_json)
                except json.JSONDecodeError:
                    continue
                if args.get("fund_id") != fund_id:
                    continue
                record = {
                    "step_id": step.id,
                    "enactment_id": step.enactment_id,
                    "as_of": args.get("as_of"),
                    "decision_id": args.get("decision_id"),
                    "open_questions": args.get("open_questions") or [],
                    "review_triggers": args.get("review_triggers") or [],
                    "prior_items_addressed": args.get("prior_items_addressed") or [],
                    "carried_forward": args.get("carried_forward") or [],
                    "next_review_intent": args.get("next_review_intent"),
                    "recorded_at": step.started_at,
                }
                if include_closed or record["open_questions"] or record["review_triggers"]:
                    records.append(record)
        return {
            "fund_id": fund_id,
            "records": records[: max(1, min(limit, 50))],
            "source": "trail.steps.fund_record_follow_up_register",
            "read_at": datetime.now(UTC).isoformat(timespec="seconds"),
        }
    finally:
        trail.close()


def _reconciliation_path() -> Path:
    raw = os.environ.get(RECONCILIATION_PATH_ENV)
    return Path(raw) if raw else DEFAULT_RECONCILIATION_PATH


def _load_reconciliations(fund_id: str) -> dict[str, dict[str, Any]]:
    """Load operator-authorized decision reconciliations for a fund.

    Returns a mapping of retired decision_id -> reconciliation record. Missing
    or malformed lines are skipped, so a partially written ledger never breaks a
    state read.
    """
    records: dict[str, dict[str, Any]] = {}
    try:
        text = _reconciliation_path().read_text(encoding="utf-8")
    except OSError:
        return records
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(row, dict) or row.get("fund_id") != fund_id:
            continue
        decision_id = row.get("decision_id")
        if decision_id:
            records[str(decision_id)] = row
    return records


def fund_read_state(
    fund_id: str,
    *,
    limit_enactments: int = 50,
) -> dict[str, Any]:
    """Reconstruct the latest visible fund state from stock-investor trail steps."""
    trail = EnactmentStore()
    try:
        enactments = []
        limit = _bounded(limit_enactments)
        for practice_id in INVESTOR_PRACTICE_IDS:
            enactments.extend(trail.recent_enactments(limit=limit, practice_id=practice_id))
        enactments.sort(key=lambda row: row.opened_at)

        mandate: dict[str, Any] | None = None
        latest_valuation: dict[str, Any] | None = None
        latest_follow_ups: dict[str, Any] | None = None
        orders: list[dict[str, Any]] = []
        decisions: list[dict[str, Any]] = []
        theses: list[dict[str, Any]] = []
        quantities: dict[str, float] = {}
        cash: float | None = None
        warnings: list[str] = []

        for enactment in enactments:
            for step in trail.steps_for(enactment.id):
                args = _json_object(step.arguments_json)
                if not args or args.get("fund_id") != fund_id:
                    continue
                material = step.material_name
                entry = {
                    "step_id": step.id,
                    "enactment_id": step.enactment_id,
                    "practice_id": enactment.practice_id,
                    "material_name": material,
                    "started_at": step.started_at,
                    "arguments": args,
                }
                if material in {"fund_record_setup", "paper_fund_record_setup"}:
                    mandate = entry
                    cash = _num(args.get("starting_capital"), cash or 0.0)
                elif material in {
                    "fund_record_valuation",
                    "paper_fund_record_valuation",
                }:
                    latest_valuation = entry
                    cash = _num(args.get("cash"), cash or 0.0)
                    quantities = {
                        str(position.get("symbol")): _num(position.get("quantity"))
                        for position in args.get("positions") or []
                        if isinstance(position, dict) and position.get("symbol")
                    }
                elif material in {
                    "fund_record_trade_decision",
                    "paper_fund_record_trade_decision",
                }:
                    decisions.append(entry)
                elif material in {
                    "brokerage_submit_buy_order",
                    "brokerage_submit_sell_order",
                }:
                    result = _json_object(step.result_summary) or {}
                    side = str(result.get("side") or args.get("side") or "").lower()
                    symbol = str(result.get("symbol") or args.get("symbol") or "")
                    quantity = _num(result.get("filled_quantity") or args.get("quantity"))
                    price = _num(
                        result.get("filled_price")
                        or args.get("estimated_price")
                        or args.get("limit_price")
                    )
                    orders.append({**entry, "result": result})
                    if symbol and side in {"buy", "sell"}:
                        signed_quantity = quantity if side == "buy" else -quantity
                        quantities[symbol] = quantities.get(symbol, 0.0) + signed_quantity
                        if cash is not None and price:
                            signed_cash = -signed_quantity * price
                            cash += signed_cash
                elif material in {"fund_record_thesis", "paper_fund_record_thesis"}:
                    theses.append(entry)
                elif material == "fund_record_follow_up_register":
                    latest_follow_ups = entry

        if mandate is None:
            warnings.append("No fund mandate/setup record found in the visible trail.")
        if not orders and not decisions:
            warnings.append("No order or trade-decision records found in the visible trail.")
        if latest_valuation is None:
            warnings.append("No valuation record found in the visible trail.")

        positions = [
            {"symbol": symbol, "quantity": quantity}
            for symbol, quantity in sorted(quantities.items())
            if abs(quantity) > 1e-9
        ]

        # Cross-check the thesis journal against the reconstructed position
        # ledger. Positions reconstruct from the order ledger; theses are a
        # separate record of intent. When the latest thesis for a symbol claims
        # the fund holds it but no position reconstructs (or claims it is
        # closed/rejected while a position is still held), the two ledgers have
        # drifted — typically a decision recorded without a matching order, or a
        # bundle migration that left a thesis stranded. This is determinable, so
        # it is surfaced as a reconstruction warning rather than left silent.
        held_symbols = {position["symbol"] for position in positions}
        latest_thesis_status: dict[str, str] = {}
        for thesis in theses:
            thesis_args = thesis.get("arguments") or {}
            symbol = thesis_args.get("symbol")
            status = thesis_args.get("status")
            if symbol and status:
                latest_thesis_status[str(symbol)] = str(status).lower()
        for symbol, status in sorted(latest_thesis_status.items()):
            if status == "holding" and symbol not in held_symbols:
                warnings.append(
                    f"Thesis/position drift: latest thesis marks {symbol} as a "
                    "'holding', but no position reconstructs from the order ledger "
                    "(decision recorded without a matching filled order?)."
                )
            elif status in {"closed", "rejected"} and symbol in held_symbols:
                warnings.append(
                    f"Thesis/position drift: a position in {symbol} is held, but "
                    f"its latest thesis status is '{status}'."
                )

        # Cross-check trade decisions against the executed-order ledger. A
        # buy/sell/add/trim decision implies an execution; if no order on the
        # trail carries its decision_id, the decision never became a position
        # change. This is the write-side counterpart of the thesis/position
        # drift above, and is exactly what leaves the decision ledger far longer
        # than the order ledger — intent recorded without the matching trade.
        # Operator-authorized reconciliations retire decisions that the trail
        # recorded but never executed (superseded starter intents), so they are
        # not re-flagged as drift every pass. They are surfaced separately in the
        # returned state, never silently dropped.
        reconciliations = _load_reconciliations(fund_id)
        executing_actions = {"buy", "sell", "add", "trim"}
        executed_decision_ids = {
            str(order["arguments"].get("decision_id"))
            for order in orders
            if isinstance(order.get("arguments"), dict)
            and order["arguments"].get("decision_id")
        }
        unmatched_decisions: list[str] = []
        reconciled_decision_ids: list[str] = []
        for decision in decisions:
            decision_args = decision.get("arguments") or {}
            action = str(decision_args.get("action") or "").lower()
            if action not in executing_actions:
                continue
            decision_id = decision_args.get("decision_id")
            decision_key = str(decision_id) if decision_id else ""
            if decision_key and decision_key in executed_decision_ids:
                continue
            if decision_key and decision_key in reconciliations:
                reconciled_decision_ids.append(decision_key)
                continue
            symbol = decision_args.get("symbol") or "?"
            unmatched_decisions.append(
                f"{action} {symbol} ({decision_id or 'no decision_id'})"
            )
        if unmatched_decisions:
            shown = "; ".join(unmatched_decisions[:8])
            more = (
                ""
                if len(unmatched_decisions) <= 8
                else f"; +{len(unmatched_decisions) - 8} more"
            )
            warnings.append(
                f"Decision/order drift: {len(unmatched_decisions)} trade "
                "decision(s) imply an execution but have no matching order on the "
                f"trail: {shown}{more}."
            )

        return {
            "fund_id": fund_id,
            "mandate": mandate,
            "cash": cash,
            "positions": positions,
            "orders": orders[-20:],
            "decisions": decisions[-20:],
            "theses": theses[-20:],
            "latest_valuation": latest_valuation,
            "latest_follow_ups": latest_follow_ups,
            "warnings": warnings,
            "reconciliations": [
                reconciliations[decision_key]
                for decision_key in reconciled_decision_ids
            ],
            "source": "trail.steps.stock_investor_state_reconstruction",
            "read_at": datetime.now(UTC).isoformat(timespec="seconds"),
        }
    finally:
        trail.close()
