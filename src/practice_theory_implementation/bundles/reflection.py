"""The Reflection practice bundle — small, second-in-catalog practice.

A minimal practice so step 6's switching has something to switch between.
Reflection records a short written reflection from the user verbatim; the
single affordance reaches for a single mock material.
"""

from __future__ import annotations

from practice_theory_implementation.types import Bundle

REFLECTION = Bundle(
    id="reflection",
    name="Reflection",
    description=(
        "Record a short written reflection from the user, dated and stored "
        "verbatim."
    ),
    teleo_affective_ids=("te_reflection",),
    understanding_ids=("und_reflection",),
    rules_ids=("rule_reflection_verbatim",),
    affordance_ids=("record_reflection",),
    mode="somatic",
)
