"""Mutable substrate overlay — SQLite-backed amendments on top of the seed pools.

The effective substrate at runtime is `seed (pools.py) + overlay (this file)`.
The overlay is loaded at server startup and merged into the in-memory
Substrate. Practice Management's meta-materials write here (so amendments
survive restart) and also update the in-memory Substrate (so amendments are
visible to subsequent projections immediately).

Schema is intentionally small: one row per substrate entity, last-write-wins.
Soft delete, history, and audit are out of scope at step 7.
"""

from __future__ import annotations

import json
import os
import sqlite3
from collections.abc import Iterable
from contextlib import contextmanager
from pathlib import Path

from practice_theory_implementation.types import (
    Affordance,
    Bundle,
    Material,
    PoolElement,
    Substrate,
)

DEFAULT_SUBSTRATE_PATH = Path("data/substrate.db")
SUBSTRATE_PATH_ENV = "PRACTICE_SUBSTRATE_PATH"

POOL_ELEMENT_POOLS = ("teleo_affective", "understanding", "rules")

SCHEMA = """
CREATE TABLE IF NOT EXISTS pool_element_overlay (
    pool    TEXT NOT NULL,
    id      TEXT NOT NULL,
    name    TEXT NOT NULL,
    content TEXT NOT NULL,
    PRIMARY KEY (pool, id)
);

CREATE TABLE IF NOT EXISTS affordance_overlay (
    id              TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    description     TEXT NOT NULL,
    materials_json  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS material_overlay (
    name              TEXT PRIMARY KEY,
    description       TEXT NOT NULL,
    input_schema_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS bundle_overlay (
    id                      TEXT PRIMARY KEY,
    name                    TEXT NOT NULL,
    description             TEXT NOT NULL,
    teleo_affective_ids     TEXT NOT NULL,
    understanding_ids       TEXT NOT NULL,
    rules_ids               TEXT NOT NULL,
    affordance_ids          TEXT NOT NULL,
    mode                    TEXT NOT NULL DEFAULT 'somatic'
);
"""


def _resolve_path(override: str | None = None) -> Path:
    raw = override or os.environ.get(SUBSTRATE_PATH_ENV) or str(DEFAULT_SUBSTRATE_PATH)
    return Path(raw)


def _pool_dict_for(substrate: Substrate, pool: str) -> dict[str, PoolElement]:
    if pool == "teleo_affective":
        return substrate.teleo_affective
    if pool == "understanding":
        return substrate.understanding
    if pool == "rules":
        return substrate.rules
    raise ValueError(
        f"unknown pool {pool!r}; must be one of {POOL_ELEMENT_POOLS}"
    )


class SubstrateStore:
    """SQLite-backed overlay for the five pools and the bundle catalog."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = _resolve_path(str(path) if path is not None else None)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path), isolation_level=None)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(SCHEMA)

    def close(self) -> None:
        self._conn.close()

    @contextmanager
    def _cursor(self):  # type: ignore[no-untyped-def]
        cur = self._conn.cursor()
        try:
            yield cur
        finally:
            cur.close()

    # --- read ---------------------------------------------------------------

    def overlay_pool_elements(self) -> Iterable[tuple[str, PoolElement]]:
        with self._cursor() as cur:
            cur.execute(
                "SELECT pool, id, name, content FROM pool_element_overlay"
            )
            for r in cur.fetchall():
                yield (
                    str(r["pool"]),
                    PoolElement(id=r["id"], name=r["name"], content=r["content"]),
                )

    def overlay_affordances(self) -> Iterable[Affordance]:
        with self._cursor() as cur:
            cur.execute(
                "SELECT id, name, description, materials_json FROM affordance_overlay"
            )
            for r in cur.fetchall():
                yield Affordance(
                    id=r["id"],
                    name=r["name"],
                    description=r["description"],
                    materials=tuple(json.loads(r["materials_json"])),
                )

    def overlay_materials(self) -> Iterable[Material]:
        with self._cursor() as cur:
            cur.execute(
                "SELECT name, description, input_schema_json FROM material_overlay"
            )
            for r in cur.fetchall():
                yield Material(
                    name=r["name"],
                    description=r["description"],
                    input_schema=json.loads(r["input_schema_json"]),
                )

    def overlay_bundles(self) -> Iterable[Bundle]:
        with self._cursor() as cur:
            cur.execute(
                "SELECT id, name, description, teleo_affective_ids, "
                "understanding_ids, rules_ids, affordance_ids, mode FROM bundle_overlay"
            )
            for r in cur.fetchall():
                yield Bundle(
                    id=r["id"],
                    name=r["name"],
                    description=r["description"],
                    teleo_affective_ids=tuple(json.loads(r["teleo_affective_ids"])),
                    understanding_ids=tuple(json.loads(r["understanding_ids"])),
                    rules_ids=tuple(json.loads(r["rules_ids"])),
                    affordance_ids=tuple(json.loads(r["affordance_ids"])),
                    mode=r["mode"],
                )

    # --- write --------------------------------------------------------------

    def upsert_pool_element(self, pool: str, element: PoolElement) -> None:
        if pool not in POOL_ELEMENT_POOLS:
            raise ValueError(f"unknown pool {pool!r}")
        with self._cursor() as cur:
            cur.execute(
                "INSERT INTO pool_element_overlay(pool, id, name, content) "
                "VALUES (?, ?, ?, ?) "
                "ON CONFLICT(pool, id) DO UPDATE SET name=excluded.name, "
                "content=excluded.content",
                (pool, element.id, element.name, element.content),
            )

    def upsert_affordance(self, affordance: Affordance) -> None:
        with self._cursor() as cur:
            cur.execute(
                "INSERT INTO affordance_overlay(id, name, description, materials_json) "
                "VALUES (?, ?, ?, ?) "
                "ON CONFLICT(id) DO UPDATE SET name=excluded.name, "
                "description=excluded.description, materials_json=excluded.materials_json",
                (
                    affordance.id,
                    affordance.name,
                    affordance.description,
                    json.dumps(list(affordance.materials)),
                ),
            )

    def upsert_material(self, material: Material) -> None:
        with self._cursor() as cur:
            cur.execute(
                "INSERT INTO material_overlay(name, description, input_schema_json) "
                "VALUES (?, ?, ?) "
                "ON CONFLICT(name) DO UPDATE SET description=excluded.description, "
                "input_schema_json=excluded.input_schema_json",
                (
                    material.name,
                    material.description,
                    json.dumps(dict(material.input_schema)),
                ),
            )

    def upsert_bundle(self, bundle: Bundle) -> None:
        with self._cursor() as cur:
            cur.execute(
                "INSERT INTO bundle_overlay("
                "id, name, description, teleo_affective_ids, understanding_ids,"
                " rules_ids, affordance_ids, mode"
                ") VALUES (?, ?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(id) DO UPDATE SET name=excluded.name, "
                "description=excluded.description, "
                "teleo_affective_ids=excluded.teleo_affective_ids, "
                "understanding_ids=excluded.understanding_ids, "
                "rules_ids=excluded.rules_ids, "
                "affordance_ids=excluded.affordance_ids, "
                "mode=excluded.mode",
                (
                    bundle.id,
                    bundle.name,
                    bundle.description,
                    json.dumps(list(bundle.teleo_affective_ids)),
                    json.dumps(list(bundle.understanding_ids)),
                    json.dumps(list(bundle.rules_ids)),
                    json.dumps(list(bundle.affordance_ids)),
                    bundle.mode,
                ),
            )


def apply_overlay_to_substrate(substrate: Substrate, store: SubstrateStore) -> None:
    """Merge the overlay's contents into the in-memory substrate. Overlay wins."""
    for pool, element in store.overlay_pool_elements():
        _pool_dict_for(substrate, pool)[element.id] = element
    for aff in store.overlay_affordances():
        substrate.affordances[aff.id] = aff
    for mat in store.overlay_materials():
        substrate.materials[mat.name] = mat


def apply_overlay_to_bundles(
    bundle_catalog: dict[str, Bundle],
    store: SubstrateStore,
) -> None:
    """Merge the overlay's bundles into the in-memory bundle catalog."""
    for bundle in store.overlay_bundles():
        bundle_catalog[bundle.id] = bundle
