---
name: morning_briefing_capture_site_check
input_schema:
  type: object
  properties:
    site_name:
      type: string
    url:
      type: string
    checked_at:
      type: string
    headline_items:
      type: array
      items:
        type: string
    source_notes:
      type: array
      items:
        type: string
    follow_up_needed:
      type: array
      items:
        type: string
    access_gap:
      type: string
  required:
  - site_name
  - checked_at
implementation:
  kind: echo
---
Record the result of checking one of the user's recurring morning sites. This material is an echo/capture surface: the practitioner remains responsible for obtaining page evidence through available browser, web, or user-supplied context, and must name access gaps plainly.
