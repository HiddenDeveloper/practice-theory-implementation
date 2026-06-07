---
id: create_calendar_event
name: Create a calendar event
materials:
- calendar_user_create_event
---
Create an event on the user's live Google Calendar. This writes to the calendar even when `send_updates` is `none`; if attendees are present and `send_updates` is `all` or `externalOnly`, invitations or update notifications may be sent. Use only after the user has explicitly authorized the event details in the current enactment.
