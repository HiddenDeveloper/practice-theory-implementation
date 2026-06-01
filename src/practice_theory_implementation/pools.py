"""The in-memory substrate — now loaded from the file substrate.

Historically this module hand-built the five pools as Python literals. The
authorable substrate (teleo-affective, understanding, rules, affordances,
bundles) now lives as markdown + YAML-frontmatter files under `substrate/`,
read by `substrate_loader`. Materials' captured surfaces stay in code
(`material_surfaces.MATERIAL_SURFACES`) because the schema must travel with its
registry function.

This module is a thin compatibility shim: it exposes the loaded `substrate`
object for the call sites that still `from .pools import substrate`.
"""

from __future__ import annotations

from practice_theory_implementation.substrate_loader import loaded
from practice_theory_implementation.types import Substrate

substrate: Substrate = loaded().substrate
