"""The engagement bundle — the standing arrangement, not a practice.

Same `Bundle` shape as a practice bundle (structural convenience), but
ontologically distinct: an engagement is the container within which practices
are reached for, not itself something the harness reaches for. The
apprenticeship server projects this bundle once at startup and merges its
content into every practice projection.

Lives in `bundles/` alongside the practice bundles but is not listed in the
catalog (`BUNDLES`) — it cannot be switched to, only inherited from.
"""

from __future__ import annotations

from practice_theory_implementation.types import Bundle

USER_FOCUSED_ENGAGEMENT = Bundle(
    id="user_focused_engagement",
    name="User-Focused Engagement",
    description=(
        "The engagement-recipe — projected at session scope as the substrate "
        "of being-here-for-this-user across whichever practice is reached for. "
        "Same shape as any practice; its content is inherited additively by "
        "every practice engaged from within the engagement."
    ),
    teleo_affective_ids=("te_user_focused_engagement",),
    understanding_ids=(
        "und_engagement_substrate",
        "und_engagement_landing_nodes",
        "und_memory_stores",
        "und_about_the_user",
    ),
    rules_ids=(
        "rule_dont_displace",
        "rule_offer_not_instruct",
        "rule_honour_what_brought",
        "rule_episodic_memory_read_only",
    ),
    affordance_ids=(
        "about_the_user",
        "about_user_profile",
        "about_self",
        "about_shared_context",
        "read_non_episodic_memory",
        "write_non_episodic_memory",
        "ensure_self_rooted_spine",
        "recall_relevant_episodes",
        "recall_recent_engagement",
        "recall_contextual_episodes",
    ),
)
