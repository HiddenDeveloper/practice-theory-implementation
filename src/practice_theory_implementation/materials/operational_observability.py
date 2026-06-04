"""Read-only operational observability materials for the engagement layer."""

from __future__ import annotations

import json
from typing import Any

from practice_theory_implementation.observability import otel_status
from practice_theory_implementation.trail import EnactmentStore


def _row_dict(row: Any) -> dict[str, Any]:
    return dict(row)


def _decode_json(value: str | None) -> object | None:
    if not value:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def read_system_observability(limit: int = 10) -> dict[str, Any]:
    """Return a read-only operational summary from the local trail + OTEL config."""
    limit = max(1, min(int(limit), 50))
    store = EnactmentStore()
    try:
        with store._cursor() as cur:
            counts: dict[str, int] = {}
            for label, query in [
                (
                    "pending_judge_inbox",
                    "SELECT COUNT(*) FROM judge_inbox WHERE consumed_at IS NULL",
                ),
                (
                    "pending_smoother_inbox",
                    "SELECT COUNT(*) FROM smoother_inbox WHERE consumed_at IS NULL",
                ),
                (
                    "unaddressed_friction",
                    "SELECT COUNT(*) FROM friction_observations WHERE addressed_at IS NULL",
                ),
                ("open_enactments", "SELECT COUNT(*) FROM enactments WHERE closed_at IS NULL"),
            ]:
                cur.execute(query)
                counts[label] = int(cur.fetchone()[0])

            starts: dict[str, str | None] = {}
            for label, query in [
                (
                    "pending_judge_inbox",
                    "SELECT MIN(routed_at) FROM judge_inbox WHERE consumed_at IS NULL",
                ),
                (
                    "pending_smoother_inbox",
                    "SELECT MIN(routed_at) FROM smoother_inbox WHERE consumed_at IS NULL",
                ),
                (
                    "unaddressed_friction",
                    "SELECT MIN(observed_at) FROM friction_observations WHERE addressed_at IS NULL",
                ),
                (
                    "open_enactments",
                    "SELECT MIN(opened_at) FROM enactments WHERE closed_at IS NULL",
                ),
            ]:
                cur.execute(query)
                value = cur.fetchone()[0]
                starts[label] = str(value) if value else None

            cur.execute(
                """
                SELECT u.recorded_at, e.practice_id, u.provider, u.model,
                       u.input_tokens, u.output_tokens, u.cache_read_tokens,
                       u.cost_usd, u.num_turns, u.dispatch_ms, u.enactment_id
                FROM enactment_usage u JOIN enactments e ON e.id = u.enactment_id
                ORDER BY u.recorded_at DESC LIMIT ?
                """,
                (limit,),
            )
            recent_usage = [_row_dict(row) for row in cur.fetchall()]

            cur.execute(
                """
                SELECT e.practice_id, COUNT(*) AS runs,
                       MAX(u.recorded_at) AS last_recorded,
                       SUM(u.input_tokens) AS input_tokens,
                       SUM(u.output_tokens) AS output_tokens,
                       SUM(u.cache_read_tokens) AS cache_read_tokens,
                       ROUND(AVG(u.dispatch_ms), 1) AS avg_dispatch_ms,
                       MAX(u.dispatch_ms) AS max_dispatch_ms
                FROM enactment_usage u JOIN enactments e ON e.id = u.enactment_id
                GROUP BY e.practice_id
                ORDER BY last_recorded DESC
                """
            )
            usage_by_practice = [_row_dict(row) for row in cur.fetchall()]
    finally:
        store.close()

    issues: list[dict[str, Any]] = []
    for key, count in counts.items():
        if count:
            issues.append(
                {
                    "kind": key,
                    "count": count,
                    "started_at": starts.get(key),
                    "still_happening": True,
                }
            )
    for row in usage_by_practice:
        avg = row.get("avg_dispatch_ms")
        if isinstance(avg, int | float) and avg > 120_000:
            issues.append(
                {
                    "kind": "high_average_dispatch_latency",
                    "practice_id": row.get("practice_id"),
                    "avg_dispatch_ms": avg,
                    "last_seen_at": row.get("last_recorded"),
                    "still_happening": True,
                }
            )

    return {
        "otel": otel_status(),
        "trail": {
            "counts": counts,
            "started_at": starts,
            "issues": issues,
            "recent_usage": recent_usage,
            "usage_by_practice": usage_by_practice,
        },
        "interpretation": (
            "OTEL carries operational spans when export is configured; the trail "
            "remains the durable evidence store for enactments, Friction, and usage."
        ),
    }


def _changed_substrate_ids(arguments: object) -> list[str]:
    if not isinstance(arguments, dict):
        return []
    out: list[str] = []
    target_id = arguments.get("id") or arguments.get("name")
    pool = arguments.get("pool")
    if isinstance(target_id, str):
        out.append(f"{pool}:{target_id}" if isinstance(pool, str) else target_id)
    return out


def read_autonomic_maintenance_context(limit: int = 10) -> dict[str, Any]:
    """Return recent Smoother work with its Friction purpose and substrate effect."""
    limit = max(1, min(int(limit), 50))
    store = EnactmentStore()
    try:
        with store._cursor() as cur:
            cur.execute(
                """
                SELECT id, practice_id, opened_at, closed_at
                FROM enactments
                WHERE practice_id = 'smoother'
                ORDER BY opened_at DESC LIMIT ?
                """,
                (limit,),
            )
            enactments = [_row_dict(row) for row in cur.fetchall()]
            out: list[dict[str, Any]] = []
            for enactment in enactments:
                enactment_id = enactment["id"]
                cur.execute(
                    """
                    SELECT id, kind, content, observation_data_json, observed_at,
                           addressed_at, target_enactment_id
                    FROM friction_observations
                    WHERE addressed_by_enactment_id = ?
                    ORDER BY id DESC LIMIT 1
                    """,
                    (enactment_id,),
                )
                friction_row = cur.fetchone()
                friction = _row_dict(friction_row) if friction_row is not None else None
                if friction is not None:
                    friction["observation_data"] = _decode_json(
                        friction.pop("observation_data_json", None)
                    )

                cur.execute(
                    """
                    SELECT affordance_id, material_name, arguments_json,
                           result_summary, started_at, completed_at, duration_ms
                    FROM steps
                    WHERE enactment_id = ?
                    ORDER BY id
                    """,
                    (enactment_id,),
                )
                steps: list[dict[str, Any]] = []
                changed_ids: list[str] = []
                for row in cur.fetchall():
                    step = _row_dict(row)
                    arguments = _decode_json(step.pop("arguments_json", None))
                    step["arguments"] = arguments
                    step["result"] = _decode_json(step.pop("result_summary", None))
                    if str(step["material_name"]).startswith("pm_"):
                        changed_ids.extend(_changed_substrate_ids(arguments))
                    steps.append(step)

                out.append(
                    {
                        "enactment_id": enactment_id,
                        "opened_at": enactment["opened_at"],
                        "closed_at": enactment["closed_at"],
                        "status": "closed" if enactment["closed_at"] else "open",
                        "friction": friction,
                        "purpose": (
                            friction["content"] if friction else "No addressed Friction found."
                        ),
                        "actions": [
                            {
                                "affordance_id": step["affordance_id"],
                                "material_name": step["material_name"],
                            }
                            for step in steps
                        ],
                        "changed_substrate_ids": sorted(set(changed_ids)),
                        "closure_basis_visible": any(
                            step["material_name"] == "smoother_read_pending_friction"
                            and isinstance(step.get("arguments"), dict)
                            and step["arguments"].get("friction_id") is not None
                            for step in steps
                        ),
                    }
                )
    finally:
        store.close()

    open_work = [item for item in out if item["status"] == "open"]
    return {
        "summary": {
            "recent_smoother_enactments": len(out),
            "open_smoother_enactments": len(open_work),
            "recent_changed_substrate_ids": sorted(
                {sid for item in out for sid in item["changed_substrate_ids"]}
            ),
        },
        "smoother_enactments": out,
        "interpretation": (
            "These are autonomic maintenance acts: each Smoother enactment exists "
            "to address Judge-emitted Friction, usually by amending substrate or "
            "recording why no mutation is appropriate."
        ),
    }
