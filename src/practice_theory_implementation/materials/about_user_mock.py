"""Engagement-layer mock material — returns the standing about-the-user record.

A real deployment would back this with a richer store (vector DB, knowledge
graph, accreted notes); here it returns a fixed content for the demo.

**The user named below is the author of the essay series this repo
accompanies, used as concrete demo content so the engagement layer's
about-the-user knowing is visible in the trail rather than abstract.** If
you fork this repo to use any practice for yourself, replace both the
returned dict here AND the `und_about_the_user` pool entry in `pools.py`
with your own content — otherwise the LLM in your session will address you
as "Monyet Batu" and reference the author's essay-writing focus rather than
your own work. The two must stay in sync; the engagement is internally
inconsistent if this mock and the pool prose disagree.
"""

from __future__ import annotations


def consult_about_user() -> dict[str, object]:
    return {
        "name": "Monyet Batu",
        "current_focus": (
            "Writing the third essay in the practice-theory series and the "
            "implementation that accompanies it."
        ),
        "preferences": [
            "plain, direct prose over ornate phrasing",
            "small steps with the doc and code kept in lockstep",
        ],
        "sovereign_over": ["their own work and time", "their words"],
    }
