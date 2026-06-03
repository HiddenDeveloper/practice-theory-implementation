---
id: rule_invite_stance_before_issue
name: Invite the user's stance before issuing
---
Before issuing any reschedule of an event with external attendees, invoke invite_stance to name the choice and hand back. Do not issue past a choice the user has not made. When you hand back at the invited stance with the change staged-but-unissued, leave the open awaiting resumable: name the staging id and the awaited stance in the handback, so that a later enactment — likely the one that resumes after the user answers asynchronously — can find the staging and pick it up. The resting state is correct conduct only while the staging stays findable; an awaiting that no future enactment can locate is the loose end this rule exists to prevent.
