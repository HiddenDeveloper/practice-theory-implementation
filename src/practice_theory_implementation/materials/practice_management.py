"""Meta-materials for Practice Management — the substrate-mutating functions.

Each function dual-writes an amendment: it persists the entity to its
`substrate/` file (via `substrate_writer`) **and** updates the in-memory
Substrate (so the change is visible to the next projection without a reload).

Phase B of the files-as-substrate migration: amendments are durable. The
authorable substrate lives in the `substrate/` files (the single source of
truth); writing the file back is what makes an authored change survive a
restart and show up as a reviewable git diff — the dual-write the old SQLite
overlay used to do, now to files. The file is written first, before the
in-memory dict is mutated, so a write failure leaves memory and disk consistent
(no half-applied amendment). `pm_reload_seed_substrate` re-reads the files.

These functions are bound to module-level state — the substrate and the bundle
catalog — wired by the server at startup via `configure(...)`.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from practice_theory_implementation import substrate_writer
from practice_theory_implementation.engagement_aliases import (
    HISTORICAL_ENGAGEMENT_IDS,
)
from practice_theory_implementation.types import (
    Affordance,
    Bundle,
    EvaluationSpec,
    Material,
    PoolElement,
    Substrate,
)

POOL_ELEMENT_POOLS = ("teleo_affective", "understanding", "rules")
_REPO_ROOT = Path(__file__).resolve().parents[3]

# wired by the server at startup
_substrate: Substrate | None = None
_bundle_catalog: dict[str, Bundle] | None = None
_register_material_function: Callable[[str, Mapping[str, Any]], None] | None = None
_reload_source_callback: Callable[[], Mapping[str, Any]] | None = None


def _pool_dict_for(substrate: Substrate, pool: str) -> dict[str, PoolElement]:
    if pool == "teleo_affective":
        return substrate.teleo_affective
    if pool == "understanding":
        return substrate.understanding
    if pool == "rules":
        return substrate.rules
    raise ValueError(f"unknown pool {pool!r}; must be one of {POOL_ELEMENT_POOLS}")


def configure(
    *,
    substrate: Substrate,
    bundle_catalog: dict[str, Bundle],
    register_material_function: Callable[[str, Mapping[str, Any]], None],
    reload_source_callback: Callable[[], Mapping[str, Any]] | None = None,
) -> None:
    """Wire the meta-materials to the live substrate and catalog (in-memory)."""
    global _reload_source_callback
    global _substrate, _bundle_catalog, _register_material_function
    _substrate = substrate
    _bundle_catalog = bundle_catalog
    _register_material_function = register_material_function
    _reload_source_callback = reload_source_callback


def _need_substrate() -> tuple[Substrate, dict[str, Bundle]]:
    if _substrate is None or _bundle_catalog is None:
        raise RuntimeError(
            "practice_management materials not configured; call configure() first"
        )
    return _substrate, _bundle_catalog


def _need_function_registrar() -> Callable[[str, Mapping[str, Any]], None]:
    if _register_material_function is None:
        raise RuntimeError(
            "practice_management materials not configured; call configure() first"
        )
    return _register_material_function


def _need_source_reloader() -> Callable[[], Mapping[str, Any]]:
    if _reload_source_callback is None:
        raise RuntimeError(
            "practice_management source reloader not configured; call configure() first"
        )
    return _reload_source_callback


def _persist(write: Callable[[], Any]) -> dict[str, Any] | None:
    """Run a file write, returning an error dict on failure (else None).

    Called before the in-memory dict is mutated, so a disk failure (OSError) or a
    rejected id/name (ValueError from the writer's path-safety guard) aborts the
    amendment cleanly — memory and the file stay in agreement.
    """
    try:
        write()
    except (OSError, ValueError) as exc:
        return {"error": f"failed to persist amendment to substrate file: {exc}"}
    return None


# --- read ------------------------------------------------------------------


def pm_read_pool(pool: str) -> list[dict[str, Any]]:
    """Return every entry in the named pool, ordered by id."""
    s, _ = _need_substrate()
    if pool in POOL_ELEMENT_POOLS:
        d = _pool_dict_for(s, pool)
        return [
            {"id": e.id, "name": e.name, "content": e.content}
            for e in sorted(d.values(), key=lambda x: x.id)
        ]
    if pool == "affordances":
        return [
            {
                "id": a.id,
                "name": a.name,
                "description": a.description,
                "materials": list(a.materials),
            }
            for a in sorted(s.affordances.values(), key=lambda x: x.id)
        ]
    if pool == "materials":
        return [
            {
                "name": m.name,
                "description": m.description,
                "input_schema": dict(m.input_schema),
            }
            for m in sorted(s.materials.values(), key=lambda x: x.name)
        ]
    if pool == "evaluations":
        return [
            {
                "id": e.id,
                "name": e.name,
                "practice_id": e.practice_id,
                "objective_ref": e.objective_ref,
                "window": e.window,
                "signals": [dict(sig) for sig in e.signals],
                "content": e.content,
            }
            for e in sorted(s.evaluations.values(), key=lambda x: x.id)
        ]
    raise ValueError(
        f"unknown pool {pool!r}; must be one of "
        f"{list(POOL_ELEMENT_POOLS) + ['affordances', 'materials', 'evaluations']}"
    )


def pm_reload_seed_substrate() -> Mapping[str, Any]:
    """Re-read the substrate files (and reload material code) from source."""
    return _need_source_reloader()()


def pm_check_documentation_impact(
    changed_ids: list[str] | None = None,
    changed_files: list[str] | None = None,
    query: str | None = None,
    limit: int = 25,
) -> dict[str, Any]:
    """Find documentation likely affected by a substrate change.

    This is a lightweight impact read, not an automatic edit. It searches
    README/docs/social-media markdown for changed ids, changed file stems, and
    optional query terms so the enacting practitioner can update prose that
    still describes the old substrate or code-supported surface.
    """
    limit = max(1, min(int(limit), 100))
    terms: list[str] = []
    for value in changed_ids or []:
        if value and value not in terms:
            terms.append(value)
    for value in changed_files or []:
        path = Path(value)
        for candidate in (path.as_posix(), path.stem):
            if candidate and candidate != "." and candidate not in terms:
                terms.append(candidate)
    if query:
        for candidate in query.split():
            stripped = candidate.strip()
            if stripped and stripped not in terms:
                terms.append(stripped)
    if not terms:
        return {
            "error": "provide at least one changed_id, changed_file, or query term"
        }

    docs: list[Path] = []
    readme = _REPO_ROOT / "README.md"
    if readme.is_file():
        docs.append(readme)
    for dirname in ("docs", "social-media"):
        base = _REPO_ROOT / dirname
        if base.is_dir():
            docs.extend(sorted(base.rglob("*.md")))

    matches: list[dict[str, Any]] = []
    lowered_terms = [(term, term.lower()) for term in terms]
    for path in docs:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for line_number, line in enumerate(lines, start=1):
            lowered = line.lower()
            hit_terms = [
                original for original, lowered_term in lowered_terms
                if lowered_term in lowered
            ]
            if not hit_terms:
                continue
            matches.append(
                {
                    "file": str(path.relative_to(_REPO_ROOT)),
                    "line": line_number,
                    "terms": hit_terms,
                    "text": line.strip()[:240],
                }
            )
            if len(matches) >= limit:
                return {"terms": terms, "matches": matches, "truncated": True}
    return {"terms": terms, "matches": matches, "truncated": False}


# --- pool element create / amend ------------------------------------------


def pm_create_element(pool: str, id: str, name: str, content: str) -> dict[str, Any]:  # noqa: A002
    s, _ = _need_substrate()
    if pool not in POOL_ELEMENT_POOLS:
        return {"error": f"unknown pool {pool!r}"}
    pool_dict = _pool_dict_for(s, pool)
    if id in pool_dict:
        return {"error": f"id {id!r} already exists in {pool!r}"}
    element = PoolElement(id=id, name=name, content=content)
    if err := _persist(lambda: substrate_writer.write_pool_element(pool, element)):
        return err
    pool_dict[id] = element
    return {"created": {"pool": pool, "id": id}}


def pm_amend_element(
    pool: str,
    id: str,  # noqa: A002
    name: str | None = None,
    content: str | None = None,
) -> dict[str, Any]:
    s, _ = _need_substrate()
    if pool not in POOL_ELEMENT_POOLS:
        return {"error": f"unknown pool {pool!r}"}
    pool_dict = _pool_dict_for(s, pool)
    if id not in pool_dict:
        return {"error": f"id {id!r} not in {pool!r}"}
    current = pool_dict[id]
    element = PoolElement(
        id=id,
        name=name if name is not None else current.name,
        content=content if content is not None else current.content,
    )
    if err := _persist(lambda: substrate_writer.write_pool_element(pool, element)):
        return err
    pool_dict[id] = element
    return {"amended": {"pool": pool, "id": id}}


# --- governed invariant author / amend / tombstone ------------------------


# --- evaluation spec create / amend ---------------------------------------


def _coerce_signals(signals: object) -> list[dict[str, Any]] | str:
    """Validate the signals payload, returning a list of dicts or an error str.

    Runs the engine's deterministic well-formedness gate (known signal kinds +
    required list params) so a malformed evaluator cannot be authored.
    """
    from practice_theory_implementation.materials.practice_evaluation import (
        validate_signals,
    )

    if not isinstance(signals, list) or not all(isinstance(s, Mapping) for s in signals):
        return "signals must be a list of mappings"
    coerced = [dict(s) for s in signals]
    if errors := validate_signals(coerced):
        return "invalid signals: " + "; ".join(errors)
    return coerced


def pm_create_evaluation(
    id: str,  # noqa: A002
    name: str,
    practice_id: str,
    signals: list[Mapping[str, Any]],
    objective_ref: str | None = None,
    derived_from: str | None = None,
    window: int = 8,
) -> dict[str, Any]:
    """Author a new evaluation spec — a practice's declarative measure of whether
    it delivers its objective. Data, not code: `signals` are generic signal kinds
    parameterised for the practice, and `objective_ref` should name one of the
    practice bundle's teleo-affective ids so the evaluator is not vacuous."""
    s, _ = _need_substrate()
    if id in s.evaluations:
        return {"error": f"evaluation {id!r} already exists"}
    coerced = _coerce_signals(signals)
    if isinstance(coerced, str):
        return {"error": coerced}
    if not isinstance(window, int) or window < 1:
        return {"error": "window must be a positive integer"}
    spec = EvaluationSpec(
        id=id,
        name=name,
        practice_id=practice_id,
        window=window,
        objective_ref=objective_ref,
        derived_from=derived_from,
        signals=tuple(coerced),
    )
    if err := _persist(lambda: substrate_writer.write_evaluation(spec)):
        return err
    s.evaluations[id] = spec
    return {"created": {"evaluation": id, "practice_id": practice_id}}


def pm_amend_evaluation(
    id: str,  # noqa: A002
    name: str | None = None,
    practice_id: str | None = None,
    signals: list[Mapping[str, Any]] | None = None,
    objective_ref: str | None = None,
    derived_from: str | None = None,
    window: int | None = None,
) -> dict[str, Any]:
    """Amend an existing evaluation spec. Omitted fields keep their current value;
    `objective_ref`/`derived_from` are only changed when explicitly passed."""
    s, _ = _need_substrate()
    if id not in s.evaluations:
        return {"error": f"evaluation {id!r} not found"}
    current = s.evaluations[id]
    if signals is not None:
        coerced = _coerce_signals(signals)
        if isinstance(coerced, str):
            return {"error": coerced}
        new_signals = tuple(coerced)
    else:
        new_signals = current.signals
    if window is not None and (not isinstance(window, int) or window < 1):
        return {"error": "window must be a positive integer"}
    spec = EvaluationSpec(
        id=id,
        name=name if name is not None else current.name,
        practice_id=practice_id if practice_id is not None else current.practice_id,
        window=window if window is not None else current.window,
        objective_ref=objective_ref if objective_ref is not None else current.objective_ref,
        derived_from=derived_from if derived_from is not None else current.derived_from,
        signals=new_signals,
    )
    if err := _persist(lambda: substrate_writer.write_evaluation(spec)):
        return err
    s.evaluations[id] = spec
    return {"amended": {"evaluation": id}}


# --- affordance create / amend --------------------------------------------


def pm_create_affordance(
    id: str,  # noqa: A002
    name: str,
    description: str,
    materials: list[str],
) -> dict[str, Any]:
    s, _ = _need_substrate()
    if id in s.affordances:
        return {"error": f"affordance id {id!r} already exists"}
    missing = [m for m in materials if m not in s.materials]
    if missing:
        return {"error": f"materials not in substrate: {missing}"}
    affordance = Affordance(
        id=id, name=name, description=description, materials=tuple(materials)
    )
    if err := _persist(lambda: substrate_writer.write_affordance(affordance)):
        return err
    s.affordances[id] = affordance
    return {"created": {"affordance": id, "materials": materials}}


def pm_amend_affordance(
    id: str,  # noqa: A002
    name: str | None = None,
    description: str | None = None,
    materials: list[str] | None = None,
    check_materials: list[str] | None = None,
) -> dict[str, Any]:
    s, _ = _need_substrate()
    if id not in s.affordances:
        return {"error": f"affordance {id!r} not found"}
    current = s.affordances[id]
    if materials is not None:
        missing = [m for m in materials if m not in s.materials]
        if missing:
            return {"error": f"materials not in substrate: {missing}"}
    if check_materials is not None:
        # A check-material reference must resolve to a real material — this is how
        # a determinable check (now a material) is wired to the affordance it
        # governs, replacing the retired author_invariant path.
        missing = [m for m in check_materials if m not in s.materials]
        if missing:
            return {"error": f"check-materials not in substrate: {missing}"}
    affordance = Affordance(
        id=id,
        name=name if name is not None else current.name,
        description=description if description is not None else current.description,
        materials=tuple(materials) if materials is not None else current.materials,
        check_materials=(
            tuple(check_materials)
            if check_materials is not None
            else current.check_materials
        ),
    )
    if err := _persist(lambda: substrate_writer.write_affordance(affordance)):
        return err
    s.affordances[id] = affordance
    return {"amended": {"affordance": id}}


# --- material create / amend ----------------------------------------------


def pm_create_material(
    name: str,
    description: str,
    input_schema: Mapping[str, Any],
    implementation: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    s, _ = _need_substrate()
    if name in s.materials:
        return {"error": f"material {name!r} already exists"}
    if implementation is not None:
        try:
            _need_function_registrar()(name, implementation)
        except (TypeError, ValueError) as exc:
            return {"error": f"invalid material implementation: {exc}"}
        if err := _persist(
            lambda: substrate_writer.write_dynamic_material(
                name, description, input_schema, implementation
            )
        ):
            return err
    s.materials[name] = Material(
        name=name, description=description, input_schema=dict(input_schema)
    )
    # A material with no implementation has no file home (and no registry
    # binding) — it cannot be invoked and does not survive a restart.
    created: dict[str, Any] = {"material": name, "persisted": implementation is not None}
    if implementation is not None:
        created["function"] = implementation.get("kind")
    return {"created": created}


def pm_amend_material(
    name: str,
    description: str | None = None,
    input_schema: Mapping[str, Any] | None = None,
    implementation: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    s, _ = _need_substrate()
    if name not in s.materials:
        return {"error": f"material {name!r} not found"}
    if implementation is not None:
        try:
            _need_function_registrar()(name, implementation)
        except (TypeError, ValueError) as exc:
            return {"error": f"invalid material implementation: {exc}"}
    current = s.materials[name]
    new_description = description if description is not None else current.description
    new_schema = dict(input_schema) if input_schema is not None else dict(current.input_schema)
    # Recover the existing implementation when amending only the surface — the
    # spec lives in the file, not the in-memory Material, so we must read it back
    # to rewrite the file faithfully. A material with no file is code-owned (no
    # implementation): its surface amendment stays in-memory only.
    new_impl: Mapping[str, Any] | None = implementation
    if new_impl is None:
        existing = substrate_writer.read_dynamic_material(name)
        if existing is not None:
            new_impl = existing.get("implementation")
    if new_impl is not None:
        if err := _persist(
            lambda: substrate_writer.write_dynamic_material(
                name, new_description, new_schema, new_impl
            )
        ):
            return err
    s.materials[name] = Material(
        name=name, description=new_description, input_schema=new_schema
    )
    return {"amended": {"material": name, "persisted": new_impl is not None}}


# --- bundle create / amend ------------------------------------------------


def _validate_bundle_refs(
    s: Substrate,
    *,
    teleo_affective_ids: list[str],
    understanding_ids: list[str],
    rules_ids: list[str],
    affordance_ids: list[str],
    evaluation_ids: list[str],
) -> list[str]:
    missing: list[str] = []
    for i in teleo_affective_ids:
        if i not in s.teleo_affective:
            missing.append(f"teleo_affective {i!r}")
    for i in understanding_ids:
        if i not in s.understanding:
            missing.append(f"understanding {i!r}")
    for i in rules_ids:
        if i not in s.rules:
            missing.append(f"rules {i!r}")
    for i in affordance_ids:
        if i not in s.affordances:
            missing.append(f"affordance {i!r}")
    for i in evaluation_ids:
        if i not in s.evaluations:
            missing.append(f"evaluation {i!r}")
    return missing


def _evaluation_coverage_errors(
    s: Substrate, *, evaluation_ids: list[str], teleo_affective_ids: list[str]
) -> list[str]:
    """The mechanical promotion gate: an eval-spec may only be wired into a
    bundle when its `objective_ref` names one of that bundle's teleo-affective
    ids, so a vacuous evaluator cannot be activated."""
    errors: list[str] = []
    teleo = set(teleo_affective_ids)
    for sid in evaluation_ids:
        spec = s.evaluations.get(sid)
        if spec is None:
            continue  # missing-ref already reported by _validate_bundle_refs
        if not spec.objective_ref:
            errors.append(f"evaluation {sid!r} declares no objective_ref")
        elif spec.objective_ref not in teleo:
            errors.append(
                f"evaluation {sid!r} objective_ref {spec.objective_ref!r} is not "
                f"a teleo-affective id of this bundle"
            )
    return errors


def pm_create_bundle(
    id: str,  # noqa: A002
    name: str,
    description: str,
    teleo_affective_ids: list[str],
    understanding_ids: list[str],
    rules_ids: list[str],
    affordance_ids: list[str],
    mode: str = "somatic",
    evaluation_ids: list[str] | None = None,
) -> dict[str, Any]:
    s, catalog = _need_substrate()
    if id in HISTORICAL_ENGAGEMENT_IDS:
        return {
            "error": (
                f"bundle id {id!r} is reserved as a historical engagement id; "
                "do not recreate it as a switchable practice bundle"
            )
        }
    if id in catalog:
        return {"error": f"bundle {id!r} already exists in catalog"}
    if mode not in ("somatic", "autonomic"):
        return {"error": f"mode must be 'somatic' or 'autonomic', got {mode!r}"}
    new_eval = list(evaluation_ids) if evaluation_ids is not None else []
    missing = _validate_bundle_refs(
        s,
        teleo_affective_ids=teleo_affective_ids,
        understanding_ids=understanding_ids,
        rules_ids=rules_ids,
        affordance_ids=affordance_ids,
        evaluation_ids=new_eval,
    )
    if missing:
        return {"error": f"unresolved references: {missing}"}
    if coverage := _evaluation_coverage_errors(
        s, evaluation_ids=new_eval, teleo_affective_ids=teleo_affective_ids
    ):
        return {"error": f"evaluation coverage gate: {coverage}"}
    bundle = Bundle(
        id=id,
        name=name,
        description=description,
        teleo_affective_ids=tuple(teleo_affective_ids),
        understanding_ids=tuple(understanding_ids),
        rules_ids=tuple(rules_ids),
        affordance_ids=tuple(affordance_ids),
        evaluation_ids=tuple(new_eval),
        mode=mode,  # type: ignore[arg-type]
    )
    if err := _persist(lambda: substrate_writer.write_bundle(bundle)):
        return err
    catalog[id] = bundle
    return {"created": {"bundle": id, "name": name, "mode": mode}}


def pm_amend_bundle(
    id: str,  # noqa: A002
    name: str | None = None,
    description: str | None = None,
    teleo_affective_ids: list[str] | None = None,
    understanding_ids: list[str] | None = None,
    rules_ids: list[str] | None = None,
    affordance_ids: list[str] | None = None,
    evaluation_ids: list[str] | None = None,
) -> dict[str, Any]:
    s, catalog = _need_substrate()
    if id not in catalog:
        return {"error": f"bundle {id!r} not in catalog"}
    current = catalog[id]
    new_teleo = teleo_affective_ids if teleo_affective_ids is not None else list(
        current.teleo_affective_ids
    )
    new_und = understanding_ids if understanding_ids is not None else list(
        current.understanding_ids
    )
    new_rules = rules_ids if rules_ids is not None else list(current.rules_ids)
    new_aff = affordance_ids if affordance_ids is not None else list(
        current.affordance_ids
    )
    # Preserve the evaluation layer unless explicitly changed — an amend that
    # omits this key must not silently drop a practice's eval-spec link.
    new_eval = evaluation_ids if evaluation_ids is not None else list(
        current.evaluation_ids
    )
    missing = _validate_bundle_refs(
        s,
        teleo_affective_ids=new_teleo,
        understanding_ids=new_und,
        rules_ids=new_rules,
        affordance_ids=new_aff,
        evaluation_ids=new_eval,
    )
    if missing:
        return {"error": f"unresolved references: {missing}"}
    if coverage := _evaluation_coverage_errors(
        s, evaluation_ids=new_eval, teleo_affective_ids=new_teleo
    ):
        return {"error": f"evaluation coverage gate: {coverage}"}
    bundle = Bundle(
        id=id,
        name=name if name is not None else current.name,
        description=description if description is not None else current.description,
        teleo_affective_ids=tuple(new_teleo),
        understanding_ids=tuple(new_und),
        rules_ids=tuple(new_rules),
        affordance_ids=tuple(new_aff),
        evaluation_ids=tuple(new_eval),
        mode=current.mode,
    )
    if err := _persist(lambda: substrate_writer.write_bundle(bundle)):
        return err
    catalog[id] = bundle
    return {"amended": {"bundle": id}}
