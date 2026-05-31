"""The Practice Management bundle — the somatic meta-practice.

Authors and amends the substrate at runtime, on the user's behalf. Same
Bundle shape as any practice; its distinctness is in what its materials do
(mutate the substrate) rather than in its data shape.
"""

from __future__ import annotations

from practice_theory_implementation.types import Bundle

PRACTICE_MANAGEMENT = Bundle(
    id="practice_management",
    name="Practice Management",
    description=(
        "Author and amend the substrate at runtime — pool elements, "
        "affordances, materials, and bundles — on the user's behalf."
    ),
    teleo_affective_ids=("te_practice_management",),
    understanding_ids=("und_practice_management",),
    rules_ids=(
        "rule_pm_preview_before_apply",
        "rule_pm_no_id_collision",
        "rule_pm_amend_additively",
    ),
    affordance_ids=(
        "read_pool",
        "author_pool_element",
        "amend_pool_element",
        "author_affordance",
        "amend_affordance",
        "author_material",
        "amend_material",
        "author_bundle",
        "amend_bundle",
        "reload_seed_substrate",
    ),
    mode="somatic",
)
