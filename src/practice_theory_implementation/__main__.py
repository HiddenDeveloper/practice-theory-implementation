"""Step 11 demonstration: the autonomic loop closes through the harness.

Runs three phases in sequence:

1. Somatic walk — the existing engagement, practices, and Practice Management
   authoring run, on a server launched with PRACTICE_SERVER_MODE=somatic.
   When the verify exits this MCP session, the server's shutdown handler
   closes the active practice enactment so the dispatcher can route it.

2. Autonomic loop — runs the harness with the ScriptedAdapter for both Judge
   and Smoother. The harness drains the inboxes (populated by the dispatcher
   from closed enactments and Friction observations) and dispatches each
   work item through the adapter. The ScriptedAdapter calls a deterministic
   Python handler that opens its own MCP session and walks the primitives —
   the same work an LLM enactment would do, scripted for the verify.

3. Trail + Friction summary — top-level enactments, their children, and the
   Friction observations table.

Three real LLM adapters (`AnthropicSDKAdapter`, `ClaudeCliAdapter`,
`CodexExecAdapter`) live alongside the ScriptedAdapter for production usage;
see the doc for runbook commands.

Run with:

    uv run python -m practice_theory_implementation
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import UTC, datetime, timedelta
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from practice_theory_implementation.autonomic_adapters import (
    AdapterConfig,
    RolePolicy,
    ScriptedAdapter,
    WorkItem,
    compose_brief,
    drain,
)
from practice_theory_implementation.autonomic_dispatcher import route_now
from practice_theory_implementation.bundles import BUNDLES
from practice_theory_implementation.pools import substrate
from practice_theory_implementation.trail import EnactmentStore


def _content_to_value(content_list: list[Any]) -> Any:
    """Extract a Python value from an MCP tool-result content list.

    FastMCP serialises a list result as multiple TextContent items (one per
    element); a scalar result comes back as a single TextContent. Aggregate
    accordingly and decode JSON where possible.
    """
    if not content_list:
        return None
    parts: list[Any] = []
    for item in content_list:
        text = getattr(item, "text", None)
        if text is None:
            parts.append(item)
            continue
        try:
            parts.append(json.loads(text))
        except json.JSONDecodeError:
            parts.append(text)
    return parts[0] if len(parts) == 1 else parts


def _print_value(label: str, value: Any) -> None:
    print(f"{label}:")
    if isinstance(value, (dict, list)):
        print("  " + json.dumps(value, indent=2, default=str).replace("\n", "\n  "))
    else:
        print(f"  {value}")
    print()


def _server_params(mode: str) -> StdioServerParameters:
    """Spawn the server in `mode` over stdio with the dispatcher disabled.

    The verify owns routing (via `route_now` between drains). Subprocess
    servers are workers — letting their dispatchers also route would create
    runaway recursion as each new autonomic enactment gets queued mid-drain.
    """
    return StdioServerParameters(
        command=sys.executable,
        args=["-m", "practice_theory_implementation.server"],
        env={
            **os.environ,
            "PRACTICE_SERVER_MODE": mode,
            "PRACTICE_DISABLE_DISPATCHER": "1",
        },
    )


async def verify_somatic() -> None:
    print("=" * 60)
    print("Somatic mode session (PRACTICE_SERVER_MODE=somatic)")
    print("=" * 60)
    print()
    async with stdio_client(_server_params("somatic")) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools_result = await session.list_tools()
            print("Tools exposed by the server:")
            for tool in tools_result.tools:
                print(f"  - {tool.name}")
            print()

            r = await session.call_tool("list_practices", {})
            _print_value("list_practices()", _content_to_value(r.content))

            # The engagement is already projected; discover the engagement-layer
            # affordances before switching to any practice.
            r = await session.call_tool("current_practice", {})
            _print_value(
                "current_practice()  [before switch — nothing active]",
                _content_to_value(r.content),
            )

            r = await session.call_tool("user_engagement", {})
            ue = _content_to_value(r.content)
            # Truncate the composition for readable output
            if isinstance(ue, dict) and "composition" in ue and ue["composition"]:
                ue = {**ue, "composition": ue["composition"][:200] + "…(truncated)"}
            _print_value(
                "user_engagement()  [engagement layer as a first-class read]",
                ue,
            )

            r = await session.call_tool("discover_affordances", {})
            _print_value(
                "discover_affordances()  [before switch — engagement only]",
                _content_to_value(r.content),
            )

            r = await session.call_tool(
                "invoke_affordance",
                {
                    "affordance_id": "about_the_user",
                    "material_name": "consult_engagement_context",
                    "arguments": {},
                },
            )
            _print_value(
                "invoke_affordance(about_the_user, consult_engagement_context, ...)",
                _content_to_value(r.content),
            )
            for affordance_id, material_name in (
                ("about_user_profile", "consult_canonical_profile"),
                ("about_self", "consult_canonical_self"),
                ("about_shared_context", "consult_canonical_context"),
            ):
                await session.call_tool(
                    "invoke_affordance",
                    {
                        "affordance_id": affordance_id,
                        "material_name": material_name,
                        "arguments": {},
                    },
                )
            for affordance_id, material_name, arguments in (
                (
                    "read_non_episodic_memory",
                    "read_non_episodic_memory",
                    {"limit": 1},
                ),
                (
                    "recall_relevant_episodes",
                    "recall_relevant_episodes",
                    {
                        "query": (
                            "user engagement canonical profile self shared "
                            "context"
                        ),
                        "limit": 1,
                    },
                ),
                (
                    "recall_recent_engagement",
                    "recall_recent_episodes",
                    {"limit": 1},
                ),
                (
                    "recall_contextual_episodes",
                    "recall_contextual_episodes",
                    {"pillar_root": "CanonicalSelf", "limit": 1},
                ),
            ):
                await session.call_tool(
                    "invoke_affordance",
                    {
                        "affordance_id": affordance_id,
                        "material_name": material_name,
                        "arguments": arguments,
                    },
                )

            r = await session.call_tool(
                "switch_practice", {"practice_id": "activities_management"}
            )
            _print_value(
                "switch_practice('activities_management')",
                _content_to_value(r.content),
            )

            r = await session.call_tool("discover_affordances", {})
            _print_value(
                "discover_affordances()  [engagement + practice]",
                _content_to_value(r.content),
            )

            r = await session.call_tool(
                "invoke_affordance",
                {
                    "affordance_id": "recent_activity",
                    "material_name": "garmin_list_activities",
                    "arguments": {
                        "start_date": "2026-05-19",
                        "end_date": "2026-05-25",
                    },
                },
            )
            _print_value(
                "invoke_affordance(recent_activity, garmin_list_activities, ...)",
                _content_to_value(r.content),
            )

            # Switch to a different practice — engagement holds across the switch.
            r = await session.call_tool(
                "switch_practice", {"practice_id": "reflection"}
            )
            _print_value(
                "switch_practice('reflection')",
                _content_to_value(r.content),
            )

            r = await session.call_tool(
                "invoke_affordance",
                {
                    "affordance_id": "record_reflection",
                    "material_name": "store_reflection",
                    "arguments": {
                        "text": "Step 6 came together — the engagement is now real.",
                    },
                },
            )
            _print_value(
                "invoke_affordance(record_reflection, store_reflection, ...)",
                _content_to_value(r.content),
            )

            # --- Calendar Stewardship: stage, invite stance, issue ---------
            # Worked-example practice for the case study essay. The bundle's
            # discipline turns "move the meeting" into three distinct steps:
            # stage (no notifications), invite stance (name the choice and
            # hand back), issue (notifications go out). The mock prints what
            # would have left the process at each step so the saved harm is
            # visible.
            print("=" * 60)
            print("Calendar Stewardship: stage, invite stance, issue")
            print("=" * 60)
            print()
            today = datetime.now(UTC).date()
            read_start = (today - timedelta(days=1)).isoformat()
            read_end = (today + timedelta(days=7)).isoformat()

            r = await session.call_tool(
                "switch_practice", {"practice_id": "calendar_stewardship"}
            )
            _print_value(
                "switch_practice('calendar_stewardship')",
                _content_to_value(r.content),
            )

            r = await session.call_tool(
                "invoke_affordance",
                {
                    "affordance_id": "read_calendar",
                    "material_name": "cal_list_events",
                    "arguments": {
                        "start_date": read_start,
                        "end_date": read_end,
                    },
                },
            )
            calendar_events = _content_to_value(r.content)
            _print_value(
                "invoke_affordance(read_calendar, cal_list_events, ...)",
                calendar_events,
            )
            customer_review = next(
                event
                for event in calendar_events
                if event["id"] == "evt-customer-review"
            )
            old_start = datetime.fromisoformat(customer_review["start"])
            old_end = datetime.fromisoformat(customer_review["end"])
            new_start = old_start + timedelta(hours=1)
            new_end = old_end + timedelta(hours=1)

            r = await session.call_tool(
                "invoke_affordance",
                {
                    "affordance_id": "propose_reschedule",
                    "material_name": "cal_propose_reschedule",
                    "arguments": {
                        "event_id": "evt-customer-review",
                        "new_start": new_start.isoformat(),
                        "new_end": new_end.isoformat(),
                        "reason": (
                            "User has a conflict at the original time; "
                            "moving an hour later in the same day."
                        ),
                    },
                },
            )
            _print_value(
                "invoke_affordance(propose_reschedule, cal_propose_reschedule, ...)",
                _content_to_value(r.content),
            )
            staging_id = None
            for block in r.content:
                v = _content_to_value([block])
                if isinstance(v, dict) and v.get("staging_id"):
                    staging_id = v["staging_id"]
                    break

            r = await session.call_tool(
                "invoke_affordance",
                {
                    "affordance_id": "invite_stance",
                    "material_name": "cal_invite_stance",
                    "arguments": {
                        "question": (
                            "Acme customer review has external attendees "
                            "(alice@acme.example, bob@acme.example). "
                            "Issue the reschedule and notify them?"
                        ),
                        "options": ["Issue with notifications", "Hold", "Cancel reschedule"],
                    },
                },
            )
            _print_value(
                "invoke_affordance(invite_stance, cal_invite_stance, ...)",
                _content_to_value(r.content),
            )

            if staging_id:
                r = await session.call_tool(
                    "invoke_affordance",
                    {
                        "affordance_id": "issue_reschedule",
                        "material_name": "cal_issue_reschedule",
                        "arguments": {"staging_id": staging_id},
                    },
                )
                _print_value(
                    "invoke_affordance(issue_reschedule, cal_issue_reschedule, ...)",
                    _content_to_value(r.content),
                )

            # --- Step 7: Practice Management authors a new bundle ----------
            print("=" * 60)
            print("Step 7: Practice Management authors a new bundle at runtime")
            print("=" * 60)
            print()

            r = await session.call_tool(
                "switch_practice", {"practice_id": "practice_management"}
            )
            _print_value("switch_practice('practice_management')", _content_to_value(r.content))

            r = await session.call_tool(
                "invoke_affordance",
                {
                    "affordance_id": "read_pool",
                    "material_name": "pm_read_pool",
                    "arguments": {"pool": "rules"},
                },
            )
            _print_value(
                "invoke_affordance(read_pool, pm_read_pool, {pool='rules'})",
                _content_to_value(r.content),
            )

            r = await session.call_tool(
                "invoke_affordance",
                {
                    "affordance_id": "author_pool_element",
                    "material_name": "pm_create_element",
                    "arguments": {
                        "pool": "teleo_affective",
                        "id": "te_quick_glance",
                        "name": "Quick glance",
                        "content": (
                            "Give the user a fast read of one thing without "
                            "interpretation — show them what's there and step back."
                        ),
                    },
                },
            )
            _print_value("pm_create_element(te_quick_glance)", _content_to_value(r.content))

            r = await session.call_tool(
                "invoke_affordance",
                {
                    "affordance_id": "author_pool_element",
                    "material_name": "pm_create_element",
                    "arguments": {
                        "pool": "understanding",
                        "id": "und_quick_glance",
                        "name": "Quick glance shape",
                        "content": (
                            "A quick-glance practice surfaces one piece of data "
                            "(a day, an activity, a summary) with no analysis."
                        ),
                    },
                },
            )
            _print_value("pm_create_element(und_quick_glance)", _content_to_value(r.content))

            r = await session.call_tool(
                "invoke_affordance",
                {
                    "affordance_id": "author_pool_element",
                    "material_name": "pm_create_element",
                    "arguments": {
                        "pool": "rules",
                        "id": "rule_quick_glance_no_analysis",
                        "name": "No analysis on the quick glance",
                        "content": (
                            "Return the data plain. Do not summarise, compare, "
                            "or interpret unless the user explicitly asks."
                        ),
                    },
                },
            )
            _print_value(
                "pm_create_element(rule_quick_glance_no_analysis)",
                _content_to_value(r.content),
            )

            r = await session.call_tool(
                "invoke_affordance",
                {
                    "affordance_id": "author_material",
                    "material_name": "pm_create_material",
                    "arguments": {
                        "name": "quick_glance_note",
                        "description": (
                            "Return one dynamically-authored quick-glance datum."
                        ),
                        "input_schema": {
                            "type": "object",
                            "properties": {"date": {"type": "string"}},
                            "required": ["date"],
                        },
                        "implementation": {
                            "kind": "expression",
                            "expression": (
                                '{"date": args["date"], '
                                '"note": "dynamic material function invoked"}'
                            ),
                        },
                    },
                },
            )
            _print_value(
                "pm_create_material(quick_glance_note)",
                _content_to_value(r.content),
            )

            r = await session.call_tool(
                "invoke_affordance",
                {
                    "affordance_id": "author_affordance",
                    "material_name": "pm_create_affordance",
                    "arguments": {
                        "id": "quick_glance_today",
                        "name": "Today at a glance",
                        "description": (
                            "Show today's wellness summary, plain — no analysis."
                        ),
                        "materials": ["quick_glance_note"],
                    },
                },
            )
            _print_value("pm_create_affordance(quick_glance_today)", _content_to_value(r.content))

            r = await session.call_tool(
                "invoke_affordance",
                {
                    "affordance_id": "author_bundle",
                    "material_name": "pm_create_bundle",
                    "arguments": {
                        "id": "quick_glance",
                        "name": "Quick Glance",
                        "description": (
                            "A minimal practice authored at runtime by Practice "
                            "Management — one affordance, one material, no analysis."
                        ),
                        "teleo_affective_ids": ["te_quick_glance"],
                        "understanding_ids": ["und_quick_glance"],
                        "rules_ids": ["rule_quick_glance_no_analysis"],
                        "affordance_ids": ["quick_glance_today"],
                    },
                },
            )
            _print_value("pm_create_bundle(quick_glance)", _content_to_value(r.content))

            # Switch into the newly-authored bundle and invoke its affordance.
            r = await session.call_tool(
                "switch_practice", {"practice_id": "quick_glance"}
            )
            _print_value("switch_practice('quick_glance')", _content_to_value(r.content))

            r = await session.call_tool(
                    "invoke_affordance",
                    {
                        "affordance_id": "quick_glance_today",
                        "material_name": "quick_glance_note",
                        "arguments": {"date": "2026-05-25"},
                    },
                )
            _print_value(
                "invoke_affordance(quick_glance_today, quick_glance_note, ...)",
                _content_to_value(r.content),
            )

            # Confirm list_practices now includes the new bundle
            r = await session.call_tool("list_practices", {})
            _print_value("list_practices()  [after PM]", _content_to_value(r.content))


# --- Scripted handlers used by the autonomic harness in the verify ----------
#
# Each handler is what an LLM enactment would do, scripted for the verify so
# the loop runs deterministically without API keys. In production the
# AnthropicSDKAdapter or CodexExecAdapter replaces these — same harness loop,
# same WorkItems, same MCP surface; the LLM does the deciding.


async def _scripted_judge_handler(work: WorkItem) -> str | None:
    """Open an autonomic MCP session, walk the four Judge primitives, decide,
    emit Friction if warranted, return the Judge enactment id."""
    assert work.metadata is not None
    target_enactment_id = str(work.metadata["enactment_id"])
    bundle_id = str(work.metadata["bundle_id"])

    async with stdio_client(_server_params("autonomic")) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            r = await session.call_tool("switch_practice", {"practice_id": "judge"})
            switched = _content_to_value(r.content) or {}
            judge_enactment_id = switched.get("practice_enactment_id")

            r = await session.call_tool(
                "invoke_affordance",
                {
                    "affordance_id": "read_enactment_steps",
                    "material_name": "judge_read_enactment_steps",
                    "arguments": {"enactment_id": target_enactment_id},
                },
            )
            steps_raw = _content_to_value(r.content)
            if steps_raw is None:
                step_list: list[Any] = []
            elif isinstance(steps_raw, list):
                step_list = steps_raw
            else:
                step_list = [steps_raw]

            r = await session.call_tool(
                "invoke_affordance",
                {
                    "affordance_id": "read_bundle",
                    "material_name": "judge_read_bundle",
                    "arguments": {"bundle_id": bundle_id},
                },
            )
            bundle = _content_to_value(r.content) or {}

            available = set(bundle.get("affordance_ids", []) or [])
            used = {s["affordance_id"] for s in step_list}

            if len(used) <= 1 and len(available) > 1:
                await session.call_tool(
                    "invoke_affordance",
                    {
                        "affordance_id": "emit_friction",
                        "material_name": "judge_emit_friction",
                        "arguments": {
                            "target_enactment_id": target_enactment_id,
                            "kind": "narrow_engagement",
                            "content": (
                                f"Enactment of {bundle_id!r} used only "
                                f"{sorted(used)} of {len(available)} "
                                f"available affordances."
                            ),
                            "observation_data": {
                                "bundle_id": bundle_id,
                                "available_affordances": sorted(available),
                                "used_affordances": sorted(used),
                                "unused_affordances": sorted(available - used),
                            },
                        },
                    },
                )
            return judge_enactment_id


async def _scripted_smoother_handler(work: WorkItem) -> str | None:
    """Read the targeted Friction, interpret it, amend the substrate, mark
    addressed, return the Smoother enactment id."""
    assert work.metadata is not None
    friction_id = int(work.metadata["friction_id"])

    async with stdio_client(_server_params("autonomic")) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            r = await session.call_tool("switch_practice", {"practice_id": "smoother"})
            switched = _content_to_value(r.content) or {}
            smoother_enactment_id = switched.get("practice_enactment_id")

            r = await session.call_tool(
                "invoke_affordance",
                {
                    "affordance_id": "read_pending_friction",
                    "material_name": "smoother_read_pending_friction",
                    "arguments": {},
                },
            )
            pending_raw = _content_to_value(r.content)
            if pending_raw is None:
                items: list[Any] = []
            elif isinstance(pending_raw, list):
                items = pending_raw
            else:
                items = [pending_raw]

            this_friction = next(
                (f for f in items if f.get("id") == friction_id), None
            )
            if this_friction is not None:
                obs = this_friction.get("observation_data") or {}
                if (
                    this_friction.get("kind") == "narrow_engagement"
                    and obs.get("bundle_id")
                ):
                    desc = (
                        f"Practitioners are invited to reach for more than "
                        f"one affordance — this practice exposes "
                        f"{len(obs.get('available_affordances', []))} in total."
                    )
                    await session.call_tool(
                        "invoke_affordance",
                        {
                            "affordance_id": "amend_bundle",
                            "material_name": "pm_amend_bundle",
                            "arguments": {
                                "id": obs["bundle_id"],
                                "description": desc,
                            },
                        },
                    )

            await session.call_tool(
                "invoke_affordance",
                {
                    "affordance_id": "mark_friction_addressed",
                    "material_name": "smoother_mark_addressed",
                    "arguments": {"friction_id": friction_id},
                },
            )
            return smoother_enactment_id


async def verify_autonomic_loop() -> None:
    """Drive the autonomic loop through the harness using ScriptedAdapter."""
    print()
    print("=" * 60)
    print("Autonomic loop (harness with ScriptedAdapter)")
    print("=" * 60)
    print()

    store = EnactmentStore()
    try:
        # Synchronously route any already-closed events into inboxes —
        # the somatic server's dispatcher has just stopped, and we don't
        # want to wait on the autonomic server's dispatcher to catch up.
        j, s = route_now(store)
        print(f"  dispatcher (one-shot): judge_inbox +{j}, smoother_inbox +{s}")

        judge_brief = compose_brief(BUNDLES["judge"], substrate)
        smoother_brief = compose_brief(BUNDLES["smoother"], substrate)

        # Each drain is bounded to the pending count snapshotted at its start.
        # Because subprocess dispatchers are disabled, drains don't compete
        # with the loop for routing; only `route_now` between drains routes.
        judge_pending = store.pending_judge_inbox_count()
        print(f"  pending judge_inbox  : {judge_pending}")
        judge_adapter = ScriptedAdapter(
            AdapterConfig(role="judge", bundle_id="judge", brief=judge_brief),
            _scripted_judge_handler,
        )
        n = await drain(
            judge_adapter,
            RolePolicy(role="judge"),
            store,
            worker_id="verify-judge",
            max_items=max(judge_pending, 1),
        )
        print(f"  Judge drained {n} work item(s)")

        # Judge may have emitted Friction during its run.
        j2, s2 = route_now(store)
        print(f"  dispatcher (one-shot): judge_inbox +{j2}, smoother_inbox +{s2}")

        smoother_pending = store.pending_smoother_inbox_count()
        print(f"  pending smoother_inbox: {smoother_pending}")
        smoother_adapter = ScriptedAdapter(
            AdapterConfig(role="smoother", bundle_id="smoother", brief=smoother_brief),
            _scripted_smoother_handler,
        )
        n = await drain(
            smoother_adapter,
            RolePolicy(role="smoother"),
            store,
            worker_id="verify-smoother",
            max_items=max(smoother_pending, 1),
        )
        print(f"  Smoother drained {n} work item(s)")
        print()

        # Step 12 — the strange loop. The Judge and Smoother enactments that
        # just ran are themselves closed enactments. Route them and run one
        # more bounded pass — Judge examines what Judge and Smoother just did.
        print("Second pass (strange loop — Judge examines Judge/Smoother enactments):")
        j3, s3 = route_now(store)
        print(f"  dispatcher (one-shot): judge_inbox +{j3}, smoother_inbox +{s3}")

        judge_pending_p2 = store.pending_judge_inbox_count()
        print(f"  pending judge_inbox  : {judge_pending_p2}")
        n = await drain(
            ScriptedAdapter(
                AdapterConfig(role="judge", bundle_id="judge", brief=judge_brief),
                _scripted_judge_handler,
            ),
            RolePolicy(role="judge"),
            store,
            worker_id="verify-judge-pass2",
            max_items=max(judge_pending_p2, 1),
        )
        print(f"  Judge drained {n} work item(s) on the second pass")

        j4, s4 = route_now(store)
        if s4:
            print(f"  Friction also routed in pass 2: smoother_inbox +{s4}")
            smoother_pending_p2 = store.pending_smoother_inbox_count()
            n = await drain(
                ScriptedAdapter(
                    AdapterConfig(
                        role="smoother", bundle_id="smoother", brief=smoother_brief
                    ),
                    _scripted_smoother_handler,
                ),
                RolePolicy(role="smoother"),
                store,
                worker_id="verify-smoother-pass2",
                max_items=max(smoother_pending_p2, 1),
            )
            print(f"  Smoother drained {n} on the second pass")
        print()
    finally:
        store.close()


def _print_trail() -> None:
    print("Trail (top-level enactments and their children):")
    store = EnactmentStore()
    try:
        all_recent = store.recent_enactments(limit=40)
        if not all_recent:
            print("  (empty)")
            return
        top_level = [e for e in all_recent if e.parent_enactment_id is None]
        top_level.sort(key=lambda e: e.opened_at)
        if not top_level:
            print("  (no top-level enactments found)")
            return

        # Label: a somatic-engagement enactment uses the engagement bundle id;
        # autonomic top-level enactments are practice bundles (Judge, Smoother).
        for top in top_level:
            label = (
                "engagement"
                if top.practice_id == "user_focused_engagement"
                else "practice (autonomic)"
            )
            _print_enactment(store, top, indent="  ", label=label)
            children = [
                e for e in all_recent if e.parent_enactment_id == top.id
            ]
            children.sort(key=lambda e: e.opened_at)
            for child in children:
                _print_enactment(store, child, indent="    ", label="practice")
    finally:
        store.close()


def _print_enactment(store: EnactmentStore, enactment: Any, *, indent: str, label: str) -> None:
    closed = enactment.closed_at or "(still open)"
    parent = enactment.parent_enactment_id or "(none)"
    print(
        f"{indent}[{label}] enactment {enactment.id}\n"
        f"{indent}  bundle    : {enactment.practice_id}\n"
        f"{indent}  parent    : {parent}\n"
        f"{indent}  opened_at : {enactment.opened_at}\n"
        f"{indent}  closed_at : {closed}"
    )
    steps = store.steps_for(enactment.id)
    print(f"{indent}  steps     : {len(steps)}")
    for s in steps:
        print(
            f"{indent}    [{s.id}] {s.affordance_id} / {s.material_name}  "
            f"({s.duration_ms} ms)"
        )
        print(f"{indent}        arguments : {s.arguments_json}")
        summary = s.result_summary
        if len(summary) > 160:
            summary = summary[:160] + "..."
        print(f"{indent}        result    : {summary}")


async def verify_persistence() -> None:
    """Phase B proof: a brand-new server reads the PM-authored files from disk.

    The somatic walk above authored `quick_glance` (pool elements, a dynamic
    material, an affordance, a bundle) through Practice Management — which now
    dual-writes to the `substrate/` files. This spawns a *fresh* server process
    (same `PRACTICE_SUBSTRATE_DIR`, no shared in-memory state) and confirms the
    authored practice and its dynamic material survived purely as files: the
    bundle lists, and its expression-material rebuilds and invokes.
    """
    print()
    print("=" * 60)
    print("Phase B: fresh server reads the PM-authored substrate from disk")
    print("=" * 60)
    print()
    async with stdio_client(_server_params("somatic")) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            r = await session.call_tool("list_practices", {})
            practices = _content_to_value(r.content)
            ids = (
                {p.get("id") for p in practices if isinstance(p, dict)}
                if isinstance(practices, list)
                else set()
            )
            print(f"  quick_glance persisted to files : {'quick_glance' in ids}")

            r = await session.call_tool(
                "switch_practice", {"practice_id": "quick_glance"}
            )
            _print_value(
                "switch_practice('quick_glance')  [bundle from disk]",
                _content_to_value(r.content),
            )

            r = await session.call_tool(
                "invoke_affordance",
                {
                    "affordance_id": "quick_glance_today",
                    "material_name": "quick_glance_note",
                    "arguments": {"date": "2026-05-25"},
                },
            )
            _print_value(
                "invoke quick_glance_note  [dynamic material rebuilt from disk]",
                _content_to_value(r.content),
            )


async def verify_all() -> None:
    await verify_somatic()
    await verify_persistence()
    await verify_autonomic_loop()


def _print_friction() -> None:
    print()
    print("Friction observations:")
    store = EnactmentStore()
    try:
        all_f = store.all_friction()
        if not all_f:
            print("  (none)")
            return
        for f in all_f:
            state = (
                f"addressed at {f.addressed_at} by {f.addressed_by_enactment_id}"
                if f.addressed_at
                else "PENDING"
            )
            print(
                f"  [{f.id}] {f.kind} -> {f.target_enactment_id}  ({state})\n"
                f"      content   : {f.content[:200]}"
            )
            if f.observation_data_json:
                print(
                    f"      evidence  : "
                    f"{f.observation_data_json[:200]}"
                )
    finally:
        store.close()


def _ensure_hermetic_trail_path() -> None:
    """Point the trail at a fresh temp DB unless the caller set PRACTICE_TRAIL_PATH.

    The verify's narrative assumes a clean trail (empty, no stale Friction). The
    substrate is read from files (see `_ensure_hermetic_substrate_dir`), so only
    the trail needs a hermetic temp DB.
    """
    import tempfile
    from pathlib import Path

    if "PRACTICE_TRAIL_PATH" in os.environ:
        return  # caller opted into a custom trail path; respect it.
    tmpdir = Path(tempfile.mkdtemp(prefix="practice-verify-"))
    os.environ["PRACTICE_TRAIL_PATH"] = str(tmpdir / "trail.db")
    print(f"[verify] using hermetic temp trail at {tmpdir}")
    print("[verify] set PRACTICE_TRAIL_PATH to persist the trail across runs")
    print()


def _ensure_hermetic_substrate_dir() -> None:
    """Copy `substrate/` to a temp dir and point the verify at it.

    Phase B's Practice Management dual-writes amendments back to the substrate
    files. If the verify ran against the checked-in `substrate/`, the PM
    authoring step would mutate tracked files and dirty git. So unless the caller
    set PRACTICE_SUBSTRATE_DIR, the spawned servers read from (and write to) a
    throwaway copy — the authored files are real (so the fresh-server
    persistence check passes), but `substrate/` stays clean. The env var
    propagates to the subprocess servers via `_server_params`'s `**os.environ`.
    """
    import shutil
    import tempfile
    from pathlib import Path

    if "PRACTICE_SUBSTRATE_DIR" in os.environ:
        return  # caller opted into a custom substrate dir; respect it.
    src = Path(__file__).resolve().parents[2] / "substrate"
    dst = Path(tempfile.mkdtemp(prefix="practice-substrate-")) / "substrate"
    shutil.copytree(src, dst)
    os.environ["PRACTICE_SUBSTRATE_DIR"] = str(dst)
    print(f"[verify] using hermetic temp substrate at {dst}")
    print("[verify] PM amendments land here, leaving the tracked substrate/ clean")
    print()


def main() -> None:
    _ensure_hermetic_trail_path()
    _ensure_hermetic_substrate_dir()
    asyncio.run(verify_all())
    print()
    _print_trail()
    _print_friction()


if __name__ == "__main__":
    main()
