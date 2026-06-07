---
id: update_calendar_event
name: Update a calendar event
materials:
- calendar_user_patch_event
---
Patch fields on an existing event on the user's live Google Calendar. This writes to the calendar even when `send_updates` is `none`; if attendees are present and `send_updates` is `all` or `externalOnly`, notifications may be sent. Use only after the user has explicitly authorized the event id, changed fields, and notification stance in the current enactment.
