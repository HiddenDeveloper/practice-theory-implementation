"""Projection — turn (bundle, substrate, registry) into a self-contained practice.

A bundle is an ID selection over the substrate; the substrate holds the pools;
the registry binds material names to executable code. None of those three on
their own is something a consumer can hold and use. Projection folds the three
together into a single ProjectedPractice — every pool id resolved into the
content it points at, every material's executable captured into a snapshot of
the registry, all validation done once at projection time so the consumer can
just use the result.

A projected practice is frozen for its lifetime. Later amendments to the
substrate or the registry do not affect projections already in hand; a new
projection picks up the changes.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from practice_theory_implementation.types import (
    Affordance,
    Bundle,
    Material,
    PoolElement,
    Substrate,
    validate_bundle,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class ProjectedPractice:
    """A bundle resolved against the substrate, with registry bindings attached.

    Self-contained: holds the resolved pool content inline plus a snapshot of
    the bindings needed for its materials. Consumers do not need to consult
    the substrate or the registry.
    """

    id: str
    name: str
    description: str
    teleo_affective: tuple[PoolElement, ...]
    understanding: tuple[PoolElement, ...]
    rules: tuple[PoolElement, ...]
    affordances: tuple[Affordance, ...]
    materials: tuple[Material, ...]
    bindings: Mapping[str, Callable[..., object]]

    def affordance_by_id(self, affordance_id: str) -> Affordance:
        for aff in self.affordances:
            if aff.id == affordance_id:
                return aff
        raise KeyError(
            f"no affordance {affordance_id!r} in practice {self.id!r} "
            f"(available: {[a.id for a in self.affordances]})"
        )

    def invoke(
        self,
        *,
        affordance_id: str,
        material_name: str,
        arguments: Mapping[str, object],
    ) -> object:
        """Resolve and call an affordance's material end-to-end.

        Confirms the affordance exists in this practice, the material is one
        the affordance reaches for, and the binding is attached. Then calls
        the bound function with the arguments as kwargs.
        """
        aff = self.affordance_by_id(affordance_id)
        if material_name not in aff.materials:
            raise ValueError(
                f"material {material_name!r} is not reached for by affordance "
                f"{affordance_id!r} (available: {list(aff.materials)})"
            )
        fn = self.bindings[material_name]
        return fn(**dict(arguments))


def compose_composition(practice: ProjectedPractice) -> str:
    """Render a ProjectedPractice as a Markdown composition.

    The composition is what the LLM enacting the practice reads as guidance —
    teleo-affective + understanding + rules + the affordance list, formatted
    as headings and bullets. Used by the server's `continuous_self` and
    `current_practice` tools to surface the practice's content as text, and
    by `autonomic_adapters.compose_brief` as the LLM's system prompt.
    """
    parts: list[str] = [
        f"# {practice.name}",
        "",
        practice.description,
        "",
        "## Teleo-affective",
        "",
    ]
    for el in practice.teleo_affective:
        parts.extend([f"### {el.name}", "", el.content, ""])

    parts.extend(["## Understanding", ""])
    for el in practice.understanding:
        parts.extend([f"### {el.name}", "", el.content, ""])

    parts.extend(["## Rules", ""])
    for el in practice.rules:
        parts.append(f"- **{el.name}** — {el.content}")
    parts.append("")

    parts.extend(["## Affordances available", ""])
    for aff in practice.affordances:
        parts.append(f"- `{aff.id}` ({aff.name}) — {aff.description}")
    parts.append("")

    return "\n".join(parts)


def _merge_unique_by_id(
    eng: tuple[Any, ...],
    pract: tuple[Any, ...],
) -> tuple[Any, ...]:
    """Engagement-first, dedupe by `.id`, return tuple. Used for TA/U/rules/aff."""
    seen: set[str] = set()
    out: list[Any] = []
    for el in eng:
        if el.id not in seen:
            out.append(el)
            seen.add(el.id)
    for el in pract:
        if el.id not in seen:
            out.append(el)
            seen.add(el.id)
    return tuple(out)


def project(
    bundle: Bundle,
    substrate: Substrate,
    registry: Mapping[str, Callable[..., object]],
    *,
    engagement: ProjectedPractice | None = None,
) -> ProjectedPractice:
    """Project a bundle into a self-contained ProjectedPractice.

    Validates bundle against substrate, derives the bundle's material set from
    its affordances (after engagement merge if provided), checks every
    derived material has a binding in the registry, and snapshots the
    resolved content and bindings into a frozen ProjectedPractice. Raises
    ValueError on any unresolved reference.

    If `engagement` is provided, its content is merged additively into the
    result (engagement-first, deduped by id). This is the apprenticeship
    layer's standing arrangement folded into the projected practice.
    """
    validate_bundle(bundle, substrate)

    base_teleo = tuple(substrate.teleo_affective[i] for i in bundle.teleo_affective_ids)
    base_und = tuple(substrate.understanding[i] for i in bundle.understanding_ids)
    base_rules = tuple(substrate.rules[i] for i in bundle.rules_ids)
    base_aff = tuple(substrate.affordances[i] for i in bundle.affordance_ids)

    if engagement is not None:
        teleo = _merge_unique_by_id(engagement.teleo_affective, base_teleo)
        understanding = _merge_unique_by_id(engagement.understanding, base_und)
        rules = _merge_unique_by_id(engagement.rules, base_rules)
        affordances = _merge_unique_by_id(engagement.affordances, base_aff)
    else:
        teleo = base_teleo
        understanding = base_und
        rules = base_rules
        affordances = base_aff

    seen: set[str] = set()
    material_names: list[str] = []
    for aff in affordances:
        for name in aff.materials:
            if name not in seen:
                material_names.append(name)
                seen.add(name)

    missing_bindings = [n for n in material_names if n not in registry]
    if missing_bindings:
        raise ValueError(
            f"bundle {bundle.id!r} has materials without registry bindings: "
            f"{missing_bindings}"
        )

    materials = tuple(substrate.materials[n] for n in material_names)
    bindings: dict[str, Callable[..., object]] = {n: registry[n] for n in material_names}

    return ProjectedPractice(
        id=bundle.id,
        name=bundle.name,
        description=bundle.description,
        teleo_affective=teleo,
        understanding=understanding,
        rules=rules,
        affordances=affordances,
        materials=materials,
        bindings=bindings,
    )
