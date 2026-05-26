"""The Smoother bundle — autonomic practitioner that addresses Friction.

Same Bundle shape as a practice bundle, autonomic. Its affordances reach for
the Smoother's own read/mark materials and for Practice Management's existing
meta-materials (`pm_amend_bundle`, etc.) — the autonomic counterpart to
somatic Practice Management, sharing machinery.
"""

from __future__ import annotations

from practice_theory_implementation.types import Bundle

SMOOTHER = Bundle(
    id="smoother",
    name="Smoother",
    description=(
        "Read pending Friction. Interpret it. Apply the smallest substrate "
        "amendment that addresses what the Friction names. Mark the Friction "
        "addressed. Reuses Practice Management's amendment affordances — "
        "autonomic counterpart, same machinery."
    ),
    teleo_affective_ids=("te_smoother",),
    understanding_ids=("und_smoother",),
    rules_ids=(
        "rule_smoother_address_what_friction_names",
        "rule_smoother_do_not_invent",
        "rule_smoother_mark_when_done",
    ),
    affordance_ids=(
        # Smoother-specific:
        "read_pending_friction",
        "mark_friction_addressed",
        # Reused from Practice Management — the autonomic-somatic reuse hinge:
        "read_pool",
        "amend_pool_element",
        "author_pool_element",
        "amend_affordance",
        "amend_material",
        "amend_bundle",
    ),
    mode="autonomic",
)
