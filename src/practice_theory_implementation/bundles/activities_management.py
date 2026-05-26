"""The Activities Management bundle — a selection of pool IDs.

Step 2 form: the bundle no longer carries inline content. Each id-tuple
resolves into the corresponding pool in `practice_theory_implementation.pools`
to produce the bundle's effective content at projection time (step 3). The
materials behind the affordances are bound to executable code in
`practice_theory_implementation.registry`.
"""

from __future__ import annotations

from practice_theory_implementation.types import Bundle

ACTIVITIES_MANAGEMENT = Bundle(
    id="activities_management",
    name="Activities Management",
    description=(
        "Keep an honest, useful view of the user's physical activities — "
        "what's been done, what the body is showing, what the rhythm looks like."
    ),
    teleo_affective_ids=("te_activities_management",),
    understanding_ids=("und_activities_management",),
    rules_ids=(
        "rule_cite_source",
        "rule_no_intent_inference",
        "rule_no_coaching",
        "rule_no_external_exposure",
    ),
    affordance_ids=(
        "recent_activity",
        "activity_detail",
        "daily_summary",
        "intermittent_walking_analysis",
    ),
    mode="somatic",
)
