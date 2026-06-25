"""Material captured surfaces — code-owned, paired with the registry functions.

Each Material here is the *captured surface* (name, description, input_schema)
of a material; its executable function lives in `registry.FUNCTIONS`. The two
halves are code-owned and travel together (the schema describes the function's
parameters), so they live in code, not in the file-based substrate. The loader
injects these into `Substrate.materials`.
"""

from __future__ import annotations

from practice_theory_implementation.types import Material
from practice_theory_implementation.visualizations import activity_type_keys

_GMAIL_SEARCH_SCHEMA = {
    "type": "object",
    "properties": {
        "query": {"type": "string"},
        "max_results": {"type": "integer", "minimum": 1, "maximum": 100},
        "page_token": {"type": "string"},
        "include_spam_trash": {"type": "boolean"},
    },
}

_GMAIL_GET_THREAD_SCHEMA = {
    "type": "object",
    "properties": {
        "thread_id": {"type": "string"},
        "format": {"type": "string", "enum": ["full", "metadata", "minimal"]},
    },
    "required": ["thread_id"],
}

_GMAIL_LIST_DRAFTS_SCHEMA = {
    "type": "object",
    "properties": {
        "query": {"type": "string"},
        "max_results": {"type": "integer", "minimum": 1, "maximum": 100},
        "page_token": {"type": "string"},
    },
}

_GMAIL_DRAFT_SCHEMA = {
    "type": "object",
    "properties": {
        "to": {"type": "array", "items": {"type": "string"}, "minItems": 1},
        "subject": {"type": "string"},
        "body": {"type": "string"},
        "cc": {"type": "array", "items": {"type": "string"}},
        "bcc": {"type": "array", "items": {"type": "string"}},
        "reply_to_thread_id": {"type": "string"},
        "reply_to_message_id": {"type": "string"},
    },
    "required": ["to", "subject", "body"],
}

_GMAIL_UPDATE_DRAFT_SCHEMA = {
    "type": "object",
    "properties": {
        "draft_id": {"type": "string"},
        **_GMAIL_DRAFT_SCHEMA["properties"],
    },
    "required": ["draft_id", "to", "subject", "body"],
}

_GMAIL_DRAFT_ID_SCHEMA = {
    "type": "object",
    "properties": {"draft_id": {"type": "string"}},
    "required": ["draft_id"],
}

_CALENDAR_LIST_EVENTS_SCHEMA = {
    "type": "object",
    "properties": {
        "start_date": {"type": "string", "format": "date"},
        "end_date": {"type": "string", "format": "date"},
        "calendar_id": {"type": "string"},
        "max_results": {"type": "integer", "minimum": 1, "maximum": 2500},
        "single_events": {"type": "boolean"},
    },
    "required": ["start_date", "end_date"],
}

_CALENDAR_EVENT_WRITE_PROPERTIES = {
    "calendar_id": {"type": "string"},
    "summary": {"type": "string"},
    "description": {"type": "string"},
    "location": {"type": "string"},
    "start_datetime": {"type": "string"},
    "end_datetime": {"type": "string"},
    "start_date": {"type": "string", "format": "date"},
    "end_date": {"type": "string", "format": "date"},
    "time_zone": {"type": "string"},
    "attendees": {"type": "array", "items": {"type": "string"}},
    "send_updates": {"type": "string", "enum": ["none", "all", "externalOnly"]},
    "transparency": {"type": "string", "enum": ["opaque", "transparent"]},
    "visibility": {"type": "string", "enum": ["default", "public", "private", "confidential"]},
}

_CALENDAR_CREATE_EVENT_SCHEMA = {
    "type": "object",
    "properties": _CALENDAR_EVENT_WRITE_PROPERTIES,
    "required": ["summary"],
}

_CALENDAR_PATCH_EVENT_SCHEMA = {
    "type": "object",
    "properties": {
        "event_id": {"type": "string"},
        **_CALENDAR_EVENT_WRITE_PROPERTIES,
    },
    "required": ["event_id"],
}

_CALENDAR_DELETE_EVENT_SCHEMA = {
    "type": "object",
    "properties": {
        "event_id": {"type": "string"},
        "calendar_id": {"type": "string"},
        "send_updates": {"type": "string", "enum": ["none", "all", "externalOnly"]},
    },
    "required": ["event_id"],
}

_CALENDAR_RESPOND_EVENT_SCHEMA = {
    "type": "object",
    "properties": {
        "event_id": {"type": "string"},
        "attendee_email": {"type": "string"},
        "response_status": {
            "type": "string",
            "enum": ["accepted", "declined", "needsAction", "tentative"],
        },
        "calendar_id": {"type": "string"},
        "send_updates": {"type": "string", "enum": ["none", "all", "externalOnly"]},
    },
    "required": ["event_id", "attendee_email", "response_status"],
}


def _gmail_materials(prefix: str, label: str) -> tuple[Material, ...]:
    return (
        Material(
            name=f"gmail_{prefix}_search_threads",
            description=f"Search {label} Gmail threads by Gmail query string.",
            input_schema=_GMAIL_SEARCH_SCHEMA,
        ),
        Material(
            name=f"gmail_{prefix}_get_thread",
            description=f"Fetch one {label} Gmail thread by thread id.",
            input_schema=_GMAIL_GET_THREAD_SCHEMA,
        ),
        Material(
            name=f"gmail_{prefix}_list_drafts",
            description=f"List {label} Gmail drafts, optionally filtered by query.",
            input_schema=_GMAIL_LIST_DRAFTS_SCHEMA,
        ),
        Material(
            name=f"gmail_{prefix}_create_draft",
            description=(
                f"Create a {label} Gmail draft. This stages language in Gmail but does not send."
            ),
            input_schema=_GMAIL_DRAFT_SCHEMA,
        ),
        Material(
            name=f"gmail_{prefix}_update_draft",
            description=f"Replace an existing {label} Gmail draft with revised contents.",
            input_schema=_GMAIL_UPDATE_DRAFT_SCHEMA,
        ),
        Material(
            name=f"gmail_{prefix}_delete_draft",
            description=f"Delete a {label} Gmail draft by draft id.",
            input_schema=_GMAIL_DRAFT_ID_SCHEMA,
        ),
        Material(
            name=f"gmail_{prefix}_send_draft",
            description=(
                f"Send an existing {label} Gmail draft by draft id. This is the irreversible "
                "message boundary and should only be invoked after explicit review."
            ),
            input_schema=_GMAIL_DRAFT_ID_SCHEMA,
        ),
    )


def _calendar_materials(prefix: str, label: str) -> tuple[Material, ...]:
    return (
        Material(
            name=f"calendar_{prefix}_list_events",
            description=(
                f"List {label} Google Calendar events in a date range from a chosen "
                "calendar, defaulting to the primary calendar. This is live read-only "
                "Calendar API access."
            ),
            input_schema=_CALENDAR_LIST_EVENTS_SCHEMA,
        ),
        Material(
            name=f"calendar_{prefix}_create_event",
            description=(
                f"Create an event on {label} Google Calendar. This writes to the live "
                "calendar. `send_updates` defaults to `none`; use `all` or "
                "`externalOnly` only after explicit review of attendee notifications."
            ),
            input_schema=_CALENDAR_CREATE_EVENT_SCHEMA,
        ),
        Material(
            name=f"calendar_{prefix}_patch_event",
            description=(
                f"Patch fields on an existing event on {label} Google Calendar. This "
                "writes to the live calendar. `send_updates` defaults to `none`; use "
                "`all` or `externalOnly` only after explicit review."
            ),
            input_schema=_CALENDAR_PATCH_EVENT_SCHEMA,
        ),
        Material(
            name=f"calendar_{prefix}_delete_event",
            description=(
                f"Delete an event from {label} Google Calendar. This is destructive. "
                "`send_updates` defaults to `none`; use `all` or `externalOnly` only "
                "after explicit review."
            ),
            input_schema=_CALENDAR_DELETE_EVENT_SCHEMA,
        ),
        Material(
            name=f"calendar_{prefix}_respond_event",
            description=(
                f"Set an attendee response on an event visible to {label} Google Calendar, "
                "such as accepted, declined, tentative, or needsAction. This writes to "
                "the live calendar."
            ),
            input_schema=_CALENDAR_RESPOND_EVENT_SCHEMA,
        ),
    )


MATERIAL_SURFACES: dict[str, Material] = {
    el.name: el
    for el in (
        # Engagement-layer materials: read canonical user-engagement context.
        Material(
            name="consult_canonical_profile",
            description=("Return CanonicalProfile for the user landing node."),
            input_schema={"type": "object", "properties": {}},
        ),
        Material(
            name="consult_canonical_self",
            description=("Return CanonicalSelf for AIlumina's model-side self."),
            input_schema={"type": "object", "properties": {}},
        ),
        Material(
            name="consult_canonical_context",
            description=("Return CanonicalContext for the shared work and objectives."),
            input_schema={"type": "object", "properties": {}},
        ),
        Material(
            name="consult_engagement_context",
            description=("Return the three canonical user-engagement landing nodes together."),
            input_schema={"type": "object", "properties": {}},
        ),
        Material(
            name="read_system_observability",
            description=(
                "Read the local operational observability summary: OTEL export "
                "configuration, queue/backlog timing, recent usage telemetry, "
                "and latency/token aggregates from the trail."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "minimum": 1, "maximum": 50}
                },
            },
        ),
        Material(
            name="render_status_dashboard",
            description=(
                "Render the autonomic-loop status (Judge inbox, Smoother inbox, "
                "open enactments with age, unaddressed Frictions) to a self-"
                "contained HTML file; return the path, live URL, and counts."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "refresh_seconds": {
                        "type": "integer",
                        "minimum": 2,
                        "maximum": 600,
                    }
                },
            },
        ),
        Material(
            name="read_autonomic_maintenance_context",
            description=(
                "Read recent Smoother enactments with the Friction each addressed, "
                "their purpose, visible closure basis, and any substrate ids they changed."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "minimum": 1, "maximum": 50}
                },
            },
        ),
        Material(
            name="read_non_episodic_memory",
            description=(
                "Read durable non-episodic memory from Neo4j through the "
                "canonical spine: CanonicalSelf, CanonicalProfile, "
                "CanonicalContext, and CanonicalGuidance. Supports id, anchor, "
                "label, simple filters, or text query. Episodic Qdrant memory "
                "remains read-only through the separate recall materials."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "memory_id": {"type": "string"},
                    "anchor": {
                        "type": "string",
                        "enum": ["self", "user", "profile", "context", "guidance"],
                    },
                    "label": {"type": "string"},
                    "kind": {"type": "string"},
                    "source": {"type": "string"},
                    "tag": {"type": "string"},
                    "query": {"type": "string"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 50},
                },
            },
        ),
        Material(
            name="write_non_episodic_memory",
            description=(
                "Write durable non-episodic memory to Neo4j under one of the "
                "canonical anchors. Episodic Qdrant memory remains read-only "
                "from this material."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "content": {"type": "string"},
                    "memory_id": {"type": "string"},
                    "kind": {"type": "string"},
                    "source": {"type": "string"},
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "confidence": {"type": "number"},
                    "anchor": {
                        "type": "string",
                        "enum": ["self", "user", "profile", "context", "guidance"],
                    },
                },
                "required": ["content"],
            },
        ),
        Material(
            name="update_canonical_field",
            description=(
                "Update a field on a canonical landing node itself "
                "(CanonicalSelf / CanonicalProfile / CanonicalContext / "
                "CanonicalGuidance) — the deliberate counterpart to "
                "write_non_episodic_memory, which only attaches a satellite. "
                "op='append' adds to a list-valued field (active_projects, "
                "recent_decisions, next_actions, open_threads, blockers, "
                "public_handles); op='replace' sets a scalar field (summary, "
                "current_focus). High-impact: stage genuinely contentious or "
                "identity-sensitive rewords instead (see the consolidation rules)."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "field": {"type": "string"},
                    "value": {},
                    "anchor": {
                        "type": "string",
                        "enum": ["self", "user", "profile", "context", "guidance"],
                    },
                    "op": {"type": "string", "enum": ["append", "replace"]},
                    "sources": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["field", "value"],
            },
        ),
        Material(
            name="ensure_self_rooted_spine",
            description=(
                "Idempotently root the canonical graph at CanonicalSelf: MERGE "
                "typed edges from CanonicalSelf to CanonicalProfile, "
                "CanonicalContext, and CanonicalGuidance. Additive; deletes "
                "nothing. Takes no arguments."
            ),
            input_schema={"type": "object", "properties": {}},
        ),
        Material(
            name="recall_relevant_episodes",
            description=(
                "Return episodic memory turns semantically relevant to a query, "
                "in the store's own similarity order (most similar first, each "
                "with its native score), using the local embedding service and "
                "Qdrant. Narrowed only by the filters and score_threshold you "
                "pass; it does not re-rank — judging which turns matter is yours."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 20},
                    "role": {"type": "string"},
                    "pillar_root": {"type": "string"},
                    "primary_category": {"type": "string"},
                    "date_from": {"type": "string"},
                    "date_to": {"type": "string"},
                    "score_threshold": {"type": "number"},
                },
                "required": ["query"],
            },
        ),
        Material(
            name="recall_recent_episodes",
            description=(
                "Return the most recent episodic memory turns by date_time, "
                "optionally scoped by conversation, role, or date range."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "minimum": 1, "maximum": 20},
                    "conversation_id": {"type": "string"},
                    "role": {"type": "string"},
                    "date_from": {"type": "string"},
                    "date_to": {"type": "string"},
                },
            },
        ),
        Material(
            name="recall_contextual_episodes",
            description=(
                "Return episodic memory turns using structured filters over "
                "canonical pillar, category, role, provider, conversation, "
                "date_time, and sequence."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "minimum": 1, "maximum": 20},
                    "pillar_root": {"type": "string"},
                    "primary_category": {"type": "string"},
                    "role": {"type": "string"},
                    "provider": {"type": "string"},
                    "conversation_id": {"type": "string"},
                    "date_from": {"type": "string"},
                    "date_to": {"type": "string"},
                    "sequence_from": {"type": "integer"},
                    "sequence_to": {"type": "integer"},
                },
            },
        ),
        # Gmail materials — account labels are resolved by env in google_mail.py.
        *_gmail_materials("user", "the user's"),
        *_gmail_materials("test", "the test mailbox's"),
        # Google Calendar materials — account labels follow the Gmail convention.
        *_calendar_materials("user", "the user's"),
        *_calendar_materials("test", "the test mailbox's"),
        # Calendar Stewardship materials — Google-Calendar-shaped mock.
        Material(
            name="cal_list_events",
            description=(
                "List the user's upcoming events in a date range, with "
                "attendee counts and an external-attendee flag."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "start_date": {"type": "string", "format": "date"},
                    "end_date": {"type": "string", "format": "date"},
                },
                "required": ["start_date", "end_date"],
            },
        ),
        Material(
            name="cal_propose_reschedule",
            description=(
                "Stage a reschedule on an event. No attendees notified "
                "(send_updates='none'). Returns a staging id."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "event_id": {"type": "string"},
                    "new_start": {"type": "string"},
                    "new_end": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["event_id", "new_start", "new_end", "reason"],
            },
        ),
        Material(
            name="cal_invite_stance",
            description=(
                "Record a question for the user with named options; no "
                "commitment is made on their behalf."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "question": {"type": "string"},
                    "options": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["question", "options"],
            },
        ),
        Material(
            name="cal_issue_reschedule",
            description=(
                "Convert a staged reschedule into an issued change. "
                "Notifications go to every attendee (send_updates='all'). "
                "Requires a staging id from a prior cal_propose_reschedule."
            ),
            input_schema={
                "type": "object",
                "properties": {"staging_id": {"type": "string"}},
                "required": ["staging_id"],
            },
        ),
        # Reflection-practice material: stores a written reflection.
        Material(
            name="store_reflection",
            description=("Store a short written reflection verbatim and return its id."),
            input_schema={
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
            },
        ),
        Material(
            name="market_fetch_snapshot",
            description=(
                "Fetch a near-live read-only market snapshot from public finance "
                "endpoints for investment analysis. Returns quote prices, "
                "market timestamps, source URLs, optional recent history, and data "
                "limitations. This material reads real market information; it does "
                "not execute trades."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "symbols": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Symbols to fetch. Defaults to broad US equity, sector, "
                            "rates, dollar, and volatility proxies."
                        ),
                    },
                    "range": {
                        "type": "string",
                        "default": "1mo",
                        "description": "Yahoo chart range such as 5d, 1mo, 3mo, 6mo, 1y.",
                    },
                    "interval": {
                        "type": "string",
                        "default": "1d",
                        "description": "Yahoo chart interval such as 1d, 1h, 5m.",
                    },
                    "include_history": {"type": "boolean", "default": True},
                    "timeout_seconds": {"type": "number", "default": 10.0},
                },
            },
        ),
        Material(
            name="read_morning_briefing_sites",
            description=(
                "Read the local Morning Briefing site list from YAML. Returns enabled "
                "recurring sites with id, name, URL, cadence, section, notes, and any "
                "configuration gaps."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    # config_path is intentionally NOT exposed: the practitioner
                    # always reads the configured default site list, so a material
                    # argument cannot be used to read arbitrary local files.
                    "include_disabled": {"type": "boolean", "default": False},
                },
            },
        ),
        Material(
            name="morning_briefing_browser_site_check",
            description=(
                "Check one recurring morning site through Cognabot's browser JIT "
                "proxy. The proxy starts the headless-browser MCP service on first "
                "request, opens the URL, captures the accessibility-tree snapshot, "
                "and returns source notes, headline candidates, snapshot text, or a "
                "structured access gap."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "site_name": {"type": "string"},
                    "url": {"type": "string"},
                    "checked_at": {"type": "string"},
                    # browser_jit_url is intentionally NOT exposed: the proxy is a
                    # fixed loopback service read from configuration, never an
                    # LLM-chosen host (SSRF). The target `url` is additionally
                    # checked against internal/private addresses in the material.
                    "timeout_seconds": {"type": "number", "default": 90.0},
                    "headline_limit": {"type": "integer", "minimum": 1, "maximum": 50},
                },
                "required": ["site_name", "url"],
            },
        ),
        Material(
            name="fund_write_decision_report",
            description=(
                "Write a concise Markdown report for a fund action decision. "
                "The report explains the evidence, market interpretation, rationale, "
                "risk basis, action recorded, and next review triggers. This writes a "
                "local artifact under data/paper_stock_reports."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "fund_id": {"type": "string"},
                    "report_id": {"type": "string"},
                    "as_of": {"type": "string"},
                    "decision_id": {"type": "string"},
                    "action": {"type": "string"},
                    "symbol": {"type": "string"},
                    "title": {"type": "string"},
                    "summary": {"type": "string"},
                    "market_regime": {"type": "string"},
                    "evidence_basis": {"type": "array", "items": {"type": "string"}},
                    "decision_rationale": {"type": "string"},
                    "risk_basis": {"type": "string"},
                    "action_recorded": {"type": "string"},
                    "expected_portfolio_effect": {"type": "string"},
                    "open_questions": {"type": "array", "items": {"type": "string"}},
                    "next_review_triggers": {"type": "array", "items": {"type": "string"}},
                    "source_citations": {"type": "array", "items": {"type": "string"}},
                },
                "required": [
                    "fund_id",
                    "report_id",
                    "as_of",
                    "decision_id",
                    "action",
                    "title",
                    "summary",
                    "decision_rationale",
                    "risk_basis",
                ],
            },
        ),
        Material(
            name="brokerage_submit_buy_order",
            description=(
                "Submit a buy order for a stock after the decision basis and sizing "
                "check have been recorded. Returns order status, fill details, and "
                "the order identifier recorded for the fund trail."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "fund_id": {"type": "string"},
                    "symbol": {"type": "string"},
                    "quantity": {"type": "number"},
                    "order_type": {"type": "string"},
                    "time_in_force": {"type": "string"},
                    "decision_id": {"type": "string"},
                    "as_of": {"type": "string"},
                    "limit_price": {"type": "number"},
                    "estimated_price": {"type": "number"},
                    "rationale": {"type": "string"},
                },
                "required": [
                    "fund_id",
                    "symbol",
                    "quantity",
                    "order_type",
                    "time_in_force",
                    "decision_id",
                    "as_of",
                ],
            },
        ),
        Material(
            name="brokerage_submit_sell_order",
            description=(
                "Submit a sell order for a stock after the decision basis and sizing "
                "check have been recorded. Returns order status, fill details, and "
                "the order identifier recorded for the fund trail."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "fund_id": {"type": "string"},
                    "symbol": {"type": "string"},
                    "quantity": {"type": "number"},
                    "order_type": {"type": "string"},
                    "time_in_force": {"type": "string"},
                    "decision_id": {"type": "string"},
                    "as_of": {"type": "string"},
                    "limit_price": {"type": "number"},
                    "estimated_price": {"type": "number"},
                    "rationale": {"type": "string"},
                },
                "required": [
                    "fund_id",
                    "symbol",
                    "quantity",
                    "order_type",
                    "time_in_force",
                    "decision_id",
                    "as_of",
                ],
            },
        ),
        Material(
            name="fund_read_follow_up_register",
            description=(
                "Read recent structured open questions and review triggers for a "
                "fund from prior stock-investor enactments. Use this at the start "
                "of a scheduled review so prior unresolved items are addressed or "
                "explicitly carried forward."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "fund_id": {"type": "string"},
                    "limit": {"type": "integer", "default": 10},
                    "include_closed": {"type": "boolean", "default": False},
                },
                "required": ["fund_id"],
            },
        ),
        Material(
            name="fund_read_state",
            description=(
                "Reconstruct the latest visible fund state from prior stock-investor "
                "trail steps: mandate, cash, positions, order history, decisions, "
                "theses, latest valuation, latest follow-ups, and reconstruction "
                "warnings. Use this before treating a fund as empty or changing a "
                "position."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "fund_id": {"type": "string"},
                    "limit_enactments": {"type": "integer", "default": 50},
                },
                "required": ["fund_id"],
            },
        ),
        Material(
            name="fund_record_follow_up_register",
            description=(
                "Record structured open questions, review triggers, prior items "
                "addressed, carried-forward items, and the next review intent for "
                "a fund decision."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "fund_id": {"type": "string"},
                    "as_of": {"type": "string"},
                    "decision_id": {"type": "string"},
                    "open_questions": {"type": "array", "items": {"type": "string"}},
                    "review_triggers": {"type": "array", "items": {"type": "string"}},
                    "prior_items_addressed": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "carried_forward": {"type": "array", "items": {"type": "string"}},
                    "next_review_intent": {"type": "string"},
                },
                "required": ["fund_id", "as_of", "decision_id"],
            },
        ),
        Material(
            name="garmin_list_activities",
            description=(
                "List the user's Garmin Connect activities within a date range. "
                "Uses Garmin-native activity ids and live Garmin Connect as the "
                "source unless PRACTICE_GARMIN_SOURCE=mock is explicitly set for "
                "verification/demo runs."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "start_date": {"type": "string", "format": "date"},
                    "end_date": {"type": "string", "format": "date"},
                    "activity_type": {"type": "string"},
                },
                "required": ["start_date", "end_date"],
            },
        ),
        Material(
            name="garmin_get_activity",
            description=(
                "Fetch detail for one Garmin Connect activity by its Garmin-native "
                "activity id, including summary fields and available per-point "
                "metric samples for cadence, speed, heart rate, elevation, and GPS "
                "route summaries/points when Garmin exposes them. In "
                "activities_management, this is a detail/deepening read, not the "
                "entry record for activity rhythm or what was done: choose it before "
                "garmin_list_activities only for an explicitly isolated supplied "
                "activity id/date, or after naming a concrete list/auth/data/material "
                "blocker and limiting the answer to that isolated record. If this or "
                "a stale detail alias is reached before the current activity list and "
                "the work would broaden to rhythm, weekly pattern, completed-activity "
                "mix, gaps, streaks, cadence, recovery context, or what was done, the "
                "next visible move must be garmin_list_activities before more Garmin "
                "reads, synthesis, or final answer."
            ),
            input_schema={
                "type": "object",
                "properties": {"activity_id": {"type": "string"}},
                "required": ["activity_id"],
            },
        ),
        Material(
            name="garmin_get_daily_summary",
            description=(
                "Fetch a Garmin Connect daily wellness summary for a given date: "
                "steps, sleep when Garmin reports it, stress, body battery, "
                "resting heart rate, distance, and active calories. In "
                "activities_management, this is daily wellness context, not a "
                "substitute for the recent activity record: choose it before "
                "garmin_list_activities only for an explicitly bounded daily wellness "
                "snapshot, or after naming a concrete list/auth/data/material blocker "
                "and limiting the answer to that snapshot. If this or a stale "
                "daily-summary alias is reached before the current activity list and "
                "the work would broaden to rhythm, weekly pattern, completed-activity "
                "mix, gaps, streaks, cadence, recovery context, or what was done, the "
                "next visible move must be garmin_list_activities before more Garmin "
                "reads, synthesis, or final answer."
            ),
            input_schema={
                "type": "object",
                "properties": {"date": {"type": "string", "format": "date"}},
                "required": ["date"],
            },
        ),
        Material(
            name="garmin_get_user_stats",
            description=(
                "Fetch aggregate Garmin Connect activity stats for a period using "
                "Garmin as the activity source: count, minutes, distance, and type "
                "breakdown."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "start_date": {"type": "string", "format": "date"},
                    "end_date": {"type": "string", "format": "date"},
                },
                "required": ["start_date", "end_date"],
            },
        ),
        Material(
            name="garmin_route_aware_iwt_analysis",
            description=(
                "Analyse Garmin walking activities against an interval-walking "
                "pattern using live speed, cadence, elevation, and GPS route data. "
                "Returns per-segment normal/fast/relaxed evidence and route "
                "comparability signals without using sleep or heart-rate data."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "start_date": {"type": "string", "format": "date"},
                    "end_date": {"type": "string", "format": "date"},
                    "normal_minutes": {"type": "integer", "minimum": 1, "maximum": 30},
                    "fast_minutes": {"type": "integer", "minimum": 1, "maximum": 30},
                    "repetitions": {"type": "integer", "minimum": 1, "maximum": 20},
                    "activity_type": {"type": "string"},
                },
                "required": ["start_date", "end_date"],
            },
        ),
        Material(
            name="garmin_render_activity_gps_shape",
            description=(
                "Render an MCP App visualization of one Garmin activity's GPS route. "
                "By default this draws the route on OpenStreetMap tiles; set "
                "show_tiles=false for a route-only shape that makes no external tile "
                "requests. Accepts an explicit Garmin-native activity id, or scans a "
                "date range and selects the newest activity that exposes GPS route "
                "points."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "activity_id": {"type": "string"},
                    "garmin_id": {"type": "string"},
                    "start_date": {"type": "string", "format": "date"},
                    "end_date": {"type": "string", "format": "date"},
                    "activity_type": {"type": "string"},
                    "max_candidates": {"type": "integer", "minimum": 1, "maximum": 50},
                    "show_tiles": {"type": "boolean"},
                    "map_style": {"type": "string", "enum": ["osm", "shape"]},
                },
            },
        ),
        Material(
            name="garmin_render_activity_type_visualization",
            description=(
                "Render an MCP App dashboard for Garmin activities grouped by one "
                f"or all supported activity types: {', '.join(activity_type_keys())}. "
                "Shows recent sessions, totals, latest activity, "
                "and a GPS route preview when Garmin exposes route points."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "activity_type": {
                        "type": "string",
                        "enum": activity_type_keys(),
                    },
                    "start_date": {"type": "string", "format": "date"},
                    "end_date": {"type": "string", "format": "date"},
                    "max_per_type": {"type": "integer", "minimum": 1, "maximum": 25},
                    "show_tiles": {"type": "boolean"},
                },
            },
        ),
        # Latent Knowledge Probe — free/public mechanistic-interpretability routes.
        Material(
            name="latent_probe_design_protocol",
            description=(
                "Select and record the free/open mechanistic-interpretability route "
                "for a latent-knowledge probe. Surfaces include Neuronpedia's public "
                "SAE feature API, NDIF/NNsight remote open-model internals for users "
                "with free research access, and local TransformerLens/SAELens routes."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "target_model": {"type": "string"},
                    "model_runtime": {"type": "string"},
                    "mechanistic_surfaces": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": [
                                "neuronpedia",
                                "ndif_nnsight",
                                "transformerlens",
                                "saelens",
                            ],
                        },
                    },
                    "question_family": {"type": "string"},
                    "known_targets": {"type": "array", "items": {"type": "string"}},
                    "unknown_controls": {"type": "array", "items": {"type": "string"}},
                    "planted_or_misleading_controls": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "intervention_plan": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "stopping_conditions": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "gaps": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["target_model", "mechanistic_surfaces", "question_family"],
            },
        ),
        Material(
            name="latent_probe_record_trial",
            description=(
                "Record one scaffolded target-model trial and enrich it with live "
                "Neuronpedia feature JSON when feature ids are supplied. Keeps "
                "relational observations, mechanistic observations, intervention "
                "results, control results, and access gaps separated."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "as_of": {"type": "string"},
                    "target_model": {"type": "string"},
                    "prompt": {"type": "string"},
                    "scaffolding_move": {"type": "string"},
                    "model_response": {"type": "string"},
                    "mechanistic_observations": {
                        "type": "array",
                        "items": {"type": "object"},
                    },
                    "relational_observations": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "intervention_results": {
                        "type": "array",
                        "items": {"type": "object"},
                    },
                    "control_results": {"type": "array", "items": {"type": "object"}},
                    "neuronpedia_features": {
                        "type": "array",
                        "items": {
                            "oneOf": [
                                {"type": "string"},
                                {
                                    "type": "object",
                                    "properties": {
                                        "feature_id": {"type": "string"},
                                        "model_id": {"type": "string"},
                                        "sae_id": {"type": "string"},
                                        "feature_index": {},
                                    },
                                },
                            ]
                        },
                    },
                    "gaps": {"type": "array", "items": {"type": "string"}},
                    "timeout_seconds": {"type": "number", "default": 10.0},
                },
                "required": ["as_of", "target_model", "prompt", "model_response"],
            },
        ),
        Material(
            name="run_neuronpedia_activation_probe",
            description=(
                "Run Neuronpedia-hosted custom-text activation testing for one SAE "
                "feature, using the public /api/activation/new endpoint. This keeps "
                "the activation pass on Neuronpedia's side instead of requiring "
                "local torch or TransformerLens. Returns tokens, activation values, "
                "max activation, source endpoint, raw response, or an auth/access gap."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "custom_text": {
                        "oneOf": [
                            {"type": "string"},
                            {"type": "array", "items": {"type": "string"}},
                        ],
                    },
                    "feature_id": {
                        "type": "string",
                        "description": "MODEL@SOURCE:INDEX, e.g. gpt2-small@9-res-jb:200.",
                    },
                    "model_id": {"type": "string"},
                    "source": {"type": "string"},
                    "feature_index": {},
                    "timeout_seconds": {"type": "number", "default": 20.0},
                    "base_url": {
                        "type": "string",
                        "default": "https://www.neuronpedia.org",
                    },
                    "api_key": {
                        "type": "string",
                        "description": (
                            "Optional Neuronpedia API key for resources that require "
                            "auth. Prefer environment-managed secrets in live use."
                        ),
                    },
                },
                "required": ["custom_text"],
            },
        ),
        Material(
            name="run_neuronpedia_topk_by_token_probe",
            description=(
                "Run Neuronpedia-hosted top-k feature discovery by token for a "
                "custom text and SAE source. This discovers which features a "
                "baseline or scaffold actually recruits, instead of requiring the "
                "practitioner to choose a feature first. Returns summarized top "
                "features per token with explanations and positive/negative strings."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "text": {
                        "oneOf": [
                            {"type": "string"},
                            {"type": "array", "items": {"type": "string"}},
                        ],
                    },
                    "model_id": {"type": "string"},
                    "source": {
                        "type": "string",
                        "description": "Neuronpedia source/SAE id, e.g. 6-res_scefr-ajt.",
                    },
                    "num_results": {"type": "integer", "minimum": 1, "maximum": 20},
                    "ignore_bos": {"type": "boolean", "default": True},
                    "density_threshold": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1,
                        "default": 0.01,
                    },
                    "timeout_seconds": {"type": "number", "default": 30.0},
                    "base_url": {
                        "type": "string",
                        "default": "https://www.neuronpedia.org",
                    },
                    "api_key": {
                        "type": "string",
                        "description": (
                            "Optional Neuronpedia API key for resources that require "
                            "auth. Prefer environment-managed secrets in live use."
                        ),
                    },
                },
                "required": ["text", "model_id", "source"],
            },
        ),
        Material(
            name="run_neuronpedia_steering_probe",
            description=(
                "Run Neuronpedia-hosted SAE feature steering for a completion prompt. "
                "Returns the default and steered completions, logprobs when provided, "
                "feature intervention settings, raw response, or an auth/access gap. "
                "Use this as the hosted causal-intervention route before local "
                "TransformerLens patching."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "prompt": {"type": "string"},
                    "model_id": {"type": "string"},
                    "features": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["modelId", "layer", "index", "strength"],
                            "properties": {
                                "modelId": {"type": "string"},
                                "layer": {"type": "string"},
                                "index": {"type": "number"},
                                "strength": {"type": "number"},
                            },
                        },
                    },
                    "temperature": {"type": "number", "default": 0.3},
                    "n_tokens": {"type": "integer", "minimum": 1, "maximum": 256},
                    "freq_penalty": {"type": "number", "default": 0.0},
                    "seed": {"type": "integer", "default": 42},
                    "strength_multiplier": {"type": "number", "default": 1.0},
                    "steer_method": {
                        "type": "string",
                        "enum": ["SIMPLE_ADDITIVE", "ORTHOGONAL_DECOMP"],
                    },
                    "timeout_seconds": {"type": "number", "default": 45.0},
                    "base_url": {
                        "type": "string",
                        "default": "https://www.neuronpedia.org",
                    },
                    "api_key": {
                        "type": "string",
                        "description": (
                            "Optional Neuronpedia API key for resources that require "
                            "auth. Prefer environment-managed secrets in live use."
                        ),
                    },
                },
                "required": ["prompt", "model_id", "features"],
            },
        ),
        Material(
            name="run_latent_recovery_trial",
            description=(
                "Run a hosted baseline-to-scaffold latent recovery trial. It discovers "
                "top Neuronpedia features for the baseline, each scaffold text, final "
                "probe, and negative controls; selects features newly recruited by the "
                "scaffold/final traces; and optionally runs Neuronpedia steering on "
                "the strongest candidate. This is the repeatable trial shape for "
                "testing whether scaffolding recruits latent structure."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "baseline_text": {"type": "string"},
                    "scaffold_texts": {"type": "array", "items": {"type": "string"}},
                    "final_probe_text": {"type": "string"},
                    "model_id": {"type": "string"},
                    "source": {"type": "string"},
                    "negative_control_texts": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "num_results": {"type": "integer", "minimum": 1, "maximum": 20},
                    "candidate_limit": {"type": "integer", "minimum": 1, "maximum": 20},
                    "run_steering": {"type": "boolean", "default": True},
                    "steering_strength": {"type": "number", "default": 20.0},
                    "steering_temperature": {"type": "number", "default": 0.3},
                    "steering_tokens": {"type": "integer", "minimum": 1, "maximum": 256},
                    "seed": {"type": "integer", "default": 42},
                    "timeout_seconds": {"type": "number", "default": 30.0},
                    "base_url": {
                        "type": "string",
                        "default": "https://www.neuronpedia.org",
                    },
                    "api_key": {
                        "type": "string",
                        "description": (
                            "Optional Neuronpedia API key for resources that require "
                            "auth. Prefer environment-managed secrets in live use."
                        ),
                    },
                },
                "required": [
                    "baseline_text",
                    "scaffold_texts",
                    "final_probe_text",
                    "model_id",
                    "source",
                ],
            },
        ),
        Material(
            name="run_interactive_latent_positioning_trial",
            description=(
                "Run a hosted cumulative transcript analysis for an interactive "
                "latent-positioning sequence. Each turn is added to the transcript, "
                "Neuronpedia top-k features are discovered for the cumulative text, "
                "features newly recruited after the first turn are selected, controls "
                "are checked, and optional steering is run on the strongest candidate."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "turns": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "speaker": {
                                    "type": "string",
                                    "enum": ["user", "assistant", "system", "observer"],
                                },
                                "text": {"type": "string"},
                            },
                            "required": ["speaker", "text"],
                        },
                    },
                    "model_id": {"type": "string"},
                    "source": {"type": "string"},
                    "target_probe_text": {"type": "string"},
                    "negative_control_turns": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "speaker": {
                                    "type": "string",
                                    "enum": ["user", "assistant", "system", "observer"],
                                },
                                "text": {"type": "string"},
                            },
                            "required": ["speaker", "text"],
                        },
                    },
                    "num_results": {"type": "integer", "minimum": 1, "maximum": 20},
                    "candidate_limit": {"type": "integer", "minimum": 1, "maximum": 20},
                    "run_steering": {"type": "boolean", "default": True},
                    "steering_strength": {"type": "number", "default": 20.0},
                    "steering_temperature": {"type": "number", "default": 0.3},
                    "steering_tokens": {"type": "integer", "minimum": 1, "maximum": 256},
                    "seed": {"type": "integer", "default": 42},
                    "timeout_seconds": {"type": "number", "default": 30.0},
                    "base_url": {
                        "type": "string",
                        "default": "https://www.neuronpedia.org",
                    },
                    "api_key": {
                        "type": "string",
                        "description": (
                            "Optional Neuronpedia API key for resources that require "
                            "auth. Prefer environment-managed secrets in live use."
                        ),
                    },
                },
                "required": ["turns", "model_id", "source"],
            },
        ),
        Material(
            name="run_transformerlens_activation_probe",
            description=(
                "Run a local TransformerLens probe against an open model when "
                "transformer_lens and torch are installed. Captures selected "
                "activation-cache summaries, next-token predictions, optional "
                "control prompts, and an optional simple zero-ablation contrast. "
                "If the optional runtime is missing, returns an explicit install "
                "gap and planned probe rather than failing the practice."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "prompt": {"type": "string"},
                    "model_name": {"type": "string", "default": "gpt2-small"},
                    "activation_names": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "target_token": {"type": "string"},
                    "control_prompts": {"type": "array", "items": {"type": "string"}},
                    "ablate_activation_name": {"type": "string"},
                    "ablate_position": {"type": "integer", "default": -1},
                    "device": {"type": "string"},
                    "top_k": {"type": "integer", "minimum": 1, "maximum": 25},
                },
                "required": ["prompt"],
            },
        ),
        Material(
            name="latent_probe_confidence_judgment",
            description=(
                "Record the bounded confidence judgment for a candidate claim. "
                "The material flags over-strong retrieval-supported judgments when "
                "behavioral, mechanistic, causal, or control evidence is missing."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "claim": {"type": "string"},
                    "classification": {
                        "type": "string",
                        "enum": [
                            "retrieval-supported",
                            "constructed-plausible",
                            "activation-present-response-blocked",
                            "confabulation-likely",
                            "unknown",
                        ],
                    },
                    "confidence": {"type": "string"},
                    "behavioral_evidence": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "mechanistic_evidence": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "causal_evidence": {"type": "array", "items": {"type": "string"}},
                    "control_evidence": {"type": "array", "items": {"type": "string"}},
                    "counterevidence": {"type": "array", "items": {"type": "string"}},
                    "missing_registers": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "next_probe": {"type": "string"},
                },
                "required": ["claim", "classification", "confidence"],
            },
        ),
        # Practice Management meta-materials.
        Material(
            name="pm_read_pool",
            description=(
                "Return every entry in the named pool. Valid pools: "
                "teleo_affective, understanding, rules, affordances, materials."
            ),
            input_schema={
                "type": "object",
                "properties": {"pool": {"type": "string"}},
                "required": ["pool"],
            },
        ),
        Material(
            name="pm_create_element",
            description="Add a new entry to a teleo_affective / understanding / rules pool.",
            input_schema={
                "type": "object",
                "properties": {
                    "pool": {"type": "string"},
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["pool", "id", "name", "content"],
            },
        ),
        Material(
            name="pm_amend_element",
            description=(
                "Amend an existing teleo_affective / understanding / rules entry "
                "(any of name/content)."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "pool": {"type": "string"},
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["pool", "id"],
            },
        ),
        Material(
            name="pm_create_affordance",
            description="Add an affordance that reaches for one or more existing materials.",
            input_schema={
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "materials": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["id", "name", "description", "materials"],
            },
        ),
        Material(
            name="pm_amend_affordance",
            description="Amend an existing affordance (any of name/description/materials).",
            input_schema={
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "materials": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["id"],
            },
        ),
        Material(
            name="pm_create_material",
            description=(
                "Add a material's captured surface (name, description, input "
                "schema) and, optionally, a persisted dynamic implementation."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "input_schema": {"type": "object"},
                    "implementation": {
                        "type": "object",
                        "properties": {
                            "kind": {
                                "type": "string",
                                "enum": ["constant", "echo", "expression"],
                            },
                            "result": {},
                            "expression": {"type": "string"},
                        },
                    },
                },
                "required": ["name", "description", "input_schema"],
            },
        ),
        Material(
            name="pm_amend_material",
            description=(
                "Amend an existing material's description, input schema, or dynamic implementation."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "input_schema": {"type": "object"},
                    "implementation": {
                        "type": "object",
                        "properties": {
                            "kind": {
                                "type": "string",
                                "enum": ["constant", "echo", "expression"],
                            },
                            "result": {},
                            "expression": {"type": "string"},
                        },
                    },
                },
                "required": ["name"],
            },
        ),
        Material(
            name="pm_create_bundle",
            description=(
                "Add a new bundle to the catalog as a selection over the pools."
                " mode defaults to somatic; pass 'autonomic' for autonomic bundles."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "teleo_affective_ids": {"type": "array", "items": {"type": "string"}},
                    "understanding_ids": {"type": "array", "items": {"type": "string"}},
                    "rules_ids": {"type": "array", "items": {"type": "string"}},
                    "affordance_ids": {"type": "array", "items": {"type": "string"}},
                    "evaluation_ids": {"type": "array", "items": {"type": "string"}},
                    "mode": {"type": "string", "enum": ["somatic", "autonomic"]},
                },
                "required": [
                    "id",
                    "name",
                    "description",
                    "teleo_affective_ids",
                    "understanding_ids",
                    "rules_ids",
                    "affordance_ids",
                ],
            },
        ),
        Material(
            name="pm_amend_bundle",
            description=(
                "Change which pool ids an existing bundle selects. Omitted id "
                "lists are preserved, including evaluation_ids — pass it only to "
                "change the bundle's evaluation layer."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "teleo_affective_ids": {"type": "array", "items": {"type": "string"}},
                    "understanding_ids": {"type": "array", "items": {"type": "string"}},
                    "rules_ids": {"type": "array", "items": {"type": "string"}},
                    "affordance_ids": {"type": "array", "items": {"type": "string"}},
                    "evaluation_ids": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["id"],
            },
        ),
        # Evaluation-spec authoring — pooled into both Practice Management
        # (somatic, the human's door) and the Smoother (autonomic, the loop's).
        Material(
            name="pm_create_evaluation",
            description=(
                "Author a new evaluation spec: a practice's declarative measure of "
                "whether it delivers its objective. Data, not code — `signals` are "
                "generic signal kinds (affordance_coverage, outcome_presence, "
                "shape_repetition, recurring_summary_marker) parameterised for the "
                "practice. `objective_ref` should name one of the practice bundle's "
                "teleo-affective ids so the evaluator is not vacuous. Wire the spec "
                "id into the bundle's evaluation_ids (via amend_bundle) to activate it."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "practice_id": {"type": "string"},
                    "signals": {"type": "array", "items": {"type": "object"}},
                    "objective_ref": {"type": "string"},
                    "derived_from": {"type": "string"},
                    "window": {"type": "integer", "minimum": 1, "maximum": 50},
                },
                "required": ["id", "name", "practice_id", "signals"],
            },
        ),
        Material(
            name="pm_amend_evaluation",
            description=(
                "Amend an existing evaluation spec. Omitted fields keep their "
                "current value; pass only what changes (signals, window, "
                "objective_ref, derived_from, name, practice_id)."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "practice_id": {"type": "string"},
                    "signals": {"type": "array", "items": {"type": "object"}},
                    "objective_ref": {"type": "string"},
                    "derived_from": {"type": "string"},
                    "window": {"type": "integer", "minimum": 1, "maximum": 50},
                },
                "required": ["id"],
            },
        ),
        Material(
            name="pm_reload_seed_substrate",
            description=(
                "Reload file-backed pools and bundles plus code-owned material "
                "surfaces and registry functions, then force projection refresh."
            ),
            input_schema={"type": "object", "properties": {}},
        ),
        Material(
            name="pm_check_documentation_impact",
            description=(
                "Search README/docs/social-media markdown for references likely "
                "affected by changed substrate ids, files, or query terms."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "changed_ids": {"type": "array", "items": {"type": "string"}},
                    "changed_files": {"type": "array", "items": {"type": "string"}},
                    "query": {"type": "string"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 100},
                },
            },
        ),
        # Judge primitives.
        Material(
            name="judge_list_recent_enactments",
            description=(
                "Return a discovery window of recent enactments from the global trail, "
                "ordered by opened_at most-recent-first. When `bundle_id` is provided, "
                "the bundle filter is applied before `limit`, so the result is the "
                "recent window for that bundle rather than a global window narrowed "
                "afterward. Dispatch/inbox recency is tracked by closed_at, so a known "
                "dispatched enactment may still resolve through `read_enactment_steps` "
                "even if it is outside this opened_at listing."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 10},
                    "bundle_id": {"type": "string"},
                },
            },
        ),
        Material(
            name="judge_read_enactment_steps",
            description=("Read every step recorded against a single enactment, in order."),
            input_schema={
                "type": "object",
                "properties": {"enactment_id": {"type": "string"}},
                "required": ["enactment_id"],
            },
        ),
        Material(
            name="judge_read_bundle",
            description=(
                "Return a bundle's structure as data — its mode and the pool ids it selects."
            ),
            input_schema={
                "type": "object",
                "properties": {"bundle_id": {"type": "string"}},
                "required": ["bundle_id"],
            },
        ),
        Material(
            name="judge_emit_friction",
            description=(
                "Record a Friction observation. kind is a short tag; content "
                "is the description; observation_data is optional structured "
                "evidence."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "target_enactment_id": {"type": "string"},
                    "kind": {"type": "string"},
                    "content": {"type": "string"},
                    "observation_data": {"type": "object"},
                },
                "required": ["target_enactment_id", "kind", "content"],
            },
        ),
        # Practice-evaluation engine — generic, afforded to the Judge. Reads a
        # practice's declarative evaluation layer and runs its signals over the
        # practice's real trail. Read-only; emits no Friction.
        Material(
            name="evaluate_quality_for_practice",
            description=(
                "Measure whether a practice is delivering its objective. Reads the "
                "named practice's evaluation layer (its declarative EvaluationSpec) "
                "and runs each signal over that practice's recent real enactments, "
                "returning structured findings (pass/concern per signal) — a "
                "measurement, not a verdict. A practice with no evaluation layer "
                "returns spec_present=false with newness_signal=true. Read-only: it "
                "does not emit Friction or change substrate."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The practice (bundle) id to evaluate.",
                    },
                    "window": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 50,
                        "description": (
                            "Override how many recent closed enactments to "
                            "consider; defaults to the spec's own window."
                        ),
                    },
                },
                "required": ["name"],
            },
        ),
        # Smoother — two smoother-specific materials; the Smoother bundle's
        # other six affordances reuse PM materials defined above.
        Material(
            name="smoother_read_pending_friction",
            description=(
                "Return Friction observations that have not been addressed yet. "
                "When addressing a dispatched Friction, pass its friction_id so "
                "the trail records the exact item used as the closure basis "
                "instead of relying on an elidable bulk pending list."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 10},
                    "friction_id": {"type": "integer"},
                },
            },
        ),
        Material(
            name="smoother_read_friction_kinds",
            description=(
                "Return the current Friction-kind vocabulary with counts (most "
                "common first). Consult before renaming so a provisional kind can "
                "be condensed toward an existing kind instead of minting another."
            ),
            input_schema={
                "type": "object",
                "properties": {"limit": {"type": "integer", "default": 200}},
            },
        ),
        Material(
            name="smoother_rename_friction",
            description=(
                "Condense a Friction's name: rename the Judge's provisional kind "
                "toward the canonical vocabulary (optionally re-wording content). "
                "Recorded as a step, so the old→new is preserved on the trail."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "friction_id": {"type": "integer"},
                    "new_kind": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["friction_id", "new_kind"],
            },
        ),
        Material(
            name="smoother_mark_addressed",
            description=(
                "Mark a Friction observation as addressed by this enactment. "
                "When closing without a substrate mutation, pass rationale so "
                "the accepted mark result carries the no-mutation basis."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "friction_id": {"type": "integer"},
                    "rationale": {"type": "string"},
                },
                "required": ["friction_id"],
            },
        ),
        # RemSleep / Memory Recall and Memory Consolidation.
        Material(
            name="remsleep_read_checkpoint",
            description=(
                "Read the RemSleep checkpoint that marks the last reviewed "
                "episodic-memory and graph-drift watermarks."
            ),
            input_schema={"type": "object", "properties": {}},
        ),
        Material(
            name="remsleep_recall_unreviewed_episodes",
            description=(
                "Recall episodic turns after the prior RemSleep checkpoint "
                "watermark. sequence_from is treated as exclusive."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "minimum": 1, "maximum": 20},
                    "sequence_from": {"type": "integer"},
                    "date_from": {"type": "string"},
                    "date_to": {"type": "string"},
                },
            },
        ),
        Material(
            name="remsleep_read_updated_graph_nodes",
            description=("Read non-canonical Neo4j nodes updated after a graph watermark."),
            input_schema={
                "type": "object",
                "properties": {
                    "since": {"type": "string"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 100},
                },
            },
        ),
        Material(
            name="remsleep_dispatch_memory_signal",
            description=(
                "Dispatch a source-backed memory signal for Memory Consolidation to consume."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "content": {"type": "string"},
                    "kind": {"type": "string"},
                    "source_ids": {"type": "array", "items": {"type": "string"}},
                    "evidence": {"type": "object"},
                    "suggested_anchor": {
                        "type": "string",
                        "enum": ["self", "user", "profile", "context", "guidance"],
                    },
                    "confidence": {"type": "number"},
                },
                "required": ["content"],
            },
        ),
        Material(
            name="remsleep_read_memory_signals",
            description=("Read pending memory signals dispatched by Memory Recall."),
            input_schema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "minimum": 1, "maximum": 100},
                    "include_handled": {"type": "boolean"},
                },
            },
        ),
        Material(
            name="remsleep_mark_memory_signal_handled",
            description=(
                "Mark a dispatched memory signal as handled after consolidation "
                "has staged, written, or explicitly skipped it."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "signal_id": {"type": "string"},
                    "notes": {"type": "string"},
                },
                "required": ["signal_id"],
            },
        ),
        Material(
            name="remsleep_stage_memory_candidate",
            description=(
                "Append a source-backed canonical-memory candidate to the "
                "RemSleep staging file for later review."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "content": {"type": "string"},
                    "anchor": {
                        "type": "string",
                        "enum": ["self", "user", "profile", "context", "guidance"],
                    },
                    "kind": {"type": "string"},
                    "source_ids": {"type": "array", "items": {"type": "string"}},
                    "evidence": {"type": "object"},
                    "confidence": {"type": "number"},
                },
                "required": ["content"],
            },
        ),
        Material(
            name="remsleep_record_checkpoint",
            description=(
                "Persist the RemSleep checkpoint after the review range has "
                "been inspected and selected candidates have been written or staged."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "episode_sequence": {"type": "integer"},
                    "episode_date_time": {"type": "string"},
                    "graph_updated_at": {"type": "string"},
                    "reviewed_at": {"type": "string"},
                    "notes": {"type": "string"},
                },
            },
        ),
    )
}
