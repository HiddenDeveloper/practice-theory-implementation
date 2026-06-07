---
id: delete_calendar_event
name: Delete a calendar event
materials:
- calendar_user_delete_event
---
Delete an event from the user's live Google Calendar. This is destructive even when `send_updates` is `none`; if attendees are present and `send_updates` is `all` or `externalOnly`, cancellation notifications may be sent. Use only after the user has explicitly authorized the event id and notification stance in the current enactment.
