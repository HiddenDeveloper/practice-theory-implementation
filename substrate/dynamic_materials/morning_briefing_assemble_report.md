---
name: morning_briefing_assemble_report
input_schema:
  type: object
  properties:
    as_of:
      type: string
    email_accounts_checked:
      type: array
      items:
        type: string
    unread_email_summary:
      type: array
      items:
        type: object
        properties:
          account:
            type: string
          thread_or_sender:
            type: string
          subject:
            type: string
          why_it_matters:
            type: string
          suggested_disposition:
            type: string
          source:
            type: string
    site_summaries:
      type: array
      items:
        type: object
        properties:
          site_name:
            type: string
          url:
            type: string
          summary:
            type: string
          source_time:
            type: string
          source:
            type: string
    live_snapshot_summary:
      type: string
    important_items:
      type: array
      items:
        type: string
    follow_ups:
      type: array
      items:
        type: string
    gaps:
      type: array
      items:
        type: string
  required:
  - as_of
implementation:
  kind: echo
---
Capture the final morning briefing as a structured artifact: unread email triage, recurring-site observations, optional live snapshot observations, important items, follow-ups, and named gaps. This material echoes the practitioner-authored report so the trail preserves the briefing basis.
