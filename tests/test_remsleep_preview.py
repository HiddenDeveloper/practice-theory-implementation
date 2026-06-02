"""Capability-enforced RemSleep preview: writes are captured, never applied.

These tests pin the boundary the preview run relies on — with
``PRACTICE_REMSLEEP_PREVIEW=1`` the three canonical-mutating materials append
their intended effect to the journal and make no store/checkpoint write; with it
unset, behavior is unchanged (the real store path is taken).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from practice_theory_implementation.materials import (
    engagement_context,
    remsleep,
    remsleep_preview,
)


@pytest.fixture
def preview_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    journal = tmp_path / "remsleep_preview.jsonl"
    monkeypatch.setenv(remsleep_preview.PREVIEW_ENABLED_ENV, "1")
    monkeypatch.setenv(remsleep_preview.PREVIEW_PATH_ENV, str(journal))
    return journal


def _forbid_neo4j(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(_statements: list[dict[str, Any]]) -> dict[str, Any]:
        raise AssertionError("preview must not call Neo4j")

    monkeypatch.setattr(engagement_context, "_neo4j_commit", _boom)


def test_write_non_episodic_memory_preview_captures_and_skips_store(
    preview_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _forbid_neo4j(monkeypatch)

    result = engagement_context.write_non_episodic_memory(
        "AIlumina values honesty over reassurance.",
        anchor="self",
        kind="value",
        tags=["self"],
        confidence=0.9,
    )

    assert result["preview"] is True
    assert result["written"] is False
    assert result["anchor"] == "self"

    entries = remsleep_preview.read_journal(preview_env)
    assert len(entries) == 1
    entry = entries[0]
    assert entry["material"] == "write_non_episodic_memory"
    assert entry["anchor"] == "self"
    assert entry["anchor_label"] == "CanonicalSelf"
    assert entry["content"] == "AIlumina values honesty over reassurance."
    assert entry["kind"] == "value"
    assert entry["tags"] == ["self"]
    assert entry["confidence"] == 0.9
    assert entry["memory_id"]


def test_ensure_self_rooted_spine_preview_captures_and_skips_store(
    preview_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _forbid_neo4j(monkeypatch)

    result = engagement_context.ensure_self_rooted_spine()

    assert result["preview"] is True
    assert result["rooted_at"] == "CanonicalSelf"
    edges = {e["edge"] for e in result["intended_spine"]}
    assert edges == {"OFFERS_COMPANIONSHIP_TO", "SITUATED_IN", "GUIDED_BY"}

    entries = remsleep_preview.read_journal(preview_env)
    assert len(entries) == 1
    assert entries[0]["material"] == "ensure_self_rooted_spine"
    assert len(entries[0]["intended_edges"]) == 3


def test_record_checkpoint_preview_does_not_advance(
    preview_env: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    checkpoint_path = tmp_path / "remsleep_checkpoint.json"
    monkeypatch.setenv(remsleep.CHECKPOINT_PATH_ENV, str(checkpoint_path))

    result = remsleep.remsleep_record_checkpoint(
        episode_sequence=42,
        episode_date_time="2026-06-02T01:00:00Z",
    )

    assert result["preview"] is True
    assert result["advanced"] is False
    # The durable checkpoint file was never written.
    assert not checkpoint_path.exists()

    entries = remsleep_preview.read_journal(preview_env)
    assert len(entries) == 1
    captured = entries[0]
    assert captured["material"] == "remsleep_record_checkpoint"
    assert captured["intended_checkpoint"]["episode_sequence"] == 42


def test_preview_disabled_writes_through(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # No preview env set: the real store path must be taken.
    monkeypatch.delenv(remsleep_preview.PREVIEW_ENABLED_ENV, raising=False)
    calls: list[list[dict[str, Any]]] = []

    def _fake_commit(statements: list[dict[str, Any]]) -> dict[str, Any]:
        calls.append(statements)
        return {"results": [{"data": [{"row": [{"id": "mem-applied"}]}]}]}

    monkeypatch.setattr(engagement_context, "_neo4j_commit", _fake_commit)

    result = engagement_context.write_non_episodic_memory(
        "applied straight through", anchor="context"
    )

    assert "preview" not in result
    assert result["written"] is True
    assert len(calls) == 1  # the store WAS called when preview is off


def test_update_canonical_field_preview_captures(
    preview_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _forbid_neo4j(monkeypatch)

    result = engagement_context.update_canonical_field(
        "recent_decisions",
        "Adopt files-as-substrate",
        anchor="context",
        op="append",
        sources=["claude-code-29a4311c-turn-1"],
    )

    assert result["preview"] is True
    assert result["written"] is False
    assert result["field"] == "recent_decisions"
    assert result["op"] == "append"

    entries = remsleep_preview.read_journal(preview_env)
    assert len(entries) == 1
    entry = entries[0]
    assert entry["material"] == "update_canonical_field"
    assert entry["anchor_label"] == "CanonicalContext"
    assert entry["field"] == "recent_decisions"
    assert entry["op"] == "append"
    assert entry["value"] == "Adopt files-as-substrate"
    assert entry["sources"] == ["claude-code-29a4311c-turn-1"]


def test_update_canonical_field_append_writes_when_live(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(remsleep_preview.PREVIEW_ENABLED_ENV, raising=False)
    captured: dict[str, Any] = {}

    def _fake_commit(statements: list[dict[str, Any]]) -> dict[str, Any]:
        captured["statement"] = statements[0]["statement"]
        captured["parameters"] = statements[0]["parameters"]
        return {"results": [{"data": [{"row": [["existing", "new entry"]]}]}]}

    monkeypatch.setattr(engagement_context, "_neo4j_commit", _fake_commit)

    result = engagement_context.update_canonical_field(
        "active_projects", "new entry", anchor="context", op="append"
    )

    assert result["written"] is True
    assert result["value"] == ["existing", "new entry"]
    # Field is backtick-quoted into the Cypher (validated, version-portable).
    assert "`active_projects`" in captured["statement"]
    assert captured["parameters"]["new_values"] == ["new entry"]


def test_update_canonical_field_replace_writes_scalar(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(remsleep_preview.PREVIEW_ENABLED_ENV, raising=False)
    captured: dict[str, Any] = {}

    def _fake_commit(statements: list[dict[str, Any]]) -> dict[str, Any]:
        captured["statement"] = statements[0]["statement"]
        captured["parameters"] = statements[0]["parameters"]
        return {"results": [{"data": [{"row": ["new summary"]}]}]}

    monkeypatch.setattr(engagement_context, "_neo4j_commit", _fake_commit)

    result = engagement_context.update_canonical_field(
        "summary", "new summary", anchor="context", op="replace"
    )

    assert result["written"] is True
    assert result["value"] == "new summary"
    assert captured["parameters"]["value"] == "new summary"


def test_update_canonical_field_guards_reject_bad_input(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Guards return before any store call, so a forbidden Neo4j proves it.
    _forbid_neo4j(monkeypatch)
    assert "error" in engagement_context.update_canonical_field("id", "x", anchor="context")
    assert "error" in engagement_context.update_canonical_field("bad field", "x")
    assert "error" in engagement_context.update_canonical_field("summary", "x", anchor="nope")
    assert "error" in engagement_context.update_canonical_field("summary", "x", op="delete")
    assert "error" in engagement_context.update_canonical_field("   ", "x")


def test_engagement_projection_folds_in_attached_memory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(engagement_context, "consult_canonical_profile", lambda: {"id": "u"})
    monkeypatch.setattr(engagement_context, "consult_canonical_self", lambda: {"id": "s"})
    monkeypatch.setattr(engagement_context, "consult_canonical_context", lambda: {"id": "c"})

    def _fake_read(*, anchor: str, limit: int = 8, **_: Any) -> dict[str, Any]:
        if anchor == "context":
            return {
                "memories": [
                    {
                        "relationship_from_anchor": "HAS_NON_EPISODIC_MEMORY",
                        "properties": {
                            "id": "m1", "kind": "fact", "content": "files-as-substrate",
                            "tags": ["substrate"], "confidence": 0.7, "updated_at": "2026-06-02",
                        },
                    },
                    # A spine sibling (not a satellite) must be filtered out.
                    {
                        "relationship_from_anchor": "SITUATED_IN",
                        "properties": {"id": "CanonicalContext-node"},
                    },
                ]
            }
        return {"memories": []}

    monkeypatch.setattr(engagement_context, "read_non_episodic_memory", _fake_read)

    out = engagement_context.consult_engagement_context()

    assert out["user"]["id"] == "u"
    assert out["self"]["id"] == "s"
    attached = out["attached_memory"]
    assert attached["context"] == [
        {
            "id": "m1", "kind": "fact", "content": "files-as-substrate",
            "tags": ["substrate"], "confidence": 0.7, "updated_at": "2026-06-02",
        }
    ]
    assert attached["self"] == []  # only HAS_NON_EPISODIC_MEMORY satellites surface
