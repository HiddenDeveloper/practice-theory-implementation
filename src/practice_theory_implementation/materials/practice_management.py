"""Meta-materials for Practice Management — the substrate-mutating functions.

Each function writes to the SubstrateStore overlay (so amendments survive
restart) and updates the in-memory Substrate (so amendments are visible to
the next projection). Reads are read-through on the in-memory Substrate; the
overlay is only consulted at startup.

These functions are bound to module-level state — the substrate, the bundle
catalog, and the overlay store — wired by the server at startup via
`configure(...)`. The choice of module-level state is deliberate: the
substrate is a singleton at this stage, and threading three dependencies
through the registry's callable interface would add ceremony without buying
anything for a step-7 implementation.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from practice_theory_implementation.substrate_store import (
    POOL_ELEMENT_POOLS,
    SubstrateStore,
    _pool_dict_for,
)
from practice_theory_implementation.types import (
    Affordance,
    Bundle,
    Material,
    PoolElement,
    Substrate,
)

# wired by the server at startup
_substrate: Substrate | None = None
_bundle_catalog: dict[str, Bundle] | None = None
_store: SubstrateStore | None = None
_register_material_function: Callable[[str, Mapping[str, Any]], None] | None = None


def configure(
    *,
    substrate: Substrate,
    bundle_catalog: dict[str, Bundle],
    store: SubstrateStore,
    register_material_function: Callable[[str, Mapping[str, Any]], None],
) -> None:
    """Wire the meta-materials to the live substrate, catalog, and overlay store."""
    global _substrate, _bundle_catalog, _store, _register_material_function
    _substrate = substrate
    _bundle_catalog = bundle_catalog
    _store = store
    _register_material_function = register_material_function


def _need_substrate() -> tuple[Substrate, dict[str, Bundle], SubstrateStore]:
    if _substrate is None or _bundle_catalog is None or _store is None:
        raise RuntimeError(
            "practice_management materials not configured; call configure() first"
        )
    return _substrate, _bundle_catalog, _store


def _need_function_registrar() -> Callable[[str, Mapping[str, Any]], None]:
    if _register_material_function is None:
        raise RuntimeError(
            "practice_management materials not configured; call configure() first"
        )
    return _register_material_function


# --- read ------------------------------------------------------------------


def pm_read_pool(pool: str) -> list[dict[str, Any]]:
    """Return every entry in the named pool, ordered by id."""
    s, _, _ = _need_substrate()
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
    raise ValueError(
        f"unknown pool {pool!r}; must be one of "
        f"{list(POOL_ELEMENT_POOLS) + ['affordances', 'materials']}"
    )


# --- pool element create / amend ------------------------------------------


def pm_create_element(pool: str, id: str, name: str, content: str) -> dict[str, Any]:  # noqa: A002
    s, _, store = _need_substrate()
    if pool not in POOL_ELEMENT_POOLS:
        return {"error": f"unknown pool {pool!r}"}
    pool_dict = _pool_dict_for(s, pool)
    if id in pool_dict:
        return {"error": f"id {id!r} already exists in {pool!r}"}
    element = PoolElement(id=id, name=name, content=content)
    store.upsert_pool_element(pool, element)
    pool_dict[id] = element
    return {"created": {"pool": pool, "id": id}}


def pm_amend_element(
    pool: str,
    id: str,  # noqa: A002
    name: str | None = None,
    content: str | None = None,
) -> dict[str, Any]:
    s, _, store = _need_substrate()
    if pool not in POOL_ELEMENT_POOLS:
        return {"error": f"unknown pool {pool!r}"}
    pool_dict = _pool_dict_for(s, pool)
    if id not in pool_dict:
        return {"error": f"id {id!r} not in {pool!r}"}
    current = pool_dict[id]
    amended = PoolElement(
        id=id,
        name=name if name is not None else current.name,
        content=content if content is not None else current.content,
    )
    store.upsert_pool_element(pool, amended)
    pool_dict[id] = amended
    return {"amended": {"pool": pool, "id": id}}


# --- affordance create / amend --------------------------------------------


def pm_create_affordance(
    id: str,  # noqa: A002
    name: str,
    description: str,
    materials: list[str],
) -> dict[str, Any]:
    s, _, store = _need_substrate()
    if id in s.affordances:
        return {"error": f"affordance id {id!r} already exists"}
    missing = [m for m in materials if m not in s.materials]
    if missing:
        return {"error": f"materials not in substrate: {missing}"}
    aff = Affordance(id=id, name=name, description=description, materials=tuple(materials))
    store.upsert_affordance(aff)
    s.affordances[id] = aff
    return {"created": {"affordance": id, "materials": materials}}


def pm_amend_affordance(
    id: str,  # noqa: A002
    name: str | None = None,
    description: str | None = None,
    materials: list[str] | None = None,
) -> dict[str, Any]:
    s, _, store = _need_substrate()
    if id not in s.affordances:
        return {"error": f"affordance {id!r} not found"}
    current = s.affordances[id]
    if materials is not None:
        missing = [m for m in materials if m not in s.materials]
        if missing:
            return {"error": f"materials not in substrate: {missing}"}
    amended = Affordance(
        id=id,
        name=name if name is not None else current.name,
        description=description if description is not None else current.description,
        materials=tuple(materials) if materials is not None else current.materials,
    )
    store.upsert_affordance(amended)
    s.affordances[id] = amended
    return {"amended": {"affordance": id}}


# --- material create / amend ----------------------------------------------


def pm_create_material(
    name: str,
    description: str,
    input_schema: Mapping[str, Any],
    implementation: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    s, _, store = _need_substrate()
    if name in s.materials:
        return {"error": f"material {name!r} already exists"}
    if implementation is not None:
        try:
            _need_function_registrar()(name, implementation)
        except (TypeError, ValueError) as exc:
            return {"error": f"invalid material implementation: {exc}"}
    mat = Material(name=name, description=description, input_schema=dict(input_schema))
    store.upsert_material(mat)
    if implementation is not None:
        store.upsert_material_function(name, dict(implementation))
    s.materials[name] = mat
    created: dict[str, Any] = {"material": name}
    if implementation is not None:
        created["function"] = implementation.get("kind")
    return {"created": created}


def pm_amend_material(
    name: str,
    description: str | None = None,
    input_schema: Mapping[str, Any] | None = None,
    implementation: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    s, _, store = _need_substrate()
    if name not in s.materials:
        return {"error": f"material {name!r} not found"}
    if implementation is not None:
        try:
            _need_function_registrar()(name, implementation)
        except (TypeError, ValueError) as exc:
            return {"error": f"invalid material implementation: {exc}"}
    current = s.materials[name]
    amended = Material(
        name=name,
        description=description if description is not None else current.description,
        input_schema=dict(input_schema) if input_schema is not None else current.input_schema,
    )
    store.upsert_material(amended)
    if implementation is not None:
        store.upsert_material_function(name, dict(implementation))
    s.materials[name] = amended
    return {"amended": {"material": name}}


# --- bundle create / amend ------------------------------------------------


def _validate_bundle_refs(
    s: Substrate,
    *,
    teleo_affective_ids: list[str],
    understanding_ids: list[str],
    rules_ids: list[str],
    affordance_ids: list[str],
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
    return missing


def pm_create_bundle(
    id: str,  # noqa: A002
    name: str,
    description: str,
    teleo_affective_ids: list[str],
    understanding_ids: list[str],
    rules_ids: list[str],
    affordance_ids: list[str],
    mode: str = "somatic",
) -> dict[str, Any]:
    s, catalog, store = _need_substrate()
    if id in catalog:
        return {"error": f"bundle {id!r} already exists in catalog"}
    if mode not in ("somatic", "autonomic"):
        return {"error": f"mode must be 'somatic' or 'autonomic', got {mode!r}"}
    missing = _validate_bundle_refs(
        s,
        teleo_affective_ids=teleo_affective_ids,
        understanding_ids=understanding_ids,
        rules_ids=rules_ids,
        affordance_ids=affordance_ids,
    )
    if missing:
        return {"error": f"unresolved references: {missing}"}
    bundle = Bundle(
        id=id,
        name=name,
        description=description,
        teleo_affective_ids=tuple(teleo_affective_ids),
        understanding_ids=tuple(understanding_ids),
        rules_ids=tuple(rules_ids),
        affordance_ids=tuple(affordance_ids),
        mode=mode,  # type: ignore[arg-type]
    )
    store.upsert_bundle(bundle)
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
) -> dict[str, Any]:
    s, catalog, store = _need_substrate()
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
    missing = _validate_bundle_refs(
        s,
        teleo_affective_ids=new_teleo,
        understanding_ids=new_und,
        rules_ids=new_rules,
        affordance_ids=new_aff,
    )
    if missing:
        return {"error": f"unresolved references: {missing}"}
    amended = Bundle(
        id=id,
        name=name if name is not None else current.name,
        description=description if description is not None else current.description,
        teleo_affective_ids=tuple(new_teleo),
        understanding_ids=tuple(new_und),
        rules_ids=tuple(new_rules),
        affordance_ids=tuple(new_aff),
        mode=current.mode,
    )
    store.upsert_bundle(amended)
    catalog[id] = amended
    return {"amended": {"bundle": id}}
