---
id: rule_calendar_writes_need_explicit_authorization
name: Calendar writes require explicit authorization
---
Do not create, update, delete, or respond to a live calendar event from implication, convenience, or inferred intent. Before invoking a live calendar write material, the current enactment must contain explicit user authorization for the event details being written: calendar/account, event id where applicable, title and time or all-day date range where applicable, attendees if any, response status where applicable, and whether notifications should be sent. If any of those are missing, invite the user's stance instead of writing.
