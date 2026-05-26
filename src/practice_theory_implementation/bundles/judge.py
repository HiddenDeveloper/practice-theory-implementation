"""The Judge bundle — autonomic practitioner that reads the trail and emits Friction.

The Judge's intelligence is in this bundle's content (teleo-affective,
understanding, rules) — the prose the enacting LLM reads. The materials
underneath are primitives only: list recent enactments, read steps, read
bundles, emit Friction. The deciding (what kinds of Friction to look for,
what content to write, what evidence to include) happens at LLM enactment.
"""

from __future__ import annotations

from practice_theory_implementation.types import Bundle

JUDGE = Bundle(
    id="judge",
    name="Judge",
    description=(
        "Read the trail. Observe what is worth attending to. Emit Friction "
        "observations naming the concern. Do not propose remedies and do not "
        "amend anything — the Smoother decides what to do."
    ),
    teleo_affective_ids=("te_judge",),
    understanding_ids=("und_judge",),
    rules_ids=(
        "rule_judge_examine_before_naming",
        "rule_judge_one_thing_per_friction",
        "rule_judge_observe_not_remediate",
    ),
    affordance_ids=(
        "list_recent_enactments",
        "read_enactment_steps",
        "read_bundle",
        "emit_friction",
    ),
    mode="autonomic",
)
