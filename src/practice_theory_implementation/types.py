"""Data shapes for the substrate, bundles, and the function registry.

Step 2 redefines Bundle as a pure selection of IDs over the substrate's pools.
Step 1's inline-content shape is gone — the bundle no longer carries its own
content; it points into pools that the substrate holds.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Literal

type JsonSchema = Mapping[str, object]
type Mode = Literal["somatic", "autonomic"]
type InvariantStatus = Literal["active", "tombstoned"]
type InvariantMode = Literal["detect"]


@dataclass(frozen=True, slots=True, kw_only=True)
class PoolElement:
    """A content element in the teleo-affective, understanding, or rules pool.

    Same shape for all three pools — small content unit with an id, a name,
    and a body of prose.
    """

    id: str
    name: str
    content: str


@dataclass(frozen=True, slots=True, kw_only=True)
class Material:
    """A material's outward face in the substrate.

    `name` is the unique handle: affordances reference materials by name, and
    the function registry binds the callable by name. The callable may be a
    hand-written function or a dynamic implementation registered at runtime.
    """

    name: str
    description: str
    input_schema: JsonSchema


@dataclass(frozen=True, slots=True, kw_only=True)
class Check:
    """A determinable precondition homed on the affordance it constrains.

    The deterministic face of a usage contract, owned by the thing it governs
    rather than living in a free-floating pool (the design move that dissolves
    the `invariants` pool — see docs/plans/invariants-as-affordance-material-
    checks.md). The engine evaluates `forbid_when` — the same predicate
    vocabulary as the legacy `Invariant` — against any closed enactment that
    contains a step on the `trigger` material, over the steps before that step;
    a satisfied predicate is a violation that raises and resolves
    `friction_kind` with no LLM. `id` is unique within the owning affordance, so
    the firing identity is `affordance:<owner_id>::<id>`. A tombstoned check
    keeps its entry (history) but is skipped by the evaluator.
    """

    id: str
    name: str
    trigger: str  # material_name whose presence in an enactment arms the check
    friction_kind: str
    message: str
    forbid_when: Mapping[str, object]  # violation predicate (see invariant_engine)
    content: str = ""
    status: InvariantStatus = "active"
    mode: InvariantMode = "detect"


@dataclass(frozen=True, slots=True, kw_only=True)
class Affordance:
    """A practice-perspectival capability framed over one or more materials.

    `materials` is a tuple of Material names this affordance reaches for,
    resolved against the substrate's material pool. `preconditions` are the
    determinable usage contracts the affordance owns — checks the engine
    enforces on the affordance's proper use (e.g. an ordering requirement over
    its materials), homed here rather than in a separate pool.
    """

    id: str
    name: str
    description: str
    materials: tuple[str, ...]
    preconditions: tuple[Check, ...] = ()


@dataclass(frozen=True, slots=True, kw_only=True)
class EvaluationSpec:
    """A declarative measure of whether a practice delivers its objective.

    A practice's own statement of how it should be judged — the assertion layer
    of its system test, run by the evaluation engine over that practice's real
    trail. Data, never code: `signals` is a tuple of small declarative checks
    (kind + params) the generic engine knows how to compute deterministically.

    `objective_ref` ties the spec back to the teleo-affective element it
    measures, so an evaluator that does not actually exercise the practice's
    declared objective is itself detectable as vacuous. `window` is how many
    recent closed enactments the engine considers. `derived_from` pins the
    bundle revision the spec was authored against, so staleness is detectable.
    """

    id: str
    name: str
    practice_id: str
    window: int = 8
    objective_ref: str | None = None
    derived_from: str | None = None
    signals: tuple[Mapping[str, object], ...] = ()
    content: str = ""


@dataclass(frozen=True, slots=True, kw_only=True)
class Bundle:
    """A practice captured as a selection of pool IDs.

    No inline content. Each id-tuple resolves into the corresponding pool to
    produce the bundle's effective content. The bundle's effective materials
    are derived from its affordances — materials are not listed on the bundle
    directly.

    `mode` declares whether the bundle is somatic (requires the user) or
    autonomic (acts alone). A mode-aware server filters its catalog by this
    field and only projects the engagement layer in somatic mode.

    `evaluation_ids` selects the bundle's evaluation layer — the practice's
    own measure of whether it delivers its objective. Empty is tolerated for
    now (the invariant that requires a present evaluation lands in a later
    phase); existing bundles without it stay valid.
    """

    id: str
    name: str
    description: str
    teleo_affective_ids: tuple[str, ...]
    understanding_ids: tuple[str, ...]
    rules_ids: tuple[str, ...]
    affordance_ids: tuple[str, ...]
    evaluation_ids: tuple[str, ...] = ()
    mode: Mode = "somatic"


@dataclass(frozen=True, slots=True, kw_only=True)
class Invariant:
    """A governed deterministic guard the Smoother authors, amends, tombstones.

    A determinable contract over an enactment's step history. The routing layer
    evaluates `forbid_when` (a declarative predicate) against any closed
    enactment that contains a step on the `trigger` material; if the predicate
    is satisfied, the contract is violated and the friction `friction_kind` is
    raised — and, because the violation is determinable, resolved — without any
    LLM. Judgement only enters when the Smoother authors/refines the rule and
    when the scheduled audit reviews how it has fired.

    `status` is the substrate's first soft-retire concept: a tombstoned
    invariant keeps its file (history) but is skipped by the evaluator.
    """

    id: str
    name: str
    trigger: str  # material_name whose presence in an enactment arms the check
    friction_kind: str
    message: str
    forbid_when: Mapping[str, object]  # declarative predicate (see invariant_engine)
    content: str  # body prose
    status: InvariantStatus = "active"
    mode: InvariantMode = "detect"
    tombstoned_at: str | None = None
    tombstone_reason: str | None = None


@dataclass(slots=True)
class Substrate:
    """The pools at the substrate level, shared across all bundles.

    Mutable so runtime additions (dynamic materials, dynamic affordances,
    invariants) are supported. Step 2 hand-populates the substrate at module
    load time; later steps may amend it.
    """

    teleo_affective: dict[str, PoolElement] = field(default_factory=dict)
    understanding: dict[str, PoolElement] = field(default_factory=dict)
    rules: dict[str, PoolElement] = field(default_factory=dict)
    affordances: dict[str, Affordance] = field(default_factory=dict)
    materials: dict[str, Material] = field(default_factory=dict)
    invariants: dict[str, Invariant] = field(default_factory=dict)
    evaluations: dict[str, EvaluationSpec] = field(default_factory=dict)


def validate_bundle(bundle: Bundle, substrate: Substrate) -> None:
    """Check every id-tuple resolves into the corresponding substrate pool.

    Materials are checked transitively via the bundle's affordances: each
    referenced affordance's `materials` must resolve into the materials pool.
    """
    missing: list[str] = []

    for ta_id in bundle.teleo_affective_ids:
        if ta_id not in substrate.teleo_affective:
            missing.append(f"teleo_affective id {ta_id!r}")
    for u_id in bundle.understanding_ids:
        if u_id not in substrate.understanding:
            missing.append(f"understanding id {u_id!r}")
    for r_id in bundle.rules_ids:
        if r_id not in substrate.rules:
            missing.append(f"rules id {r_id!r}")
    for ev_id in bundle.evaluation_ids:
        if ev_id not in substrate.evaluations:
            missing.append(f"evaluation id {ev_id!r}")
    for aff_id in bundle.affordance_ids:
        if aff_id not in substrate.affordances:
            missing.append(f"affordance id {aff_id!r}")
            continue
        aff = substrate.affordances[aff_id]
        for mat_name in aff.materials:
            if mat_name not in substrate.materials:
                missing.append(
                    f"material name {mat_name!r} (via affordance {aff_id!r})"
                )

    if missing:
        raise ValueError(
            f"bundle {bundle.id!r} has unresolved references: " + "; ".join(missing)
        )
