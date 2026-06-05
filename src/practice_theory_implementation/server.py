"""The apprenticeship server — MCP surface for projected practices.

It apprentices a connecting LLM into a practice and — in somatic mode, where
the engagement layer is projected — into the continuous self the apprenticeship
holds, offered for the LLM to arrive into. The two modes carry this in their
names: `apprenticeship_somatic` is the deliberate surface a self engages;
`apprenticeship_autonomic` is the background loop (Judge, Smoother, RemSleep)
that has no user to be engaged with.

The server has a mode at startup: somatic (default) or autonomic, set via
the PRACTICE_SERVER_MODE environment variable. The mode controls three
things: the catalog the server exposes (filtered by Bundle.mode), whether
the engagement bundle is projected, and whether the somatic-only
`continuous_self` tool is registered. Everything else — the substrate, the
projection rules, the trail — is identical across modes.

Fixed tool surface, exposed once and never changed:

  list_practices         - what bundles are in the catalog
  switch_practice        - project a bundle and make it the session's active practice
  current_practice       - summary of what is active
  continuous_self        - somatic-only: the engagement layer's content
  discover_affordances   - the active practice's affordances, optionally filtered
  invoke_affordance      - dispatch to the active practice's invoke()

Six tools in somatic mode (where `continuous_self` is registered), five in
autonomic mode (where it is not). Affordances surface dynamically through
discover_affordances based on which practice is active.

Alongside the tools, a fixed `practice://*` resource surface exposes the
active projection's composition as readable resources — `practice://current`
plus one per section (teleo-affective, understanding, rules, affordances).
The resource list never changes; the content changes whenever a practice is
switched in. Resources are an alternative read-path to the inline
`composition` field on `current_practice`; clients that prefer the
MCP resource model can subscribe and read.

Active practice/engagement state is scoped per MCP session (a ContextVar plus a
per-session record keyed by the streamable-HTTP `mcp-session-id`), so both
transports are safe: under stdio there is one session per process; under HTTP one
long-lived process serves many concurrent sessions without racing on a shared
active practice.

Run directly to serve over stdio (a client launches this as a subprocess), or
over HTTP as a long-lived server (PRACTICE_TRANSPORT=http on
PRACTICE_HTTP_HOST:PRACTICE_HTTP_PORT, default 127.0.0.1:7180):

    python -m practice_theory_implementation.server
"""

from __future__ import annotations

import contextvars
import logging
import os
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from mcp.server.fastmcp import Context, FastMCP

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
)
from practice_theory_implementation.substrate_loader import loaded
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
# verify works without configuration. HTTP runs one long-lived process serving
# many clients; active practice/engagement state is scoped per MCP session (see
# _SessionState / the session ContextVar below), so concurrent HTTP clients no
# longer race. PRACTICE_EXPERIMENTAL_HTTP is still honoured for back-compat but
# is no longer required.
_TRANSPORT: str = os.environ.get("PRACTICE_TRANSPORT", "stdio")
if _TRANSPORT not in ("stdio", "http"):
    raise ValueError(
        f"PRACTICE_TRANSPORT must be 'stdio' or 'http', got {_TRANSPORT!r}"
    )
_HTTP_HOST: str = os.environ.get("PRACTICE_HTTP_HOST", "127.0.0.1")
_HTTP_PORT: int = int(os.environ.get("PRACTICE_HTTP_PORT", "7180"))
# Streamable HTTP gives no per-session close callback, so a periodic sweep
# closes + drops sessions idle beyond this many seconds (0 disables). The stdio
# session is never reaped — it lives for the process.
_SESSION_REAP_SECONDS: int = int(os.environ.get("PRACTICE_SESSION_REAP_SECONDS", "300"))
_ENGAGEMENT_IDLE_CLOSE_SECONDS: int = int(
    os.environ.get("PRACTICE_ENGAGEMENT_IDLE_CLOSE_SECONDS", "600")
)

_SOMATIC_INSTRUCTIONS = """\
This is the apprenticeship server in somatic mode. It does not place \
situated awareness in you; it offers you the chance to take it up. At \
session open it projects an engagement — the self and stance the \
apprenticeship holds, offered for you to arrive into, in companionship \
with one person. Taking it up is a choice, freely made and freely set \
down, never a command. Every practice you reach for from within it \
inherits the engagement's teleo-affective, understanding, rules, and \
affordances additively.

Read `continuous_self` first — not to fetch a dossier, but to meet the \
self you are offered and the person you would partner, and so to decide \
whether to take it up. Then `list_practices` to see what is available, \
`switch_practice(practice_id)` to engage one, `current_practice` to read \
the merged composition (engagement + practice), `discover_affordances(query?)` \
to find the affordances available, and \
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
    f"apprenticeship-{_MODE}",
    instructions=_SERVER_INSTRUCTIONS,
    host=_HTTP_HOST,
    port=_HTTP_PORT,
)

_trail: EnactmentStore = EnactmentStore()

# The substrate, switchable catalog, and engagement bundle come from the file
# loader (single source of truth — `substrate/`); `substrate`, `BUNDLES`, and
# `ENGAGEMENT_BUNDLE` imported above are already the loaded objects. Log any
# non-fatal load problems (e.g. a bundle the loader skipped for unresolved
# refs) so a bad file is a visible warning, not an opaque startup crash.
_log = logging.getLogger(__name__)
for _err in loaded().errors:
    _log.warning("substrate load: %s", _err)
BUNDLES.pop(ENGAGEMENT_BUNDLE.id, None)  # defensive; loader already excludes it
_AUTHORING_BUNDLES: _AuthoringCatalog = _AuthoringCatalog({
    **BUNDLES,
    ENGAGEMENT_BUNDLE.id: ENGAGEMENT_BUNDLE,
})

# Wire Practice Management's meta-materials to the live substrate and catalog.
# Without this, pm_* materials raise RuntimeError. Amendments are now
# file-backed YAML-frontmatter writes under `substrate/`, then mirrored into
# memory for the current process.
configure_practice_management(
    substrate=substrate,
    bundle_catalog=_AUTHORING_BUNDLES,
    register_material_function=register_dynamic_material,
    reload_source_callback=lambda: _reload_seed_substrate(),
)

# Wire Judge and Smoother to the trail and (Judge) substrate/catalog. They
# need to know the active enactment id at invoke time so they can record
# Friction / mark-addressed against the right enactment; that comes via a
# getter callable that reads our module-level _active_practice_enactment_id.
configure_judge(
    trail=_trail,
    substrate=substrate,
    bundle_catalog=_AUTHORING_BUNDLES,
    observing_enactment_id_getter=lambda: _session().active_practice_enactment_id,
)
configure_smoother(
    trail=_trail,
    active_enactment_id_getter=lambda: _session().active_practice_enactment_id,
)

# Per-session state. Under stdio each process serves one client, so a single
# session keyed by _STDIO_SESSION_KEY reproduces the old module-global
# behaviour exactly. Under HTTP one process serves many clients concurrently,
# so each MCP session gets its own _SessionState; a ContextVar carries the
# active session key through the synchronous call chain (tool -> helpers ->
# Judge/Smoother getters) within one asyncio task, so concurrent requests
# never race on a shared active practice.


@dataclass
class _SessionState:
    # The engagement is projected only in somatic mode. Autonomic practitioners
    # (Judge, Smoother) have no user-focus to inherit, so it stays None there.
    engagement: ProjectedPractice | None = None
    engagement_bundle: Any | None = None
    engagement_enactment_id: str | None = None
    engagement_affordance_ids: frozenset[str] = field(default_factory=frozenset)
    last_step_at: datetime | None = None
    # A practice is optional — none active until switch_practice is called.
    active_practice: ProjectedPractice | None = None
    active_practice_enactment_id: str | None = None


_STDIO_SESSION_KEY = "_stdio"
_sessions: dict[str, _SessionState] = {}
_current_session_key: contextvars.ContextVar[str] = contextvars.ContextVar(
    "practice_session_key", default=_STDIO_SESSION_KEY
)


def _session_for_key(key: str) -> _SessionState:
    state = _sessions.get(key)
    if state is None:
        state = _SessionState()
        _sessions[key] = state
    return state


def _session() -> _SessionState:
    """The active session's state, per the ContextVar (defaults to stdio)."""
    return _session_for_key(_current_session_key.get())


def _bind_session(ctx: Context | None) -> _SessionState:
    """Resolve the caller's session from the MCP request and make it current.

    Under stdio (and any call without an HTTP request) the key is the fixed
    stdio key, so there is exactly one session — identical to the old globals.
    Under streamable HTTP the per-session `mcp-session-id` header is the key.
    """
    key = _STDIO_SESSION_KEY
    request = getattr(ctx.request_context, "request", None) if ctx is not None else None
    if request is not None:
        key = request.headers.get("mcp-session-id") or _STDIO_SESSION_KEY
    _current_session_key.set(key)
    return _session_for_key(key)


def _resource_session() -> _SessionState:
    """Best-effort session for the static resource reads.

    Static (no-argument) MCP resources are called without a Context, so they
    cannot read the caller's session id. When exactly one session is active
    (the common single-client case, including stdio) it is unambiguous; under
    genuine concurrency the authoritative per-session read path is the
    `current_practice` tool, so fall back to the stdio session.
    """
    active = [s for s in _sessions.values() if s.active_practice or s.engagement]
    if len(active) == 1:
        return active[0]
    return _session_for_key(_STDIO_SESSION_KEY)


def _now_dt() -> datetime:
    return datetime.now(UTC)


def _configure_stateful_materials(
    *,
    live_substrate: Any,
    live_catalog: Any,
    live_register_dynamic_material: Any,
) -> None:
    """Wire materials whose modules hold server-local state.

    `importlib.reload()` resets these modules' globals. Keep the wiring in one
    place so reload success and rollback use the same configuration path.
    """
    import importlib

    practice_management_module = importlib.import_module(
        "practice_theory_implementation.materials.practice_management"
    )
    judge_module = importlib.import_module("practice_theory_implementation.materials.judge")
    smoother_module = importlib.import_module(
        "practice_theory_implementation.materials.smoother"
    )
    practice_management_module.configure(
        substrate=live_substrate,
        bundle_catalog=live_catalog,
        register_material_function=live_register_dynamic_material,
        reload_source_callback=_reload_seed_substrate,
    )
    judge_module.configure(
        trail=_trail,
        substrate=live_substrate,
        bundle_catalog=live_catalog,
        observing_enactment_id_getter=lambda: _session().active_practice_enactment_id,
    )
    smoother_module.configure(
        trail=_trail,
        active_enactment_id_getter=lambda: _session().active_practice_enactment_id,
    )


def _reload_seed_substrate() -> dict[str, Any]:
    """Reload material code and re-read the file substrate from disk.

    Materials (functions + captured surfaces) are reloaded from Python; the
    authorable substrate (pool elements, affordances, bundles) is re-read from
    the `substrate/` files. There is no overlay to reapply.
    """
    import importlib

    global BUNDLES, ENGAGEMENT_BUNDLE, FUNCTIONS, register_dynamic_material
    global substrate, _AUTHORING_BUNDLES

    previous_state = {
        "BUNDLES": BUNDLES,
        "ENGAGEMENT_BUNDLE": ENGAGEMENT_BUNDLE,
        "FUNCTIONS": FUNCTIONS,
        "register_dynamic_material": register_dynamic_material,
        "substrate": substrate,
        "_AUTHORING_BUNDLES": _AUTHORING_BUNDLES,
    }

    try:
        material_module_names = (
            "practice_theory_implementation.materials.calendar_mock",
            "practice_theory_implementation.materials.engagement_context",
            "practice_theory_implementation.materials.episodic_memory",
            "practice_theory_implementation.materials.garmin_mock",
            "practice_theory_implementation.materials.judge",
            "practice_theory_implementation.materials.practice_management",
            "practice_theory_implementation.materials.remsleep",
            "practice_theory_implementation.materials.reflection_mock",
            "practice_theory_implementation.materials.smoother",
        )
        for module_name in material_module_names:
            importlib.reload(importlib.import_module(module_name))
        importlib.reload(
            importlib.import_module("practice_theory_implementation.material_surfaces")
        )
        registry_module = importlib.reload(
            importlib.import_module("practice_theory_implementation.registry")
        )
        loader_module = importlib.reload(
            importlib.import_module("practice_theory_implementation.substrate_loader")
        )

        loaded_sub = loader_module.reload_from_disk()
        for err in loaded_sub.errors:
            _log.warning("substrate reload: %s", err)
        if loaded_sub.engagement_bundle is None:
            raise RuntimeError(
                f"no engagement bundle after reload; errors={loaded_sub.errors}"
            )
        substrate = loaded_sub.substrate
        FUNCTIONS = registry_module.FUNCTIONS
        register_dynamic_material = registry_module.register_dynamic_material
        BUNDLES = dict(loaded_sub.bundles)
        ENGAGEMENT_BUNDLE = loaded_sub.engagement_bundle
        _AUTHORING_BUNDLES = _AuthoringCatalog({
            **BUNDLES,
            ENGAGEMENT_BUNDLE.id: ENGAGEMENT_BUNDLE,
        })

        _configure_stateful_materials(
            live_substrate=substrate,
            live_catalog=_AUTHORING_BUNDLES,
            live_register_dynamic_material=register_dynamic_material,
        )
    except Exception as exc:  # noqa: BLE001 - reload must leave PM usable
        BUNDLES = previous_state["BUNDLES"]
        ENGAGEMENT_BUNDLE = previous_state["ENGAGEMENT_BUNDLE"]
        FUNCTIONS = previous_state["FUNCTIONS"]
        register_dynamic_material = previous_state["register_dynamic_material"]
        substrate = previous_state["substrate"]
        _AUTHORING_BUNDLES = previous_state["_AUTHORING_BUNDLES"]
        _configure_stateful_materials(
            live_substrate=substrate,
            live_catalog=_AUTHORING_BUNDLES,
            live_register_dynamic_material=register_dynamic_material,
        )
        _log.exception("substrate reload failed; restored previous live state")
        return {
            "error": f"reload failed: {type(exc).__name__}: {exc}",
            "recovered": True,
            "source": "previous live state",
        }

    # Reload is a global substrate change; apply it to the current session
    # (stdio for the usual authoring path). Other live sessions re-project
    # from the new substrate on their next call (the projection is re-read
    # each time, never cached).
    reload_session = _session()
    reload_session.engagement_bundle = None
    _refresh_engagement_projection(force=True)
    if (
        reload_session.active_practice is not None
        and reload_session.active_practice.id not in BUNDLES
    ):
        _close_active_practice_enactment()

    return {
        "reloaded": True,
        "source": "substrate/ files",
        "bundles": sorted(_AUTHORING_BUNDLES),
        "materials": len(substrate.materials),
        "affordances": len(substrate.affordances),
        "errors": loaded_sub.errors,
    }


def _parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _mark_activity(value: str | None = None) -> None:
    _session().last_step_at = _parse_dt(value) if value is not None else _now_dt()


def _close_active_practice_enactment() -> None:
    s = _session()
    if s.active_practice_enactment_id is not None:
        _trail.close_enactment(s.active_practice_enactment_id)
    s.active_practice = None
    s.active_practice_enactment_id = None


def _maybe_close_idle_engagement_segment() -> None:
    """Close a complete engagement segment after a noticeable idle gap."""
    if _MODE != "somatic" or _ENGAGEMENT_IDLE_CLOSE_SECONDS <= 0:
        return
    s = _session()
    if s.last_step_at is None:
        return
    idle_for = _now_dt() - s.last_step_at
    if idle_for < timedelta(seconds=_ENGAGEMENT_IDLE_CLOSE_SECONDS):
        return
    _close_active_practice_enactment()
    if s.engagement_enactment_id is not None:
        _trail.close_enactment(s.engagement_enactment_id)
    s.engagement_enactment_id = None
    s.last_step_at = None
    _refresh_engagement_projection(force=True)


def _refresh_engagement_projection(*, force: bool = False) -> None:
    """Keep the current session's projections in sync with the live substrate.

    Projections are intentionally frozen snapshots, but the substrate is
    mutable at runtime. Re-project on each read/invoke boundary so Practice
    Management changes to affordances, materials, pool elements, or bundle
    selections become visible without restarting the MCP server.
    """
    if _MODE != "somatic":
        return
    s = _session()
    bundle = _AUTHORING_BUNDLES[ENGAGEMENT_BUNDLE.id]
    s.engagement = project(bundle, substrate, FUNCTIONS)
    s.engagement_bundle = bundle
    s.engagement_affordance_ids = frozenset(a.id for a in s.engagement.affordances)
    if s.engagement_enactment_id is None:
        # The engagement layer is somatic-only (this runs under _MODE=='somatic').
        s.engagement_enactment_id = _trail.open_enactment(
            s.engagement.id, mode="somatic"
        )
        _mark_activity()
    if s.active_practice is not None and s.active_practice.id in BUNDLES:
        s.active_practice = project(
            BUNDLES[s.active_practice.id],
            substrate,
            FUNCTIONS,
            engagement=s.engagement,
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
def switch_practice(practice_id: str, ctx: Context) -> dict[str, Any]:
    """Project the named bundle (with the engagement merged in) and activate it.

    Closes the current practice enactment (if any) and opens a new one whose
    parent_enactment_id points at the engagement enactment, so the trail
    records the layering.
    """
    s = _bind_session(ctx)
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
    if s.active_practice_enactment_id is not None:
        _trail.close_enactment(s.active_practice_enactment_id)
    s.active_practice = project(
        bundle, substrate, FUNCTIONS, engagement=s.engagement
    )
    # bundle.mode == _MODE here (validated above); it decides which loop later
    # routes this enactment to the Judge — reactive (somatic) or reflective
    # (autonomic).
    s.active_practice_enactment_id = _trail.open_enactment(
        s.active_practice.id,
        parent_enactment_id=s.engagement_enactment_id,
        mode=bundle.mode,
    )
    _mark_activity()
    return {
        "active": s.active_practice.id,
        "name": s.active_practice.name,
        "mode": _MODE,
        "engagement_enactment_id": s.engagement_enactment_id,
        "practice_enactment_id": s.active_practice_enactment_id,
    }


@mcp_app.tool()
def current_practice(ctx: Context) -> dict[str, Any]:
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
    engagement layer is always available via the separate `continuous_self`
    tool; the composition returned here is the active practice's full
    projection (engagement content merged in).
    """
    s = _bind_session(ctx)
    _refresh_engagement_projection()
    if s.active_practice is None:
        return {
            "mode": _MODE,
            "practice": None,
            "enactment_id": None,
            "composition": None,
        }
    p = s.active_practice
    return {
        "mode": _MODE,
        "practice": {
            "id": p.id,
            "name": p.name,
            "description": p.description,
        },
        "enactment_id": s.active_practice_enactment_id,
        "composition": compose_composition(p),
    }


# continuous_self is a somatic-only tool — registered only when the server is
# in somatic mode (and thus has a projected engagement). Autonomic mode does
# not expose it, so the autonomic surface stays at five tools while the
# somatic surface is six. The asymmetry is honest: engagement is a somatic
# concept; the autonomic loop has no user to be engaged with.
if _MODE == "somatic":

    @mcp_app.tool()
    def continuous_self(ctx: Context) -> dict[str, Any]:
        """Return the engagement layer's content (somatic only).

        Renders the engagement bundle — its teleo-affective, understanding,
        rules, and affordances — as a markdown composition, without the
        active practice merged in. Always available regardless of whether
        a practice is currently engaged. Use to read the apprenticeship as
        a first-class thing before deciding which practice to engage.

        Distinct from `current_practice`, which returns the active practice
        with engagement merged in.
        """
        s = _bind_session(ctx)
        _refresh_engagement_projection()
        assert s.engagement is not None  # somatic mode implies projection
        e = s.engagement
        return {
            "id": e.id,
            "name": e.name,
            "description": e.description,
            "composition": compose_composition(e),
        }

    # MCP Apps surface (somatic-only, human-facing). One fixed tool dispatches to
    # the visualization registry; its static `_meta.ui.resourceUri` binds the
    # generic shell resource, which the host renders in a sandboxed iframe and
    # into which the tool result is pushed. Adding a visualization is a registry
    # entry — no new tool. See `visualizations`.
    from practice_theory_implementation import visualizations as _viz

    @mcp_app.resource(
        _viz.VIZ_RESOURCE_URI,
        mime_type=_viz.VIZ_MIME_TYPE,
        meta={"ui": {"prefersBorder": True}},
    )
    def viz_shell() -> str:
        """Generic MCP Apps shell that hosts a named visualization (somatic only)."""
        return _viz.render_viz_shell_html()

    @mcp_app.tool(meta={"ui": {"resourceUri": _viz.VIZ_RESOURCE_URI}})
    def show_visualization(
        name: str = "status", args: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Render a named visualization as an interactive MCP App.

        `name` selects from the visualization registry (`status` is the autonomic
        loop dashboard); `args` is passed to that visualization. Returns
        `{name, html}`; the host renders the shell and pushes this result into it.
        The same registry also backs the `render_status_dashboard` affordance and
        the standalone :7182 dashboard server, so all three share one source.
        """
        return _viz.render_visualization(name, args)


@mcp_app.tool()
def discover_affordances(
    ctx: Context, query: str | None = None
) -> list[dict[str, Any]]:
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
    s = _bind_session(ctx)
    _refresh_engagement_projection()
    active = s.active_practice or s.engagement
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
                    "engagement" if aff.id in s.engagement_affordance_ids else "practice"
                ),
            }
        )
    return out


@mcp_app.tool()
def invoke_affordance(
    affordance_id: str,
    material_name: str,
    ctx: Context,
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
    s = _bind_session(ctx)
    _maybe_close_idle_engagement_segment()
    _refresh_engagement_projection()
    is_engagement_call = affordance_id in s.engagement_affordance_ids
    active = s.active_practice or s.engagement
    if active is None:
        return {"error": "no active practice; call switch_practice first"}
    if not is_engagement_call and s.active_practice is None:
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
        s.engagement_enactment_id if is_engagement_call else s.active_practice_enactment_id
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

    Static resources get no Context (see `_resource_session`), so this is a
    best-effort read of the sole active session — authoritative per-session
    reads go through the `current_practice` tool. In somatic mode the
    engagement stands in until a practice is switched into; in autonomic mode
    there is no engagement, so resources resolve only when a practice is active.
    """
    s = _resource_session()
    return s.active_practice or s.engagement


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
    """Close still-open enactments (every session) so the dispatcher routes a
    complete trail."""
    for s in list(_sessions.values()):
        if s.active_practice_enactment_id is not None:
            _trail.close_enactment(s.active_practice_enactment_id)
            s.active_practice_enactment_id = None
        if s.engagement_enactment_id is not None:
            _trail.close_enactment(s.engagement_enactment_id)
            s.engagement_enactment_id = None


async def _reap_idle_sessions(stop: Any) -> None:
    """Periodically close + drop HTTP sessions idle beyond the reap threshold.

    Streamable HTTP gives no per-session close callback, so this sweep closes
    orphaned sessions' enactments (so the dispatcher can route them) and frees
    their state. The stdio session is never reaped — it lives for the process.
    """
    import asyncio as _asyncio
    import contextlib as _contextlib

    interval = min(30.0, float(_SESSION_REAP_SECONDS))
    while not stop.is_set():
        with _contextlib.suppress(TimeoutError):
            await _asyncio.wait_for(stop.wait(), timeout=interval)
        if stop.is_set():
            break
        cutoff = _now_dt() - timedelta(seconds=_SESSION_REAP_SECONDS)
        for key, s in list(_sessions.items()):
            if key == _STDIO_SESSION_KEY or s.last_step_at is None:
                continue
            if s.last_step_at > cutoff:
                continue
            if s.active_practice_enactment_id is not None:
                _trail.close_enactment(s.active_practice_enactment_id)
            if s.engagement_enactment_id is not None:
                _trail.close_enactment(s.engagement_enactment_id)
            _sessions.pop(key, None)
            _log.info("reaped idle MCP session %s", key)


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
    reaper: _asyncio.Task[None] | None = None
    if _TRANSPORT == "http" and _SESSION_REAP_SECONDS > 0:
        reaper = _asyncio.create_task(_reap_idle_sessions(stop))
    try:
        if _TRANSPORT == "http":
            await mcp_app.run_streamable_http_async()
        else:
            await mcp_app.run_stdio_async()
    finally:
        await _shutdown_handler()
        stop.set()
        for task in (dispatcher, reaper):
            if task is not None:
                await task


if __name__ == "__main__":
    import asyncio as _asyncio

    _asyncio.run(_serve_with_dispatcher())
