"""Per-enactment usage telemetry — trail round-trip + Claude-CLI usage parsing.

Autonomic-only for now; the table is keyed by enactment_id so a somatic row is
the same shape later. Cost is stored as the provider reports it (null when the
provider doesn't surface it), never re-derived.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from practice_theory_implementation.autonomic_adapters import (
    AdapterConfig,
    AutonomicAdapter,
    RolePolicy,
    WorkItem,
    _parse_claude_cli_result,
    drain,
)
from practice_theory_implementation.trail import EnactmentStore, UsageRecord


def test_record_and_read_usage_roundtrip(tmp_path: Path) -> None:
    store = EnactmentStore(tmp_path / "trail.db")
    eid = store.open_enactment("judge", mode="autonomic")
    store.record_usage(
        eid,
        UsageRecord(
            provider="anthropic_cli",
            model="claude-sonnet-4-6",
            input_tokens=1500,
            output_tokens=320,
            cache_read_tokens=12000,
            cache_creation_tokens=800,
            cost_usd=0.0123,
            num_turns=3,
        ),
        dispatch_ms=4200,
    )

    row = store.usage_for(eid)
    assert row is not None
    assert row.enactment_id == eid
    assert row.provider == "anthropic_cli"
    assert row.model == "claude-sonnet-4-6"
    assert (row.input_tokens, row.output_tokens) == (1500, 320)
    assert (row.cache_read_tokens, row.cache_creation_tokens) == (12000, 800)
    assert row.cost_usd == 0.0123
    assert row.num_turns == 3
    assert row.dispatch_ms == 4200
    assert row.recorded_at  # stamped
    store.close()


def test_usage_for_missing_returns_none(tmp_path: Path) -> None:
    store = EnactmentStore(tmp_path / "trail.db")
    assert store.usage_for("no-such-enactment") is None
    store.close()


def test_record_usage_is_idempotent_on_enactment_id(tmp_path: Path) -> None:
    store = EnactmentStore(tmp_path / "trail.db")
    eid = store.open_enactment("smoother", mode="autonomic")
    store.record_usage(eid, UsageRecord(provider="codex", input_tokens=10))
    store.record_usage(eid, UsageRecord(provider="codex", input_tokens=99))  # replace
    row = store.usage_for(eid)
    assert row is not None and row.input_tokens == 99  # second write wins
    store.close()


def test_cost_null_when_provider_omits_it(tmp_path: Path) -> None:
    # Codex path: provider/model only, tokens and cost null — stored, not invented.
    store = EnactmentStore(tmp_path / "trail.db")
    eid = store.open_enactment("memory_recall", mode="autonomic")
    store.record_usage(eid, UsageRecord(provider="codex", model="gpt-5"))
    row = store.usage_for(eid)
    assert row is not None
    assert row.provider == "codex" and row.model == "gpt-5"
    assert row.cost_usd is None and row.input_tokens is None
    store.close()


def test_parse_claude_cli_result_extracts_usage_and_text() -> None:
    blob = (
        '{"type":"result","subtype":"success","is_error":false,'
        '"duration_ms":4200,"num_turns":3,'
        '"result":"Observed: emitted one friction.",'
        '"total_cost_usd":0.0123,'
        '"usage":{"input_tokens":1500,"output_tokens":320,'
        '"cache_read_input_tokens":12000,"cache_creation_input_tokens":800}}'
    )
    usage, text = _parse_claude_cli_result(blob, model="claude-sonnet-4-6")
    assert usage is not None
    assert usage.provider == "anthropic_cli"
    assert usage.model == "claude-sonnet-4-6"
    assert usage.input_tokens == 1500
    assert usage.output_tokens == 320
    assert usage.cache_read_tokens == 12000
    assert usage.cache_creation_tokens == 800
    assert usage.cost_usd == 0.0123
    assert usage.num_turns == 3
    assert text == "Observed: emitted one friction."


def test_parse_claude_cli_result_tolerates_garbage() -> None:
    # Best-effort: non-JSON or non-object stdout yields (None, None), never raises.
    assert _parse_claude_cli_result("not json at all", model=None) == (None, None)
    assert _parse_claude_cli_result("[]", model=None) == (None, None)
    assert _parse_claude_cli_result("", model=None) == (None, None)


def test_parse_claude_cli_result_model_from_modelusage() -> None:
    # Confirmed against live `claude -p --output-format json`: the model name is
    # not a top-level field — it is the key of `modelUsage`. Recover it there.
    blob = (
        '{"type":"result","subtype":"success","result":"hi",'
        '"model":null,"total_cost_usd":0.04,"num_turns":1,'
        '"usage":{"input_tokens":10,"output_tokens":5},'
        '"modelUsage":{"claude-opus-4-8[1m]":{"input_tokens":10}}}'
    )
    usage, _ = _parse_claude_cli_result(blob, model=None)
    assert usage is not None
    assert usage.model == "claude-opus-4-8[1m]"
    # An explicit configured model still takes precedence.
    usage2, _ = _parse_claude_cli_result(blob, model="claude-sonnet-4-6")
    assert usage2 is not None and usage2.model == "claude-sonnet-4-6"


class _UsageAdapter(AutonomicAdapter):
    """Test adapter: enacts a judge enactment and reports fixed usage."""

    def __init__(
        self, config: AdapterConfig, store: EnactmentStore, usage: UsageRecord
    ) -> None:
        super().__init__(config)
        self._store = store
        self._usage = usage
        self.last_eid: str | None = None

    async def open(self) -> None:
        return

    async def close(self) -> None:
        return

    async def dispatch(self, work: WorkItem) -> str | None:
        eid = self._store.open_enactment("judge", mode="autonomic")
        self._store.close_enactment(eid)
        self.last_usage = self._usage
        self.last_eid = eid
        return eid


def test_loop_records_usage_keyed_by_consumer_enactment(tmp_path: Path) -> None:
    store = EnactmentStore(tmp_path / "trail.db")
    # A closed somatic enactment becomes Judge work.
    som = store.open_enactment("correspondent", mode="somatic")
    store.close_enactment(som)
    assert store.route_closed_enactments_to_judge_inbox() == 1

    usage = UsageRecord(
        provider="anthropic_cli", model="m", input_tokens=7, cost_usd=0.5
    )
    adapter = _UsageAdapter(
        AdapterConfig(role="judge", bundle_id="judge", brief=""), store, usage
    )
    n = asyncio.run(
        drain(adapter, RolePolicy(role="judge"), store, worker_id="t", max_items=1)
    )
    assert n == 1

    # Usage is attributed to the JUDGE enactment the dispatch produced, not the
    # somatic one it examined.
    assert adapter.last_eid is not None
    row = store.usage_for(adapter.last_eid)
    assert row is not None
    assert row.provider == "anthropic_cli"
    assert row.input_tokens == 7
    assert row.cost_usd == 0.5
    assert row.dispatch_ms is not None and row.dispatch_ms >= 0
    assert store.usage_for(som) is None  # the examined enactment has no usage row
    store.close()
