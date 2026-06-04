"""Files-as-substrate loader — markdown + YAML frontmatter is the source of truth.

The authorable substrate (teleo-affective, understanding, rules, affordances,
bundles) lives as markdown files under `substrate/`, one file per entity, with
`filename stem == frontmatter id`. Each file is YAML frontmatter (the structured
fields) followed by a body (the one prose field: `content` for pool elements,
`description` for affordances and bundles).

Materials are mostly NOT loaded here — their captured surfaces are code-owned
(`material_surfaces.MATERIAL_SURFACES`) and injected into `Substrate.materials`,
because the surface (schema) must stay glued to its function in the registry.
The one exception is **dynamic materials** authored at runtime by Practice
Management: those live as files under `substrate/dynamic_materials/`, and the
loader rebuilds their callables via `registry.build_dynamic_material_function`
as it reads them — they have no hand-written function to glue a surface to.

Validation is graceful: a bundle whose references don't resolve is skipped and
recorded in `errors` (logged by the server), never raised — so one bad file
cannot take the server down. The engagement bundle is the one flagged
`engagement: true`; exactly one is required.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from practice_theory_implementation.engagement_aliases import (
    HISTORICAL_ENGAGEMENT_IDS,
)
from practice_theory_implementation.material_surfaces import MATERIAL_SURFACES
from practice_theory_implementation.types import (
    Affordance,
    Bundle,
    Invariant,
    Material,
    PoolElement,
    Substrate,
    validate_bundle,
)

SUBSTRATE_DIR_ENV = "PRACTICE_SUBSTRATE_DIR"
_DEFAULT_ROOT = Path(__file__).resolve().parents[2] / "substrate"


@dataclass(frozen=True, slots=True, kw_only=True)
class LoadedSubstrate:
    """The result of loading the file substrate: ready-to-project objects + errors."""

    substrate: Substrate
    bundles: dict[str, Bundle]          # switchable catalog; engagement excluded
    engagement_bundle: Bundle | None    # the `engagement: true` bundle
    errors: list[str]                   # non-fatal problems, for the caller to log


def _resolve_root(root: str | Path | None) -> Path:
    if root is not None:
        return Path(root)
    return Path(os.environ.get(SUBSTRATE_DIR_ENV) or _DEFAULT_ROOT)


def substrate_root(root: str | Path | None = None) -> Path:
    """Resolve the substrate directory, the way both loader and writer must.

    Public so `substrate_writer` resolves the same root the loader reads from
    (`PRACTICE_SUBSTRATE_DIR`, else the repo `substrate/`).
    """
    return _resolve_root(root)


def split_frontmatter(text: str, *, source: str) -> tuple[dict[str, Any], str]:
    """Split a `---`-fenced YAML frontmatter block from the markdown body."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        raise ValueError(f"{source}: missing leading '---' frontmatter fence")
    try:
        close = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        raise ValueError(f"{source}: unterminated frontmatter (no closing '---')") from None
    data = yaml.safe_load("\n".join(lines[1:close])) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{source}: frontmatter is not a mapping")
    body = "\n".join(lines[close + 1:]).strip()
    return data, body


def _read_dir(directory: Path, errors: list[str]) -> list[tuple[str, dict[str, Any], str]]:
    """Return (stem, frontmatter, body) for each *.md in directory, sorted by name."""
    out: list[tuple[str, dict[str, Any], str]] = []
    if not directory.is_dir():
        return out
    for path in sorted(directory.glob("*.md")):
        try:
            fm, body = split_frontmatter(path.read_text(encoding="utf-8"), source=str(path))
        except ValueError as exc:
            errors.append(str(exc))
            continue
        out.append((path.stem, fm, body))
    return out


def _load_pool(root: Path, pool: str, errors: list[str]) -> dict[str, PoolElement]:
    result: dict[str, PoolElement] = {}
    for stem, fm, body in _read_dir(root / pool, errors):
        if fm.get("id") != stem:
            errors.append(f"{pool}/{stem}.md: frontmatter id {fm.get('id')!r} != filename")
            continue
        result[stem] = PoolElement(id=stem, name=str(fm.get("name", stem)), content=body)
    return result


def _load_affordances(root: Path, errors: list[str]) -> dict[str, Affordance]:
    result: dict[str, Affordance] = {}
    for stem, fm, body in _read_dir(root / "affordances", errors):
        if fm.get("id") != stem:
            errors.append(f"affordances/{stem}.md: frontmatter id {fm.get('id')!r} != filename")
            continue
        result[stem] = Affordance(
            id=stem,
            name=str(fm.get("name", stem)),
            description=body,
            materials=tuple(fm.get("materials") or ()),
        )
    return result


def _load_dynamic_materials(
    root: Path, errors: list[str], code_surfaces: dict[str, Material]
) -> dict[str, Material]:
    """Load PM-authored dynamic materials, rebuilding each callable as we read.

    Each file carries the material's surface (`name`, `input_schema`) and an
    `implementation` block; the loader registers the rebuilt callable into the
    function registry so the material is invocable straight after a load. Graceful:
    a bad implementation or a name that collides with a code-owned surface is
    recorded in `errors` and skipped, never raised. Registry is imported lazily —
    its module imports the materials package, and importing it at module scope
    would weigh down the very early `pools`/`bundles` import of this loader.
    """
    from practice_theory_implementation import registry

    result: dict[str, Material] = {}
    for stem, fm, body in _read_dir(root / "dynamic_materials", errors):
        if fm.get("name") != stem:
            errors.append(
                f"dynamic_materials/{stem}.md: frontmatter name {fm.get('name')!r} != filename"
            )
            continue
        name = stem  # validated equal to frontmatter name; typed str
        if name in code_surfaces:
            errors.append(
                f"dynamic_materials/{stem}.md: name collides with code-owned material"
            )
            continue
        implementation = fm.get("implementation")
        if not isinstance(implementation, dict):
            errors.append(f"dynamic_materials/{stem}.md: missing/invalid implementation")
            continue
        try:
            registry.register_dynamic_material(name, implementation)
        except (TypeError, ValueError) as exc:
            errors.append(f"dynamic_materials/{stem}.md: {exc}")
            continue
        result[name] = Material(
            name=name, description=body, input_schema=fm.get("input_schema") or {}
        )
    return result


def _load_invariants(root: Path, errors: list[str]) -> dict[str, Invariant]:
    """Load governed deterministic invariants from `invariants/*.md`.

    Graceful: a malformed predicate or missing field is recorded in `errors` and
    skipped, never raised. Tombstoned invariants are still loaded (their file is
    kept); the evaluator filters them out by `status`.
    """
    from practice_theory_implementation.invariant_engine import validate_predicate

    result: dict[str, Invariant] = {}
    for stem, fm, body in _read_dir(root / "invariants", errors):
        if fm.get("id") != stem:
            errors.append(f"invariants/{stem}.md: frontmatter id {fm.get('id')!r} != filename")
            continue
        status = fm.get("status", "active")
        if status not in ("active", "tombstoned"):
            errors.append(f"invariants/{stem}.md: invalid status {status!r}")
            continue
        forbid_when = fm.get("forbid_when")
        if not isinstance(forbid_when, dict):
            errors.append(f"invariants/{stem}.md: missing/invalid forbid_when predicate")
            continue
        if predicate_error := validate_predicate(forbid_when):
            errors.append(f"invariants/{stem}.md: {predicate_error}")
            continue
        trigger = fm.get("trigger")
        friction_kind = fm.get("friction_kind")
        if not isinstance(trigger, str) or not isinstance(friction_kind, str):
            errors.append(f"invariants/{stem}.md: trigger and friction_kind must be strings")
            continue
        result[stem] = Invariant(
            id=stem,
            name=str(fm.get("name", stem)),
            trigger=trigger,
            friction_kind=friction_kind,
            message=str(fm.get("message", "")),
            forbid_when=forbid_when,
            content=body,
            status=status,  # type: ignore[arg-type]
            mode=fm.get("mode", "detect"),  # type: ignore[arg-type]
            tombstoned_at=fm.get("tombstoned_at"),
            tombstone_reason=fm.get("tombstone_reason"),
        )
    return result


def _load_bundles(root: Path, errors: list[str]) -> tuple[dict[str, Bundle], list[Bundle]]:
    catalog: dict[str, Bundle] = {}
    engagements: list[Bundle] = []
    for stem, fm, body in _read_dir(root / "bundles", errors):
        if fm.get("id") != stem:
            errors.append(f"bundles/{stem}.md: frontmatter id {fm.get('id')!r} != filename")
            continue
        if stem in HISTORICAL_ENGAGEMENT_IDS:
            errors.append(
                f"bundles/{stem}.md: historical engagement id is reserved; "
                "do not load it as a practice bundle"
            )
            continue
        mode = fm.get("mode", "somatic")
        if mode not in ("somatic", "autonomic"):
            errors.append(f"bundles/{stem}.md: invalid mode {mode!r}")
            continue
        bundle = Bundle(
            id=stem,
            name=str(fm.get("name", stem)),
            description=body,
            teleo_affective_ids=tuple(fm.get("teleo_affective_ids") or ()),
            understanding_ids=tuple(fm.get("understanding_ids") or ()),
            rules_ids=tuple(fm.get("rules_ids") or ()),
            affordance_ids=tuple(fm.get("affordance_ids") or ()),
            mode=mode,  # type: ignore[arg-type]
        )
        if fm.get("engagement") is True:
            engagements.append(bundle)
        else:
            catalog[stem] = bundle
    return catalog, engagements


def load_substrate(
    *,
    root: str | Path | None = None,
    material_surfaces: dict[str, Material],
) -> LoadedSubstrate:
    """Load the file substrate into a Substrate + bundle catalog + engagement bundle.

    Graceful: reference problems land in `errors`, not exceptions. Materials come
    from `material_surfaces` (code), not files.
    """
    base = _resolve_root(root)
    errors: list[str] = []
    code_surfaces = dict(material_surfaces)
    dynamic_surfaces = _load_dynamic_materials(base, errors, code_surfaces)
    substrate = Substrate(
        teleo_affective=_load_pool(base, "teleo_affective", errors),
        understanding=_load_pool(base, "understanding", errors),
        rules=_load_pool(base, "rules", errors),
        affordances=_load_affordances(base, errors),
        materials={**code_surfaces, **dynamic_surfaces},
        invariants=_load_invariants(base, errors),
    )
    catalog, engagements = _load_bundles(base, errors)

    engagement: Bundle | None = None
    if len(engagements) == 1:
        engagement = engagements[0]
    elif not engagements:
        errors.append("no bundle is marked `engagement: true`")
    else:
        errors.append(f"multiple engagement bundles: {sorted(b.id for b in engagements)}")
        engagement = engagements[0]

    valid: dict[str, Bundle] = {}
    for bid, bundle in catalog.items():
        try:
            validate_bundle(bundle, substrate)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        valid[bid] = bundle
    if engagement is not None:
        try:
            validate_bundle(engagement, substrate)
        except ValueError as exc:
            errors.append(f"engagement bundle {engagement.id!r} invalid: {exc}")

    return LoadedSubstrate(
        substrate=substrate, bundles=valid, engagement_bundle=engagement, errors=errors
    )


# --- module-level cached load: a single source for pools.py + bundles/__init__ ---

_LOADED: LoadedSubstrate | None = None


def loaded() -> LoadedSubstrate:
    """Return the cached load, loading once on first call."""
    global _LOADED
    if _LOADED is None:
        _LOADED = load_substrate(material_surfaces=MATERIAL_SURFACES)
    return _LOADED


def reload_from_disk() -> LoadedSubstrate:
    """Drop the cache and re-read the files (used by pm_reload_seed_substrate)."""
    global _LOADED
    _LOADED = None
    return loaded()
