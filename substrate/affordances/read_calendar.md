---
id: read_calendar
name: Read the calendar
materials:
- cal_list_events
- calendar_user_list_events
---
List upcoming events in a date range to see what is on the calendar before proposing any change. Prefer the live `calendar_user_list_events` material when Google Calendar OAuth is available; use the deterministic `cal_list_events` mock for verification/demo runs. Returns attendee counts and an external-attendee flag so the practitioner knows what a change would touch.
