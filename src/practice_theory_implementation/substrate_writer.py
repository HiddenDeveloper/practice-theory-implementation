"""Files-as-substrate writer — the Phase B persistence path for amendments.

Practice Management and the Smoother author the substrate at runtime. Phase A
made the markdown + YAML-frontmatter files under `substrate/` the single source
of truth but kept amendments in-memory only. This module restores durability by
writing one entity back to its `<id>.md` file, so an authored change survives a
restart and shows up as a reviewable git diff — no overlay store reintroduced.

Each write is the mirror of the loader's read (`substrate_loader`): the
structured fields become deterministic YAML frontmatter (stable key order via
`sort_keys=False`), and the one prose field (`content` for pool elements,
`description` for affordances/bundles/materials) becomes the **verbatim body** —
never reflowed, so round-tripping prose is lossless. Writes are atomic
(write-temp-then-rename) so a crash mid-write cannot leave a half-written file.

The write root is resolved exactly as the loader resolves its read root
(`PRACTICE_SUBSTRATE_DIR`, else the repo `substrate/`), so the writer and loader
always agree on where a file lives.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

from practice_theory_implementation.substrate_loader import (
    split_frontmatter,
    substrate_root,
)
from practice_theory_implementation.types import Affordance, Bundle, PoolElement

DYNAMIC_MATERIALS_DIR = "dynamic_materials"


def _render(frontmatter: dict[str, Any], body: str) -> str:
    """Render `---`-fenced frontmatter + verbatim body, the loader's read shape.

    Frontmatter key order is preserved (`sort_keys=False`) so re-serialising an
    unchanged entity is a no-op diff. The body is written exactly as given.
    """
    fm = yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=True)
    return f"---\n{fm}---\n{body}\n"


def _write_atomic(path: Path, text: str) -> None:
    """Write `text` to `path` atomically (temp file in the same dir + rename)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.parent / (path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def _path_for(subdir: str, stem: str, *, root: str | Path | None) -> Path:
    return substrate_root(root) / subdir / f"{stem}.md"


def write_pool_element(
    pool: str, element: PoolElement, *, root: str | Path | None = None
) -> Path:
    """Persist one pool element to `<pool>/<id>.md` (pool == directory name)."""
    path = _path_for(pool, element.id, root=root)
    _write_atomic(path, _render({"id": element.id, "name": element.name}, element.content))
    return path


def write_affordance(
    affordance: Affordance, *, root: str | Path | None = None
) -> Path:
    """Persist one affordance to `affordances/<id>.md`."""
    path = _path_for("affordances", affordance.id, root=root)
    frontmatter = {
        "id": affordance.id,
        "name": affordance.name,
        "materials": list(affordance.materials),
    }
    _write_atomic(path, _render(frontmatter, affordance.description))
    return path


def write_bundle(bundle: Bundle, *, root: str | Path | None = None) -> Path:
    """Persist one bundle to `bundles/<id>.md`.

    `engagement` is emitted explicitly (mirroring the seed files). The flag is a
    loader-level concept not carried on the `Bundle` dataclass, so an *amend*
    preserves whatever the existing file declared — never silently demoting the
    `engagement: true` bundle to a catalog bundle. A brand-new bundle has no file
    yet, so it defaults to `False`.
    """
    path = _path_for("bundles", bundle.id, root=root)
    frontmatter = {
        "id": bundle.id,
        "name": bundle.name,
        "mode": bundle.mode,
        "engagement": _existing_engagement_flag(path),
        "teleo_affective_ids": list(bundle.teleo_affective_ids),
        "understanding_ids": list(bundle.understanding_ids),
        "rules_ids": list(bundle.rules_ids),
        "affordance_ids": list(bundle.affordance_ids),
    }
    _write_atomic(path, _render(frontmatter, bundle.description))
    return path


def _existing_engagement_flag(path: Path) -> bool:
    """Return the `engagement` flag of an existing bundle file, else False."""
    if not path.is_file():
        return False
    fm, _ = split_frontmatter(path.read_text(encoding="utf-8"), source=str(path))
    return fm.get("engagement") is True


def write_dynamic_material(
    name: str,
    description: str,
    input_schema: Mapping[str, Any],
    implementation: Mapping[str, Any],
    *,
    root: str | Path | None = None,
) -> Path:
    """Persist one PM-authored dynamic material to `dynamic_materials/<name>.md`.

    Dynamic materials are the single exception to "materials live in code": they
    are authored at runtime, so their surface (name, schema) and rebuildable
    `implementation` block (`kind: constant|echo|expression`) are stored as a
    file, and the loader rebuilds the callable at load.
    """
    path = _path_for(DYNAMIC_MATERIALS_DIR, name, root=root)
    frontmatter = {
        "name": name,
        "input_schema": _plain(input_schema),
        "implementation": _plain(implementation),
    }
    _write_atomic(path, _render(frontmatter, description))
    return path


def read_dynamic_material(
    name: str, *, root: str | Path | None = None
) -> dict[str, Any] | None:
    """Return {description, input_schema, implementation} for a persisted dynamic
    material, or None if it has no file (e.g. a code-owned material surface).

    Used by `pm_amend_material` to recover the existing `implementation` block
    when an amendment changes only the description or schema — the implementation
    spec is not retained in the in-memory surface, only in the file.
    """
    path = _path_for(DYNAMIC_MATERIALS_DIR, name, root=root)
    if not path.is_file():
        return None
    fm, body = split_frontmatter(path.read_text(encoding="utf-8"), source=str(path))
    return {
        "description": body,
        "input_schema": fm.get("input_schema") or {},
        "implementation": fm.get("implementation"),
    }


def _plain(value: Any) -> Any:
    """Coerce a mapping/sequence to plain dict/list so YAML emits clean blocks.

    Input schemas and implementations arrive as JSON-ish Mappings (sometimes
    immutable proxies); `yaml.safe_dump` only handles built-in containers.
    """
    if isinstance(value, Mapping):
        return {k: _plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    return value
