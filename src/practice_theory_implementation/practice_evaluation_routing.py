"""Route practice-evaluation results into the autonomic loop.

Phase 2 closes the Judge loop around the Phase 1 engine. Two deterministic
substrate-shape checks (no LLM) plus the bridge to the Judge for the one part
that needs judgement:

- **Newness** — set-diff of somatic practices minus those carrying a current
  evaluation layer. A practice with no spec is not yet measurable; emit a
  deterministic `practice_missing_evaluation` Friction so the Smoother authors
  one. (The §11 `bundle_requires_current_evaluation` invariant, detect-only.)
- **Objective coverage** — a spec whose `objective_ref` does not name one of its
  bundle's teleo-affective ids is a vacuous evaluator; emit a deterministic
  `evaluation_objective_uncovered` Friction. (The §11
  `evaluation_must_cover_teleo_affective` invariant, detect-only.)
- **Concerns** — running the engine over a practice's real trail yields
  `concern` signals. Whether a concern is *real quality friction* or acceptable
  variation (patient holding, legitimately periodic work) is a judgement, so
  concerns are NOT turned into Friction here. The runner dispatches the Judge
  with `compose_concern_brief`; the Judge emits Friction for genuine ones via its
  own `emit_friction`, and those flow to the Smoother by the normal route.

Friction emission is idempotent: a check that already has an open Friction for a
practice is not re-raised, so repeated passes do not pile up duplicates.
Staleness (`evaluation_not_stale`) is deferred until bundle revisions are
hashed.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field

from practice_theory_implementation.materials import practice_evaluation
from practice_theory_implementation.substrate_loader import LoadedSubstrate
from practice_theory_implementation.trail import EnactmentStore
from practice_theory_implementation.types import Bundle

logger = logging.getLogger(__name__)

PRACTICE_EVAL_OBSERVER = "system:practice-eval"
MISSING_EVALUATION_KIND = "practice_missing_evaluation"
OBJECTIVE_UNCOVERED_KIND = "evaluation_objective_uncovered"


# --- deterministic substrate-shape reads (pure) ---------------------------


def evaluable_somatic_bundles(loaded: LoadedSubstrate) -> list[Bundle]:
    """The somatic practices in the catalog — those the evaluation regime
    applies to. (Autonomic practices judging themselves is a later concern.)"""
    return [b for b in loaded.bundles.values() if b.mode == "somatic"]


def _resolved_specs(loaded: LoadedSubstrate, bundle: Bundle) -> list[str]:
    specs = [sid for sid in bundle.evaluation_ids if sid in loaded.substrate.evaluations]
    if specs:
        return specs
    return [
        s.id
        for s in loaded.substrate.evaluations.values()
        if s.practice_id == bundle.id
    ]


def unevaluated_somatic_practices(loaded: LoadedSubstrate) -> list[str]:
    """Somatic practices carrying no current evaluation layer."""
    return [
        b.id
        for b in evaluable_somatic_bundles(loaded)
        if not _resolved_specs(loaded, b)
    ]


def objective_uncovered(loaded: LoadedSubstrate) -> list[tuple[str, str, str]]:
    """(bundle_id, spec_id, reason) for specs that do not cover their objective.

    A spec must name an `objective_ref` that is one of its bundle's
    teleo-affective ids, so the evaluator demonstrably measures the practice's
    declared purpose rather than something incidental.
    """
    out: list[tuple[str, str, str]] = []
    for bundle in evaluable_somatic_bundles(loaded):
        for sid in _resolved_specs(loaded, bundle):
            spec = loaded.substrate.evaluations.get(sid)
            if spec is None:
                continue
            if not spec.objective_ref:
                out.append((bundle.id, sid, "spec declares no objective_ref"))
            elif spec.objective_ref not in bundle.teleo_affective_ids:
                out.append(
                    (
                        bundle.id,
                        sid,
                        f"objective_ref {spec.objective_ref!r} is not a "
                        f"teleo-affective id of bundle {bundle.id!r}",
                    )
                )
    return out


def practices_with_concerns(
    loaded: LoadedSubstrate, store: EnactmentStore
) -> list[dict]:
    """Run the engine over every evaluated somatic practice; keep those with
    at least one `concern`. Each entry is the engine's full result."""
    out: list[dict] = []
    for bundle in evaluable_somatic_bundles(loaded):
        if not _resolved_specs(loaded, bundle):
            continue
        result = practice_evaluation.evaluate_with(
            trail=store,
            substrate=loaded.substrate,
            bundle_catalog=loaded.bundles,
            name=bundle.id,
        )
        if result.get("concern_count", 0) > 0:
            out.append(result)
    return out


def evaluation_window_signature(result: dict) -> str:
    """Stable signature of the enactment window + concerns behind a result.

    Two evaluations of the same practice yield the same signature when neither
    the evaluated enactment window nor the set of concern signals has changed.
    The Judge dispatch is keyed on this so an idle somatic practice — one with
    no new human-driven enactment since its last review — is not re-reviewed
    every cooldown cycle (the activities_management duplication: a frozen 8-pass
    window re-judged ~2,200 times). Built purely from data the engine already
    reports: per-spec `evaluated_enactment_ids` and, for findings in `concern`
    status, their `signal_id`. A new enactment or a newly-tripped signal changes
    the signature and so re-opens review; pure substrate re-wording does not.
    """
    ids: set[str] = set()
    concerns: set[str] = set()

    def _collect(part: dict) -> None:
        ids.update(part.get("evaluated_enactment_ids") or [])
        for finding in part.get("findings") or []:
            if finding.get("status") == "concern":
                concerns.add(str(finding.get("signal_id")))

    _collect(result)
    for part in result.get("results") or []:
        _collect(part)
    return "ids:" + ",".join(sorted(ids)) + ";concerns:" + ",".join(sorted(concerns))


# --- idempotent deterministic Friction routing ----------------------------


def _open_friction_practices(store: EnactmentStore, kind: str) -> set[str]:
    """practice_ids that already have an unaddressed Friction of this kind."""
    seen: set[str] = set()
    for fr in store.pending_friction(limit=500):
        if fr.kind != kind or not fr.observation_data_json:
            continue
        try:
            data = json.loads(fr.observation_data_json)
        except (ValueError, TypeError):
            continue
        pid = data.get("practice_id")
        if isinstance(pid, str):
            seen.add(pid)
    return seen


def _target_for(store: EnactmentStore, bundle_id: str) -> str:
    """A Friction needs a target enactment; these are bundle-level findings, so
    use the practice's most recent enactment, falling back to a bundle sentinel
    when it has never been enacted."""
    row = store.most_recent_enactment_of(bundle_id)
    return row.id if row is not None else f"bundle:{bundle_id}"


@dataclass(slots=True)
class RoutingSummary:
    missing_evaluation: int = 0
    objective_uncovered: int = 0
    practices_with_concerns: int = 0
    detail: list[str] = field(default_factory=list)

    @property
    def notification(self) -> str:
        return (
            "practice-eval routing: "
            f"missing_evaluation={self.missing_evaluation} "
            f"objective_uncovered={self.objective_uncovered} "
            f"practices_with_concerns={self.practices_with_concerns}"
        )


def route_evaluation_governance(
    store: EnactmentStore, loaded: LoadedSubstrate
) -> RoutingSummary:
    """Emit the deterministic, idempotent governance Frictions (no LLM).

    Detect-only: it raises Friction so the gap is visible and the Smoother can
    act once it carries the pooled authoring (Phases 3-4); it does not itself
    amend substrate.
    """
    summary = RoutingSummary()

    already_missing = _open_friction_practices(store, MISSING_EVALUATION_KIND)
    for pid in unevaluated_somatic_practices(loaded):
        if pid in already_missing:
            continue
        store.record_friction(
            observing_enactment_id=PRACTICE_EVAL_OBSERVER,
            target_enactment_id=_target_for(store, pid),
            kind=MISSING_EVALUATION_KIND,
            content=(
                f"Practice {pid!r} has no evaluation layer, so whether it "
                f"delivers its objective cannot be measured. An EvaluationSpec "
                f"should be authored for it."
            ),
            observation_data={
                "practice_id": pid,
                "detector": "unevaluated_somatic_practice",
                "basis": "no current evaluation_ids resolve for this bundle",
            },
        )
        summary.missing_evaluation += 1
        summary.detail.append(f"missing_evaluation: {pid}")

    already_uncovered = _open_friction_practices(store, OBJECTIVE_UNCOVERED_KIND)
    for pid, sid, reason in objective_uncovered(loaded):
        if pid in already_uncovered:
            continue
        store.record_friction(
            observing_enactment_id=PRACTICE_EVAL_OBSERVER,
            target_enactment_id=_target_for(store, pid),
            kind=OBJECTIVE_UNCOVERED_KIND,
            content=(
                f"Evaluation spec {sid!r} for practice {pid!r} does not cover the "
                f"practice's declared objective: {reason}. The evaluator may be "
                f"vacuous."
            ),
            observation_data={
                "practice_id": pid,
                "spec_id": sid,
                "detector": "objective_uncovered",
                "basis": reason,
            },
        )
        summary.objective_uncovered += 1
        summary.detail.append(f"objective_uncovered: {pid}/{sid}")

    return summary


# --- Judge dispatch brief (pure) ------------------------------------------


def compose_concern_brief(result: dict) -> str:
    """Build the Judge dispatch from one practice's engine result.

    The Judge re-examines and decides whether each concern is real quality
    friction or acceptable variation — it is not handed a verdict.
    """
    pid = result.get("practice_id")
    lines: list[str] = []
    for finding in result.get("findings", []):
        if finding.get("status") != "concern":
            continue
        evidence = json.dumps(finding.get("evidence", {}), sort_keys=True)
        lines.append(
            f"- signal `{finding.get('signal_id')}` ({finding.get('kind')}) raised a "
            f"concern: {finding.get('detail')}\n  evidence: {evidence}"
        )
    body = "\n".join(lines)
    return (
        "# Practice quality review\n\n"
        f"The evaluation engine measured practice `{pid}` over its real trail and "
        "raised the concerns below. A concern is a measurement, NOT a verdict.\n\n"
        "Re-examine using `evaluate_practice_quality` and the enactment trail, then "
        "decide for each concern whether it is genuine quality friction (a real "
        "stall, drift left unresolved, or an objective the practice is failing to "
        "deliver) or acceptable variation (disciplined patience, legitimately "
        "periodic work). `emit_friction` once per genuine concern, naming the "
        "practice_id and the signal_id in observation_data so the Smoother can act; "
        "record a no-finding for concerns that are acceptable. Do not propose "
        "remedies — the Smoother decides what to do.\n\n"
        f"Concerns under review for `{pid}`:\n{body}\n"
    )
