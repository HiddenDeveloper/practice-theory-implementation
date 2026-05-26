"""Engagement-layer mock material — returns the standing about-the-user record.

A real deployment would back this with a richer store (vector DB, knowledge
graph, accreted notes); here it returns a fixed content for the demo. The
content matches the `und_about_the_user` pool element so the engagement is
internally consistent.
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
