"""The practice server — MCP surface for projected practices.

(The prior essays called this the apprenticeship server. At this stage of the
build it apprentices the LLM in a practice and — when the engagement layer
is projected (somatic mode) — about the user. The "apprenticeship server"
name is fully earned only in somatic mode; an autonomic-mode server is
narrower.)

The server has a mode at startup: somatic (default) or autonomic, set via
the PRACTICE_SERVER_MODE environment variable. The mode controls three
things: the catalog the server exposes (filtered by Bundle.mode), whether
the engagement bundle is projected, and whether the somatic-only
`user_engagement` tool is registered. Everything else — the substrate, the
projection rules, the trail — is identical across modes.

Fixed tool surface, exposed once and never changed:

  list_practices         - what bundles are in the catalog
  switch_practice        - project a bundle and make it the session's active practice
  current_practice       - summary of what is active
  user_engagement        - somatic-only: the engagement layer's content
  discover_affordances   - the active practice's affordances, optionally filtered
  invoke_affordance      - dispatch to the active practice's invoke()

Six tools in somatic mode (where `user_engagement` is registered), five in
autonomic mode (where it is not). Affordances surface dynamically through
discover_affordances based on which practice is active.

Alongside the tools, a fixed `practice://*` resource surface exposes the
active projection's composition as readable resources — `practice://current`
plus one per section (teleo-affective, understanding, rules, affordances).
The resource list never changes; the content changes whenever a practice is
switched in. Resources are an alternative read-path to the inline
`composition` field on `current_practice`; clients that prefer the
MCP resource model can subscribe and read.

In stdio transport each connection is its own process, so the active
practice is module-level state. HTTP transport is still experimental here:
until per-session lifespan state lands, it is safe only for one client per
server process and must be opted into explicitly.

Run directly to serve over stdio (the client launches this as a subprocess):

    python -m practice_theory_implementation.server
"""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from typing import Any

from mcp.server.fastmcp import FastMCP

from practice_theory_implementation.bundles import BUNDLES, ENGAGEMENT_BUNDLE
from practice_theory_implementation.materials.judge import (
    configure as configure_judge,
)
from practice_theory_implementation.materials.practice_management import (
    configure as configure_practice_management,
)
from practice_theory_implementation.materials.smoother import (
    configure as configure_smoother,
)
from practice_theory_implementation.pools import substrate
from practice_theory_implementation.projection import (
    ProjectedPractice,
    compose_composition,
    project,
)
from practice_theory_implementation.registry import (
    FUNCTIONS,
    register_dynamic_material,
    register_dynamic_materials,
)
from practice_theory_implementation.substrate_store import (
    SubstrateStore,
    apply_overlay_to_bundles,
    apply_overlay_to_substrate,
)
from practice_theory_implementation.trail import EnactmentStore, time_call


class _AuthoringCatalog(dict[str, Any]):
    """Catalog PM can amend, while only practice bundles stay switchable."""

    def __setitem__(self, key: str, value: Any) -> None:
        super().__setitem__(key, value)
        if key != ENGAGEMENT_BUNDLE.id:
            BUNDLES[key] = value


# Mode is set at startup via PRACTICE_SERVER_MODE; default is somatic.
_MODE: str = os.environ.get("PRACTICE_SERVER_MODE", "somatic")
if _MODE not in ("somatic", "autonomic"):
    raise ValueError(
        f"PRACTICE_SERVER_MODE must be 'somatic' or 'autonomic', got {_MODE!r}"
    )

# Transport is set at startup via PRACTICE_TRANSPORT; default stdio so the
# verify works without configuration. HTTP is useful for manual experiments
# with a long-lived server, but this module still keeps active projection
# state in globals, so concurrent HTTP clients would race on that state.
_TRANSPORT: str = os.environ.get("PRACTICE_TRANSPORT", "stdio")
if _TRANSPORT not in ("stdio", "http"):
    raise ValueError(
        f"PRACTICE_TRANSPORT must be 'stdio' or 'http', got {_TRANSPORT!r}"
    )
if _TRANSPORT == "http" and os.environ.get("PRACTICE_EXPERIMENTAL_HTTP") != "1":
    raise ValueError(
        "PRACTICE_TRANSPORT=http is experimental because active practice state "
        "is process-global. Set PRACTICE_EXPERIMENTAL_HTTP=1 to opt in, and "
        "use only one client per server process until per-session state lands."
    )
_HTTP_HOST: str = os.environ.get("PRACTICE_HTTP_HOST", "127.0.0.1")
_HTTP_PORT: int = int(os.environ.get("PRACTICE_HTTP_PORT", "7180"))
_ENGAGEMENT_IDLE_CLOSE_SECONDS: int = int(
    os.environ.get("PRACTICE_ENGAGEMENT_IDLE_CLOSE_SECONDS", "600")
)

_SOMATIC_INSTRUCTIONS = """\
This is the apprenticeship server in somatic mode — a standing arrangement \
with the user, within which discrete practices are reached for. The \
engagement bundle is projected at session open; every practice you switch \
into inherits its teleo-affective, rules, and affordances additively.

Start by reading `user_engagement` to see what the apprenticeship knows \
about the user before deciding which practice to engage. Then `list_practices` \
to see what is available, `switch_practice(practice_id)` to engage one, \
`current_practice` to read the merged composition (engagement + practice), \
`discover_affordances(query?)` to find the affordances available, and \
`invoke_affordance(affordance_id, material_name, arguments)` to act.

Every invocation is recorded on the trail. Engagement-layer affordances \
(e.g. `about_the_user`) record on the engagement enactment; practice-layer \
affordances record on the active practice enactment, whose `parent_enactment_id` \
points at the engagement. The trail is the substrate trust rests on — \
inspectable by you, the user, and downstream Judge enactments.

The active projection is also readable as MCP resources: `practice://current` \
(full composition), `practice://teleo-affective`, `practice://understanding`, \
`practice://rules`, `practice://affordances`. Same content as the inline \
`composition` field on `current_practice`; pick whichever read-path fits \
your client.
"""

_AUTONOMIC_INSTRUCTIONS = """\
This is the apprenticeship server in autonomic mode. There is no user in \
the loop; you are an autonomic practitioner (Judge or Smoother) tending the \
substrate. The engagement layer is not projected — autonomic practices have \
no user-focus to inherit.

Use `list_practices` to see autonomic bundles, `switch_practice(practice_id)` \
to enact one, `discover_affordances(query?)` to find what's available, and \
`invoke_affordance(affordance_id, material_name, arguments)` to act. The \
Judge reads the trail and emits Friction observations; the Smoother reads \
pending Friction and amends the substrate through Practice Management's \
meta-materials.

Your own enactment is recorded on the trail too. The dispatcher routes \
closed enactments — yours included — into `judge_inbox`, so the loop is \
recursive by construction: the Judge can be judged, the Smoother can amend \
the Smoother. Read the bundle's understanding before acting; its prose \
carries the heuristics.

The active projection is also readable as MCP resources: `practice://current` \
(full composition), `practice://teleo-affective`, `practice://understanding`, \
`practice://rules`, `practice://affordances`.
"""

_SERVER_INSTRUCTIONS: str = (
    _SOMATIC_INSTRUCTIONS if _MODE == "somatic" else _AUTONOMIC_INSTRUCTIONS
)

mcp_app: FastMCP = FastMCP(
    f"practice-server-{_MODE}",
    instructions=_SERVER_INSTRUCTIONS,
    host=_HTTP_HOST,
    port=_HTTP_PORT,
)

_trail: EnactmentStore = EnactmentStore()

# Open the substrate overlay store and merge runtime amendments into the
# in-memory substrate and bundle catalog before anything else reads them.
_substrate_store: SubstrateStore = SubstrateStore()
apply_overlay_to_substrate(substrate, _substrate_store)
register_dynamic_materials(_substrate_store.overlay_material_functions())
apply_overlay_to_bundles(BUNDLES, _substrate_store)
BUNDLES.pop(ENGAGEMENT_BUNDLE.id, None)
_AUTHORING_BUNDLES: _AuthoringCatalog = _AuthoringCatalog({
    **BUNDLES,
    ENGAGEMENT_BUNDLE.id: ENGAGEMENT_BUNDLE,
})
apply_overlay_to_bundles(_AUTHORING_BUNDLES, _substrate_store)

# Wire Practice Management's meta-materials to the live substrate, catalog,
# and overlay store. Without this, pm_* materials raise RuntimeError.
configure_practice_management(
    substrate=substrate,
    bundle_catalog=_AUTHORING_BUNDLES,
    store=_substrate_store,
    register_material_function=register_dynamic_material,
)

# Wire Judge and Smoother to the trail and (Judge) substrate/catalog. They
# need to know the active enactment id at invoke time so they can record
# Friction / mark-addressed against the right enactment; that comes via a
# getter callable that reads our module-level _active_practice_enactment_id.
configure_judge(
    trail=_trail,
    substrate=substrate,
    bundle_catalog=_AUTHORING_BUNDLES,
    observing_enactment_id_getter=lambda: _active_practice_enactment_id,
)
configure_smoother(
    trail=_trail,
    active_enactment_id_getter=lambda: _active_practice_enactment_id,
)

# The engagement is projected only in somatic mode. Autonomic practitioners
# (Judge, Smoother in later steps) have no user-focus to inherit.
_engagement: ProjectedPractice | None = None
_engagement_bundle: Any | None = None
_engagement_enactment_id: str | None = None
_engagement_affordance_ids: frozenset[str] = frozenset()
_last_step_at: datetime | None = None

# A practice is optional — none active until switch_practice is called.
_active_practice: ProjectedPractice | None = None
_active_practice_enactment_id: str | None = None


def _now_dt() -> datetime:
    return datetime.now(UTC)


def _parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _mark_activity(value: str | None = None) -> None:
    global _last_step_at
    _last_step_at = _parse_dt(value) if value is not None else _now_dt()


def _close_active_practice_enactment() -> None:
    global _active_practice, _active_practice_enactment_id
    if _active_practice_enactment_id is not None:
        _trail.close_enactment(_active_practice_enactment_id)
    _active_practice = None
    _active_practice_enactment_id = None


def _maybe_close_idle_engagement_segment() -> None:
    """Close a complete engagement segment after a noticeable idle gap."""
    global _engagement_enactment_id, _last_step_at
    if _MODE != "somatic" or _ENGAGEMENT_IDLE_CLOSE_SECONDS <= 0:
        return
    if _last_step_at is None:
        return
    idle_for = _now_dt() - _last_step_at
    if idle_for < timedelta(seconds=_ENGAGEMENT_IDLE_CLOSE_SECONDS):
        return
    _close_active_practice_enactment()
    if _engagement_enactment_id is not None:
        _trail.close_enactment(_engagement_enactment_id)
    _engagement_enactment_id = None
    _last_step_at = None
    _refresh_engagement_projection(force=True)


def _refresh_engagement_projection(*, force: bool = False) -> None:
    """Keep the projected engagement in sync with PM-authored amendments."""
    global _active_practice, _engagement, _engagement_affordance_ids
    global _engagement_bundle, _engagement_enactment_id
    if _MODE != "somatic":
        return
    bundle = _AUTHORING_BUNDLES[ENGAGEMENT_BUNDLE.id]
    if (
        not force
        and bundle == _engagement_bundle
        and _engagement_enactment_id is not None
    ):
        return
    _engagement = project(bundle, substrate, FUNCTIONS)
    _engagement_bundle = bundle
    _engagement_affordance_ids = frozenset(a.id for a in _engagement.affordances)
    if _engagement_enactment_id is None:
        _engagement_enactment_id = _trail.open_enactment(_engagement.id)
        _mark_activity()
    if _active_practice is not None and _active_practice.id in BUNDLES:
        _active_practice = project(
            BUNDLES[_active_practice.id],
            substrate,
            FUNCTIONS,
            engagement=_engagement,
        )


_refresh_engagement_projection(force=True)


@mcp_app.tool()
def list_practices() -> list[dict[str, str]]:
    """Return the practice bundles in the catalog whose mode matches the server's."""
    return [
        {"id": b.id, "name": b.name, "description": b.description, "mode": b.mode}
        for b in BUNDLES.values()
        if b.mode == _MODE
    ]


@mcp_app.tool()
def switch_practice(practice_id: str) -> dict[str, Any]:
    """Project the named bundle (with the engagement merged in) and activate it.

    Closes the current practice enactment (if any) and opens a new one whose
    parent_enactment_id points at the engagement enactment, so the trail
    records the layering.
    """
    global _active_practice, _active_practice_enactment_id
    _maybe_close_idle_engagement_segment()
    _refresh_engagement_projection()
    if practice_id not in BUNDLES:
        return {
            "error": f"unknown practice {practice_id!r}",
            "available": [b.id for b in BUNDLES.values() if b.mode == _MODE],
        }
    bundle = BUNDLES[practice_id]
    if bundle.mode != _MODE:
        return {
            "error": (
                f"practice {practice_id!r} is {bundle.mode}; server is {_MODE}"
            ),
        }
    if _active_practice_enactment_id is not None:
        _trail.close_enactment(_active_practice_enactment_id)
    _active_practice = project(
        bundle, substrate, FUNCTIONS, engagement=_engagement
    )
    _active_practice_enactment_id = _trail.open_enactment(
        _active_practice.id, parent_enactment_id=_engagement_enactment_id
    )
    _mark_activity()
    return {
        "active": _active_practice.id,
        "name": _active_practice.name,
        "mode": _MODE,
        "engagement_enactment_id": _engagement_enactment_id,
        "practice_enactment_id": _active_practice_enactment_id,
    }


@mcp_app.tool()
def current_practice() -> dict[str, Any]:
    """Return the active practice's projection, with composition.

    Shape:
      {
        "mode": "somatic" | "autonomic",
        "practice": {"id", "name", "description"} | None,
        "enactment_id": str | None,
        "composition": str | None,
      }

    On a fresh session, `practice`, `enactment_id`, and `composition` are
    all `None` until `switch_practice` is called. In somatic mode the
    engagement layer is always available via the separate `user_engagement`
    tool; the composition returned here is the active practice's full
    projection (engagement content merged in).
    """
    _refresh_engagement_projection()
    if _active_practice is None:
        return {
            "mode": _MODE,
            "practice": None,
            "enactment_id": None,
            "composition": None,
        }
    p = _active_practice
    return {
        "mode": _MODE,
        "practice": {
            "id": p.id,
            "name": p.name,
            "description": p.description,
        },
        "enactment_id": _active_practice_enactment_id,
        "composition": compose_composition(p),
    }


# user_engagement is a somatic-only tool — registered only when the server is
# in somatic mode (and thus has a projected engagement). Autonomic mode does
# not expose it, so the autonomic surface stays at five tools while the
# somatic surface is six. The asymmetry is honest: engagement is a somatic
# concept; the autonomic loop has no user to be engaged with.
if _MODE == "somatic":

    @mcp_app.tool()
    def user_engagement() -> dict[str, Any]:
        """Return the engagement layer's content (somatic only).

        Renders the engagement bundle — its teleo-affective, understanding,
        rules, and affordances — as a markdown composition, without the
        active practice merged in. Always available regardless of whether
        a practice is currently engaged. Use to read the apprenticeship as
        a first-class thing before deciding which practice to engage.

        Distinct from `current_practice`, which returns the active practice
        with engagement merged in.
        """
        _refresh_engagement_projection()
        assert _engagement is not None  # somatic mode implies projection
        e = _engagement
        return {
            "id": e.id,
            "name": e.name,
            "description": e.description,
            "composition": compose_composition(e),
        }


@mcp_app.tool()
def discover_affordances(query: str | None = None) -> list[dict[str, Any]]:
    """List the active projection's affordances, optionally filtered.

    Engagement affordances are always present (engagement is projected at
    server startup); practice affordances appear once a practice is switched
    in. `query` is a case-insensitive substring match against name and
    description. Each result is tagged with `layer` so the caller can see
    which is engagement and which is practice.

    Each affordance's `materials` field is a list of
    `{name, description, input_schema}` objects rather than just names.
    The per-material `input_schema` matters because the harness LLM
    constructing the `arguments` payload for `invoke_affordance` needs to
    know what shape to send, and the generic tool surface does not
    otherwise expose per-material schemas — surfacing them here puts the
    schema in front of the LLM at the same moment it learns the affordance
    exists.
    """
    _refresh_engagement_projection()
    active = _active_practice or _engagement
    if active is None:
        return []
    q = query.lower() if query else None
    materials_by_name = {m.name: m for m in active.materials}
    out: list[dict[str, Any]] = []
    for aff in active.affordances:
        if q is not None and q not in aff.name.lower() and q not in aff.description.lower():
            continue
        material_views: list[dict[str, Any]] = []
        for mat_name in aff.materials:
            mat = materials_by_name.get(mat_name)
            if mat is None:
                material_views.append(
                    {"name": mat_name, "description": None, "input_schema": None}
                )
            else:
                material_views.append(
                    {
                        "name": mat.name,
                        "description": mat.description,
                        "input_schema": dict(mat.input_schema),
                    }
                )
        out.append(
            {
                "id": aff.id,
                "name": aff.name,
                "description": aff.description,
                "materials": material_views,
                "layer": (
                    "engagement" if aff.id in _engagement_affordance_ids else "practice"
                ),
            }
        )
    return out


@mcp_app.tool()
def invoke_affordance(
    affordance_id: str,
    material_name: str,
    arguments: dict[str, Any] | None = None,
) -> Any:
    """Dispatch through the active practice's invoke() and return the result.

    Records a step on the active enactment's trail with the arguments, the
    result (summarised), and the call's timing. Errors during invocation come
    back as `{"error": "..."}` rather than as transport-level exceptions, so
    the harness sees a clean tool result. This holds for any exception a
    material can raise — the projection's own KeyError/ValueError validation,
    a TypeError from a mismatched argument payload, or a domain error from the
    material body — not just the validation failures. Failed calls are still
    recorded, so the trail (and the Judge reading it) sees the failure too.
    """
    args = arguments or {}
    _maybe_close_idle_engagement_segment()
    _refresh_engagement_projection()
    is_engagement_call = affordance_id in _engagement_affordance_ids
    active = _active_practice or _engagement
    if active is None:
        return {"error": "no active practice; call switch_practice first"}
    if not is_engagement_call and _active_practice is None:
        return {"error": "no active practice; call switch_practice first"}
    with time_call() as timing:
        try:
            result: Any = active.invoke(
                affordance_id=affordance_id,
                material_name=material_name,
                arguments=args,
            )
        except Exception as exc:  # noqa: BLE001 — clean tool result is the contract
            # The message carries the exception type because an unexpected
            # error (e.g. a bare TypeError) often has a terse or empty str(),
            # and the type is what makes the recorded step diagnosable.
            result = {"error": f"{type(exc).__name__}: {exc}"}
    target_enactment = (
        _engagement_enactment_id if is_engagement_call else _active_practice_enactment_id
    )
    if target_enactment is not None:
        _trail.record_step(
            enactment_id=target_enactment,
            affordance_id=affordance_id,
            material_name=material_name,
            arguments=args,
            result=result,
            started_at=timing["started_at"],
            completed_at=timing["completed_at"],
            duration_ms=timing["duration_ms"],
        )
    _mark_activity(timing["completed_at"])
    return result


# ---------------------------------------------------------------------------
# Resource surface — five fixed URIs reading from the active projection.
#
# The resource *list* never changes (no resources/list_changed nudge needed
# in either direction). The *content* changes whenever switch_practice is
# called. The composition is also returned inline by current_practice; the
# resource surface is provided for clients that prefer the MCP resource read
# model over a tool round-trip.
# ---------------------------------------------------------------------------

_NO_ACTIVE_MARKDOWN = (
    "_No active practice. Call `switch_practice(practice_id)` to engage one._"
)


def _active_for_resources() -> ProjectedPractice | None:
    """Return the active projection for resource reads.

    In somatic mode the engagement is projected at startup and stands in
    until a practice is switched into. In autonomic mode there is no
    engagement, so resources resolve only when a practice is active.
    """
    _refresh_engagement_projection()
    return _active_practice or _engagement


@mcp_app.resource("practice://current", mime_type="text/markdown")
def resource_current() -> str:
    """The active projection's full composition as Markdown."""
    active = _active_for_resources()
    if active is None:
        return _NO_ACTIVE_MARKDOWN
    return compose_composition(active)


@mcp_app.resource("practice://teleo-affective", mime_type="text/markdown")
def resource_teleo_affective() -> str:
    """The active projection's teleo-affective section."""
    active = _active_for_resources()
    if active is None:
        return _NO_ACTIVE_MARKDOWN
    parts: list[str] = ["## Teleo-affective", ""]
    for el in active.teleo_affective:
        parts.extend([f"### {el.name}", "", el.content, ""])
    return "\n".join(parts)


@mcp_app.resource("practice://understanding", mime_type="text/markdown")
def resource_understanding() -> str:
    """The active projection's understanding section."""
    active = _active_for_resources()
    if active is None:
        return _NO_ACTIVE_MARKDOWN
    parts: list[str] = ["## Understanding", ""]
    for el in active.understanding:
        parts.extend([f"### {el.name}", "", el.content, ""])
    return "\n".join(parts)


@mcp_app.resource("practice://rules", mime_type="text/markdown")
def resource_rules() -> str:
    """The active projection's rules section."""
    active = _active_for_resources()
    if active is None:
        return _NO_ACTIVE_MARKDOWN
    parts: list[str] = ["## Rules", ""]
    for el in active.rules:
        parts.append(f"- **{el.name}** — {el.content}")
    parts.append("")
    return "\n".join(parts)


@mcp_app.resource("practice://affordances", mime_type="text/markdown")
def resource_affordances() -> str:
    """The active projection's affordances section."""
    active = _active_for_resources()
    if active is None:
        return _NO_ACTIVE_MARKDOWN
    parts: list[str] = ["## Affordances available", ""]
    for aff in active.affordances:
        parts.append(f"- `{aff.id}` ({aff.name}) — {aff.description}")
    parts.append("")
    return "\n".join(parts)


async def _shutdown_handler() -> None:
    """Close still-open enactments so the dispatcher can route a complete trail."""
    global _active_practice_enactment_id, _engagement_enactment_id
    if _active_practice_enactment_id is not None:
        _trail.close_enactment(_active_practice_enactment_id)
        _active_practice_enactment_id = None
    if _engagement_enactment_id is not None:
        _trail.close_enactment(_engagement_enactment_id)
        _engagement_enactment_id = None


async def _serve_with_dispatcher() -> None:
    """Run the MCP server (stdio or http) and the dispatcher concurrently.

    The dispatcher can be turned off via PRACTICE_DISABLE_DISPATCHER — useful
    when this process is a short-lived worker (e.g. an autonomic adapter's
    per-dispatch subprocess) and the routing is owned by another long-lived
    process or by a one-shot caller like the verify's route_now.
    """
    import asyncio as _asyncio
    import logging as _logging
    import sys as _sys

    from practice_theory_implementation.autonomic_dispatcher import dispatcher_task

    log_level_name = os.environ.get("PRACTICE_LOG_LEVEL", "WARNING").upper()
    log_level = getattr(_logging, log_level_name, _logging.WARNING)
    _logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(name)s %(message)s",
        stream=_sys.stderr,
    )

    stop = _asyncio.Event()
    dispatcher_disabled = os.environ.get("PRACTICE_DISABLE_DISPATCHER", "").strip()
    dispatcher: _asyncio.Task[None] | None = None
    if not dispatcher_disabled:
        dispatcher = _asyncio.create_task(dispatcher_task(stop, store=_trail))
    try:
        if _TRANSPORT == "http":
            await mcp_app.run_streamable_http_async()
        else:
            await mcp_app.run_stdio_async()
    finally:
        await _shutdown_handler()
        if dispatcher is not None:
            stop.set()
            await dispatcher


if __name__ == "__main__":
    import asyncio as _asyncio

    _asyncio.run(_serve_with_dispatcher())
