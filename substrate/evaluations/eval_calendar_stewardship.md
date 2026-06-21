---
id: eval_calendar_stewardship
name: Calendar Stewardship - objective delivery
practice_id: calendar_stewardship
objective_ref: te_calendar_stewardship
derived_from: calendar_stewardship@friction-455
window: 8
signals:
- id: reads_calendar_before_calendar_conduct
  kind: affordance_coverage
  required_materials:
  - cal_list_events
  - calendar_user_list_events
  detail: Calendar stewardship should inspect the calendar before offering, staging,
    issuing, or otherwise changing calendar commitments. Count either the deterministic
    `cal_list_events` material used by the `read_calendar` affordance in verification/demo
    runs or the live `calendar_user_list_events` material when Google Calendar OAuth
    is available. Without a calendar read, the practice cannot make visible what commitments
    or people a change touches.
- id: stewardship_produces_calendar_outcomes
  kind: outcome_presence
  outcome_materials:
  - cal_propose_reschedule
  - cal_invite_stance
  - cal_issue_reschedule
  - calendar_user_create_event
  - calendar_user_patch_event
  - calendar_user_delete_event
  - calendar_user_respond_event
  max_consecutive_without: 6
  detail: The objective is to steward commitments, not only inspect them. A long run
    with no staged proposal, stance invitation, issued change, or authorized live
    calendar action may be appropriate quiet stewardship or may be a stall for the
    Judge to inspect.
- id: not_repeating_calendar_shape_without_progress
  kind: shape_repetition
  max_identical: 4
  detail: Identical calendar enactment shapes repeated across many passes suggest
    the practitioner may be cycling through the same moves rather than advancing the
    user's calendar commitment work.
- id: declared_calendar_gaps_are_resolving
  kind: recurring_summary_marker
  markers:
  - calendar access gap
  - oauth
  - authorization missing
  - awaiting stance
  - staged-but-unissued
  max_consecutive: 5
  detail: Repeated disclosure of the same calendar access, authorization, or awaiting-stance
    gap is useful only if the gap remains findable and eventually resolves; repeated
    markers beyond the threshold merit judgement.
---

