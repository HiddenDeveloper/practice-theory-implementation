from __future__ import annotations

from practice_theory_implementation.materials.remsleep import (
    remsleep_summarize_recall_candidates,
)


def test_summarizes_episodic_recall_with_source_backed_evidence() -> None:
    result = remsleep_summarize_recall_candidates(
        episodes={
            "episodes": [
                {
                    "turn_id": "ai-turn",
                    "role": "ai",
                    "sequence": 1,
                    "date_time": "2026-06-01T01:00:00Z",
                    "text": "Assistant observation",
                },
                {
                    "turn_id": "user-turn",
                    "role": "user",
                    "sequence": 2,
                    "date_time": "2026-06-01T01:01:00Z",
                    "text": "User said the recall should summarize real candidates.",
                },
            ],
            "review_window": {"sequence_from_exclusive": 0},
        },
        graph={"nodes": []},
    )

    candidate = result["candidates"][0]

    assert candidate["kind"] == "episodic_recall_summary"
    assert candidate["source_ids"] == ["user-turn"]
    assert "2 unreviewed episodic turns" in candidate["content"]
    assert "User said the recall" in candidate["content"]
    assert candidate["evidence"] == {
        "episode_count": 2,
        "user_episode_count": 1,
        "latest_sequence": 2,
        "latest_date_time": "2026-06-01T01:01:00Z",
        "review_window": {"sequence_from_exclusive": 0},
    }


def test_summarizes_graph_drift_with_label_counts_and_truncated_sources() -> None:
    graph_nodes = [
        {
            "labels": ["Decision"],
            "properties": {"id": f"decision-{idx}", "updated_at": f"2026-06-01T00:{idx:02d}:00Z"},
        }
        for idx in range(12)
    ]

    result = remsleep_summarize_recall_candidates(
        episodes={"episodes": []},
        graph={"since": "2026-05-31T00:00:00Z", "nodes": graph_nodes},
    )

    candidate = result["candidates"][0]

    assert candidate["kind"] == "graph_drift_summary"
    assert candidate["evidence"]["graph_node_count"] == 12
    assert candidate["evidence"]["label_counts"] == {"Decision": 12}
    assert candidate["evidence"]["latest_updated_at"] == "2026-06-01T00:11:00Z"
    assert len(candidate["source_ids"]) == 10
    assert candidate["source_ids"][0] == "neo4j:Decision:decision-0"


def test_summarizes_store_warnings_when_reads_are_partial() -> None:
    result = remsleep_summarize_recall_candidates(
        episodes={"warning": "episodic read unavailable"},
        graph={"warning": "graph read unavailable"},
    )

    candidate = result["candidates"][0]

    assert candidate["kind"] == "recall_warning"
    assert candidate["confidence"] == 0.5
    assert candidate["evidence"] == {
        "warnings": ["episodic read unavailable", "graph read unavailable"]
    }
    assert result["summary"] == {
        "episode_count": 0,
        "graph_node_count": 0,
        "warning_count": 2,
    }


def test_returns_noop_when_no_evidence_or_warnings_are_available() -> None:
    result = remsleep_summarize_recall_candidates(
        episodes={"episodes": []},
        graph={"nodes": []},
    )

    candidate = result["candidates"][0]

    assert candidate["kind"] == "recall_noop"
    assert candidate["confidence"] == 0.4
    assert candidate["evidence"] == {
        "episode_count": 0,
        "graph_node_count": 0,
        "warnings": [],
    }


def test_clamps_max_candidates_to_at_least_one() -> None:
    result = remsleep_summarize_recall_candidates(
        episodes={"episodes": [{"turn_id": "turn-1", "role": "user", "text": "one"}]},
        graph={"nodes": [{"labels": ["Topic"], "properties": {"name": "memory"}}]},
        max_candidates=0,
    )

    assert len(result["candidates"]) == 1
    assert result["candidates"][0]["kind"] == "episodic_recall_summary"
