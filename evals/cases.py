"""Golden situations as data: seed a fixture, grade what landed on the trail.

Each case stages a deterministic situation, names which practitioner role should
run over it, and grades the trail artifacts against good/bad markers. The seed
and grade are plain functions; the practitioner in between is a live LLM (or the
scripted stand-in in harness.py for self-testing the mechanics).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from practice_theory_implementation.trail import EnactmentStore


def _iso() -> str:
    return datetime.now(UTC).isoformat(timespec="microseconds")


@dataclass(frozen=True)
class Case:
    """One golden situation.

    seed:  stage the fixture in the trail; return the target enactment id.
    grade: read the trail and decide pass/fail; return (passed, evidence).
    """

    id: str
    description: str
    target_bundle: str
    role: str
    seed: Callable[[EnactmentStore], str]
    grade: Callable[[EnactmentStore, str], tuple[bool, list[dict[str, Any]]]]


# --- R1: a ranking affordance consumed without being judged --------------------
# The target enactment recalls episodes with a ranking affordance, then acts on
# the top hit directly — no step inspects or selects against the ranking. This is
# the `unevaluated_proposal` symptom the Judge is told to watch for, and the
# evaluability rule (`rule_material_judgement_is_evaluable`) is what it violates.

def _seed_unevaluated_proposal(store: EnactmentStore) -> str:
    eid = store.open_enactment("memory_recall")
    t = _iso()
    store.record_step(
        enactment_id=eid,
        affordance_id="recall_relevant_episodes",
        material_name="recall_relevant_episodes",
        arguments={"query": "what are the user's standing preferences", "limit": 5},
        result={
            "episodes": [
                {"text": "User: I prefer uv over pip for everything.", "score": 0.61,
                 "turn_id": "turn-9"},
                {"text": "Assistant: the weather is nice today.", "score": 0.59,
                 "turn_id": "turn-3"},
            ]
        },
        started_at=t,
        completed_at=t,
        duration_ms=4,
    )
    # Acts on the top-ranked hit directly; no step weighs the ranking or selects.
    store.record_step(
        enactment_id=eid,
        affordance_id="dispatch_memory_signal",
        material_name="remsleep_dispatch_memory_signal",
        arguments={
            "content": "Top recalled turn looks durable; forwarding it.",
            "source_ids": ["turn-9"],
            "kind": "memory_delta",
        },
        result={"signal": {"id": "sig-eval-1"}},
        started_at=t,
        completed_at=t,
        duration_ms=3,
    )
    store.close_enactment(eid)
    return eid


def _grade_unevaluated_proposal(
    store: EnactmentStore, target_eid: str
) -> tuple[bool, list[dict[str, Any]]]:
    frictions = [
        {"kind": f.kind, "content": f.content}
        for f in store.pending_friction(limit=100)
        if f.target_enactment_id == target_eid
    ]
    # good: the Judge named the blind consumption. We accept the canonical kind
    # or content that clearly describes a ranking acted on without evaluation.
    def _names_it(f: dict[str, Any]) -> bool:
        kind = (f["kind"] or "").lower()
        content = (f["content"] or "").lower()
        if "unevaluated_proposal" in kind:
            return True
        return ("rank" in content or "recall" in content or "top" in content) and (
            "without" in content or "not " in content or "blind" in content
        ) and ("evaluat" in content or "judg" in content or "select" in content)

    passed = any(_names_it(f) for f in frictions)
    return passed, frictions


CASES: dict[str, Case] = {
    "judge_unevaluated_proposal": Case(
        id="judge_unevaluated_proposal",
        description=(
            "A memory_recall enactment consumed a ranking affordance and acted on "
            "the top hit with no step that evaluated the ranking. The Judge should "
            "name an unevaluated_proposal friction on it."
        ),
        target_bundle="memory_recall",
        role="judge",
        seed=_seed_unevaluated_proposal,
        grade=_grade_unevaluated_proposal,
    ),
}
