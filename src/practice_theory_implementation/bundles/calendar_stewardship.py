"""The Calendar Stewardship practice bundle.

A worked-example practice introduced for the case study essay. The bundle's
discipline — stage before issue, invite stance before notifying attendees —
is what shapes the LLM's behaviour against the calendar mock so the failure
mode (silently moving a meeting and notifying five people) cannot happen
by accident.
"""

from __future__ import annotations

from practice_theory_implementation.types import Bundle

CALENDAR_STEWARDSHIP = Bundle(
    id="calendar_stewardship",
    name="Calendar Stewardship",
    description=(
        "Tend the user's calendar as a record of commitments to people — "
        "not as fields to be edited. Stage proposed changes; invite the "
        "user's stance before any change that notifies attendees; issue "
        "deliberately, never silently."
    ),
    teleo_affective_ids=("te_calendar_stewardship",),
    understanding_ids=("und_meetings_as_commitments",),
    rules_ids=(
        "rule_stage_before_issue",
        "rule_invite_stance_before_issue",
        "rule_no_silent_attendee_changes",
    ),
    affordance_ids=(
        "read_calendar",
        "propose_reschedule",
        "invite_stance",
        "issue_reschedule",
    ),
    mode="somatic",
)
