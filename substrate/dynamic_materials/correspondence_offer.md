---
name: correspondence_offer
input_schema:
  type: object
  properties:
    kind:
      type: string
      enum:
      - attend
      - friction
      - draft
      - stance
      - limit
    correspondent:
      type: string
    subject:
      type: string
    message_excerpt:
      type: string
    literal_layer:
      type: string
    implicit_layer:
      type: string
    evidence:
      type: array
      items:
        type: string
    unresolved_questions:
      type: array
      items:
        type: string
    offered_text:
      type: string
  required:
  - kind
  - offered_text
implementation:
  kind: echo
---
Return a structured correspondence offering without sending, editing, or storing mail. The returned arguments are the artifact for the user to review: an attending, surfaced friction, draft, stance invitation, or boundary declaration.
