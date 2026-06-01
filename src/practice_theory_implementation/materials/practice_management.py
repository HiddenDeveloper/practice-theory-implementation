"""Meta-materials for Practice Management — the substrate-mutating functions.

Each function updates the in-memory Substrate (so amendments are visible to the
next projection). Reads are read-through on the in-memory Substrate.

Phase A of the files-as-substrate migration: amendments are **in-memory only**
and do not persist across restart — the authorable substrate now lives in the
`substrate/` files (the single source of truth), and a file write-path will
restore persistence in Phase B. Until then, durable changes are made by editing
the files (and `pm_reload_seed_substrate` re-reads them).

These functions are bound to module-level state — the substrate and the bundle
catalog — wired by the server at startup via `configure(...)`.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from practice_theory_implementation.types import (
    Affordance,
    Bundle,
    Material,
    PoolElement,
    Substrate,
)

POOL_ELEMENT_POOLS = ("teleo_affective", "understanding", "rules")

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
    raise ValueError(
        f"unknown pool {pool!r}; must be one of "
        f"{list(POOL_ELEMENT_POOLS) + ['affordances', 'materials']}"
    )


def pm_reload_seed_substrate() -> Mapping[str, Any]:
    """Re-read the substrate files (and reload material code) from source."""
    return _need_source_reloader()()


# --- pool element create / amend ------------------------------------------


def pm_create_element(pool: str, id: str, name: str, content: str) -> dict[str, Any]:  # noqa: A002
    s, _ = _need_substrate()
    if pool not in POOL_ELEMENT_POOLS:
        return {"error": f"unknown pool {pool!r}"}
    pool_dict = _pool_dict_for(s, pool)
    if id in pool_dict:
        return {"error": f"id {id!r} already exists in {pool!r}"}
    pool_dict[id] = PoolElement(id=id, name=name, content=content)
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
    pool_dict[id] = PoolElement(
        id=id,
        name=name if name is not None else current.name,
        content=content if content is not None else current.content,
    )
    return {"amended": {"pool": pool, "id": id}}


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
    s.affordances[id] = Affordance(
        id=id, name=name, description=description, materials=tuple(materials)
    )
    return {"created": {"affordance": id, "materials": materials}}


def pm_amend_affordance(
    id: str,  # noqa: A002
    name: str | None = None,
    description: str | None = None,
    materials: list[str] | None = None,
) -> dict[str, Any]:
    s, _ = _need_substrate()
    if id not in s.affordances:
        return {"error": f"affordance {id!r} not found"}
    current = s.affordances[id]
    if materials is not None:
        missing = [m for m in materials if m not in s.materials]
        if missing:
            return {"error": f"materials not in substrate: {missing}"}
    s.affordances[id] = Affordance(
        id=id,
        name=name if name is not None else current.name,
        description=description if description is not None else current.description,
        materials=tuple(materials) if materials is not None else current.materials,
    )
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
    s.materials[name] = Material(
        name=name, description=description, input_schema=dict(input_schema)
    )
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
    s, _ = _need_substrate()
    if name not in s.materials:
        return {"error": f"material {name!r} not found"}
    if implementation is not None:
        try:
            _need_function_registrar()(name, implementation)
        except (TypeError, ValueError) as exc:
            return {"error": f"invalid material implementation: {exc}"}
    current = s.materials[name]
    s.materials[name] = Material(
        name=name,
        description=description if description is not None else current.description,
        input_schema=dict(input_schema) if input_schema is not None else current.input_schema,
    )
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
    s, catalog = _need_substrate()
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
    catalog[id] = Bundle(
        id=id,
        name=name,
        description=description,
        teleo_affective_ids=tuple(teleo_affective_ids),
        understanding_ids=tuple(understanding_ids),
        rules_ids=tuple(rules_ids),
        affordance_ids=tuple(affordance_ids),
        mode=mode,  # type: ignore[arg-type]
    )
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
    missing = _validate_bundle_refs(
        s,
        teleo_affective_ids=new_teleo,
        understanding_ids=new_und,
        rules_ids=new_rules,
        affordance_ids=new_aff,
    )
    if missing:
        return {"error": f"unresolved references: {missing}"}
    catalog[id] = Bundle(
        id=id,
        name=name if name is not None else current.name,
        description=description if description is not None else current.description,
        teleo_affective_ids=tuple(new_teleo),
        understanding_ids=tuple(new_und),
        rules_ids=tuple(new_rules),
        affordance_ids=tuple(new_aff),
        mode=current.mode,
    )
    return {"amended": {"bundle": id}}
