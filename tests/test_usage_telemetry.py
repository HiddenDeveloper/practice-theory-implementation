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
    _parse_codex_exec_usage,
    _usage_from_sdk_result,
    drain,
)
from practice_theory_implementation.trail import EnactmentStore, UsageRecord


def _record_dummy_step(store: EnactmentStore, enactment_id: str) -> None:
    store.record_step(
        enactment_id=enactment_id,
        affordance_id="test_affordance",
        material_name="test_material",
        arguments={},
        result={"ok": True},
        started_at="2026-01-01T00:00:00+00:00",
        completed_at="2026-01-01T00:00:01+00:00",
        duration_ms=1000,
    )


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


def test_parse_codex_exec_usage_from_jsonl() -> None:
    # Confirmed against live `codex exec --json` (codex-cli 0.136.0): usage on
    # the turn.completed event, agent text on the last item.completed.
    jsonl = "\n".join(
        [
            '{"type":"thread.started","thread_id":"t1"}',
            '{"type":"turn.started"}',
            '{"type":"item.completed","item":{"id":"item_0",'
            '"type":"agent_message","text":"a small poem"}}',
            '{"type":"turn.completed","usage":{"input_tokens":11357,'
            '"cached_input_tokens":2432,"output_tokens":35,'
            '"reasoning_output_tokens":0}}',
        ]
    )
    usage, text = _parse_codex_exec_usage(jsonl, model="gpt-5-codex")
    assert usage is not None
    assert usage.provider == "codex"
    assert usage.model == "gpt-5-codex"
    assert usage.input_tokens == 11357
    assert usage.output_tokens == 35
    assert usage.cache_read_tokens == 2432  # codex's cached_input_tokens
    assert usage.cache_creation_tokens is None  # codex has no creation/read split
    assert usage.cost_usd is None  # codex --json reports no cost
    assert usage.num_turns == 1
    assert text == "a small poem"


def test_parse_codex_exec_usage_tolerates_garbage() -> None:
    assert _parse_codex_exec_usage("not jsonl at all", model=None) == (None, None)
    assert _parse_codex_exec_usage("", model=None) == (None, None)
    # Valid events but no turn.completed -> no usage captured.
    assert _parse_codex_exec_usage('{"type":"turn.started"}', model=None) == (
        None,
        None,
    )


def test_usage_from_sdk_result_matches_live_shape() -> None:
    # Confirmed against a live ClaudeSDKClient query (claude-agent-sdk 0.2.87):
    # usage is a dict with these keys; total_cost_usd / num_turns are attributes.
    import types

    msg = types.SimpleNamespace(
        usage={
            "input_tokens": 6,
            "output_tokens": 71,
            "cache_read_input_tokens": 0,
            "cache_creation_input_tokens": 17181,
            "service_tier": "standard",
        },
        total_cost_usd=0.10968725,
        num_turns=1,
    )
    u = _usage_from_sdk_result(msg, model="claude-sonnet-4-6")
    assert u.provider == "anthropic"
    assert u.model == "claude-sonnet-4-6"
    assert u.input_tokens == 6
    assert u.output_tokens == 71
    assert u.cache_read_tokens == 0
    assert u.cache_creation_tokens == 17181
    assert u.cost_usd == 0.10968725
    assert u.num_turns == 1


def test_usage_from_sdk_result_tolerates_missing_fields() -> None:
    import types

    u = _usage_from_sdk_result(types.SimpleNamespace(), model=None)
    assert u.provider == "anthropic"
    assert u.input_tokens is None and u.cost_usd is None


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


class _OpenUsageAdapter(_UsageAdapter):
    async def dispatch(self, work: WorkItem) -> str | None:
        eid = self._store.open_enactment("judge", mode="autonomic")
        self.last_usage = self._usage
        self.last_eid = eid
        return eid


def test_loop_records_usage_keyed_by_consumer_enactment(tmp_path: Path) -> None:
    store = EnactmentStore(tmp_path / "trail.db")
    # A closed somatic enactment becomes Judge work.
    som = store.open_enactment("correspondent", mode="somatic")
    _record_dummy_step(store, som)
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


def test_drain_closes_open_consumer_enactment_after_dispatch(tmp_path: Path) -> None:
    store = EnactmentStore(tmp_path / "trail.db")
    som = store.open_enactment("correspondent", mode="somatic")
    _record_dummy_step(store, som)
    store.close_enactment(som)
    assert store.route_closed_enactments_to_judge_inbox() == 1

    adapter = _OpenUsageAdapter(
        AdapterConfig(role="judge", bundle_id="judge", brief=""),
        store,
        UsageRecord(provider="codex", input_tokens=11),
    )
    n = asyncio.run(
        drain(adapter, RolePolicy(role="judge"), store, worker_id="t", max_items=1)
    )
    assert n == 1

    assert adapter.last_eid is not None
    rows = [row for row in store.recent_enactments(limit=10) if row.id == adapter.last_eid]
    assert rows and rows[0].closed_at is not None
    assert store.usage_for(adapter.last_eid) is not None
    store.close()
