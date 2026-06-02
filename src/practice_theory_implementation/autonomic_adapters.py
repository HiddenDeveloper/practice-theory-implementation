"""Autonomic adapters — abstractions over the LLM-driving primitive.

One run-loop (`run_role_loop`) works against any adapter that implements the
`AutonomicAdapter` ABC. Four concrete adapters are provided — three drive a
real LLM (Anthropic SDK, Claude CLI, Codex exec) and one is a deterministic
stand-in (`ScriptedAdapter`) used by the verify:

- `ScriptedAdapter` — deterministic, no LLM. Used by the verify so the loop
  is demonstrable without API keys or external tooling. Takes a per-role
  scripted callable that receives the WorkItem and decides what to do; the
  callable opens an MCP session, drives the autonomic surface, and returns.

- `AnthropicSDKAdapter` — uses `claude-agent-sdk`. Opens a long-lived
  `ClaudeSDKClient` per role; conversation and cached system prompt persist
  across work items. Dispatches by sending a query naming the inbox row.
  Requires `claude-agent-sdk` to be installed and Claude credentials
  available (subscription or API key). Note: Anthropic's subscription terms
  for SDK use are scheduled to change on 2026-06-15.

- `ClaudeCliAdapter` — invokes `claude -p` (Claude Code's print mode) as a
  subprocess per work item. Same provider as the SDK adapter but no Python
  dependency. Stateless across dispatches. Requires the `claude` binary on
  PATH; configurable via `PRACTICE_CLAUDE_BIN`.

- `CodexExecAdapter` — invokes `codex exec` as a subprocess per work item.
  Stateless across dispatches. The autonomic MCP server is injected inline
  via `codex exec -c mcp_servers.…`, so the adapter does not depend on the
  user's `~/.codex/config.toml` or a `.mcp.json` in cwd. Requires the Codex
  CLI binary; configurable via `PRACTICE_CODEX_BIN`.

The brief (system prompt) for each role is composed from the role's bundle
content — teleo-affective + understanding + rules — by `compose_brief`.
Bundle content lives in the substrate; the adapter receives the composed
string at startup.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import os
import subprocess
import tomllib
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from practice_theory_implementation.projection import compose_composition, project
from practice_theory_implementation.trail import EnactmentStore
from practice_theory_implementation.types import Bundle, Substrate

logger = logging.getLogger(__name__)

_PRACTICE_SERVICE_ENV_KEYS = (
    "PRACTICE_NEO4J_HTTP_URL",
    "PRACTICE_NEO4J_AUTH",
    "PRACTICE_NEO4J_USER",
    "PRACTICE_NEO4J_PASSWORD",
    "NEO4J_AUTH",
    "NEO4J_USER",
    "NEO4J_PASSWORD",
    "PRACTICE_QDRANT_URL",
    "PRACTICE_EMBED_URL",
    "PRACTICE_EPISODIC_COLLECTION",
)


# ---------------------------------------------------------------------------
# Common types
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class WorkItem:
    """One unit of dispatched work, role-agnostic shape."""

    primary_id: object             # enactment_id (Judge) or friction_id (Smoother)
    role: str                      # "judge" | "smoother"
    dispatch_message: str          # the text the LLM sees when work arrives
    metadata: dict[str, Any] | None = None  # role-specific extras (e.g. bundle_id)


@dataclass(frozen=True, slots=True)
class AdapterConfig:
    """Per-role adapter configuration."""

    role: str                      # "judge" | "smoother"
    bundle_id: str                 # which bundle in the catalog this role enacts
    brief: str                     # the system prompt (composed from bundle content)
    mcp_url: str | None = None     # for HTTP MCP transport; None for stdio


# ---------------------------------------------------------------------------
# Brief composition
# ---------------------------------------------------------------------------


def compose_brief(bundle: Bundle, substrate: Substrate) -> str:
    """Compose a system-prompt brief from a bundle's content.

    Projects the bundle (without engagement merge — autonomic bundles have
    no engagement) and delegates to `compose_composition` to render. The
    LLM enacting the role reads this as its system prompt.
    """
    from practice_theory_implementation.registry import FUNCTIONS

    return compose_composition(project(bundle, substrate, FUNCTIONS))


def _local_mcp_env(cwd: Path) -> dict[str, str]:
    """Read local MCP env values from .codex/config.toml when present.

    Local secrets stay in the ignored `.codex/config.toml`; the adapters use
    them to launch autonomic MCP subprocesses with the same service access as
    the somatic server. Values already present in `os.environ` still win.
    """
    config_path = cwd / ".codex" / "config.toml"
    if not config_path.is_file():
        return {}
    try:
        config = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        logger.warning("could not read local MCP env from %s: %s", config_path, exc)
        return {}
    servers = config.get("mcp_servers")
    if not isinstance(servers, dict):
        return {}
    merged: dict[str, str] = {}
    # Prefer an explicit autonomic config if one exists, then fall back to the
    # somatic server's service credentials because both surfaces read the same
    # local Neo4j/Qdrant stores.
    for server_name in ("practice_server_somatic", "practice_server_autonomic"):
        server = servers.get(server_name)
        if not isinstance(server, dict):
            continue
        env = server.get("env")
        if not isinstance(env, dict):
            continue
        for key, value in env.items():
            if key in _PRACTICE_SERVICE_ENV_KEYS and value is not None:
                merged[key] = str(value)
    return merged


def practice_service_env(cwd: Path | None = None) -> dict[str, str]:
    """Return service env from the shell plus local MCP config fallback."""
    root = cwd or Path.cwd()
    local = _local_mcp_env(root)
    out = {
        key: value
        for key, value in local.items()
        if key in _PRACTICE_SERVICE_ENV_KEYS
    }
    for key in _PRACTICE_SERVICE_ENV_KEYS:
        if os.environ.get(key):
            out[key] = os.environ[key]
    return out


def _server_env(
    *,
    mode: str,
    cwd: Path,
    disable_dispatcher: bool,
    include_service_env: bool,
) -> dict[str, str]:
    env = {
        "PRACTICE_SERVER_MODE": mode,
        "PRACTICE_TRANSPORT": "stdio",
    }
    if disable_dispatcher:
        env["PRACTICE_DISABLE_DISPATCHER"] = "1"
    if include_service_env:
        env.update(practice_service_env(cwd))
    return env


def _subprocess_env(cwd: Path) -> dict[str, str]:
    env = dict(os.environ)
    env.update(practice_service_env(cwd))
    return env


# ---------------------------------------------------------------------------
# AutonomicAdapter ABC
# ---------------------------------------------------------------------------


class AutonomicAdapter(ABC):
    """Drives an LLM to enact one autonomic practice per dispatch.

    Lifecycle: `open()` once, `dispatch(work)` per work item, `close()` once.
    The shared run-loop calls these in order; subclasses choose what each
    means for their LLM primitive.
    """

    def __init__(self, config: AdapterConfig) -> None:
        self.config = config

    @abstractmethod
    async def open(self) -> None:
        """Set up the LLM primitive. May be a no-op for stateless adapters."""

    @abstractmethod
    async def dispatch(self, work: WorkItem) -> str | None:
        """Enact one work item. Return the consumer enactment id if known,
        or None if the adapter cannot determine it (the run-loop will fall
        back to a most-recent-in-progress query on the trail)."""

    @abstractmethod
    async def close(self) -> None:
        """Tear down the LLM primitive."""


# ---------------------------------------------------------------------------
# ScriptedAdapter — deterministic, no LLM
# ---------------------------------------------------------------------------


ScriptedHandler = Callable[[WorkItem], Awaitable[str | None]]


class ScriptedAdapter(AutonomicAdapter):
    """Adapter for the verify and tests — no LLM, no API calls.

    Takes an async callable. The callable receives the WorkItem and is
    expected to open its own MCP session, drive the autonomic surface
    (switch to the role's bundle, invoke affordances, etc.), and return
    the consumer enactment id. The handler stands in for what an LLM
    enactment would do — deterministically.
    """

    def __init__(self, config: AdapterConfig, handler: ScriptedHandler) -> None:
        super().__init__(config)
        self._handler = handler

    async def open(self) -> None:
        return

    async def dispatch(self, work: WorkItem) -> str | None:
        return await self._handler(work)

    async def close(self) -> None:
        return


# ---------------------------------------------------------------------------
# AnthropicSDKAdapter — claude-agent-sdk
# ---------------------------------------------------------------------------


class AnthropicSDKAdapter(AutonomicAdapter):
    """Drives Claude via `claude-agent-sdk`.

    One long-lived `ClaudeSDKClient` per adapter instance — conversation
    and cached system prompt persist across work items. Each `dispatch`
    sends a single query naming the dispatched work and drains the
    response stream.

    Requires `claude-agent-sdk` installed. Requires Claude credentials —
    either an Anthropic API key (`ANTHROPIC_API_KEY`) or a logged-in
    Claude Code / Claude Pro / Max subscription. The subscription path is
    scheduled to change on 2026-06-15; check current Anthropic policy.

    `mcp_url` on AdapterConfig is optional. Unset (the default), the adapter
    uses stdio — each adapter instance spawns its own server subprocess.
    Set, the adapter connects to a long-lived HTTP MCP server. The server's
    HTTP path is experimental and requires PRACTICE_EXPERIMENTAL_HTTP=1 until
    per-session lifespan state lands.
    """

    def __init__(
        self,
        config: AdapterConfig,
        *,
        model: str = "claude-sonnet-4-6",
        cwd: Path | None = None,
        max_turns: int | None = 60,
    ) -> None:
        super().__init__(config)
        # mcp_url is optional. If set, the adapter uses HTTP transport. If
        # not, the adapter uses stdio — each adapter instance spawns its
        # own server subprocess via `python -m
        # practice_theory_implementation.server`. Stdio is the safer default
        # under concurrent Judge+Smoother loops because each role gets its
        # own server process with its own module-level state. HTTP requires
        # per-session state in the server (not yet implemented); under HTTP
        # with module-level state, concurrent sessions race on
        # `_active_practice`.
        self._model = model
        self._cwd = cwd or Path.cwd()
        self._max_turns = max_turns
        self._client: Any = None

    async def open(self) -> None:
        import sys as _sys

        # claude_agent_sdk ships only with the optional `anthropic` extra, so it
        # may be absent (e.g. Codex-only installs); the type checker is told the
        # import is allowed to be missing.
        from claude_agent_sdk import (  # pyright: ignore[reportMissingImports]
            ClaudeAgentOptions,
            ClaudeSDKClient,
        )

        mcp_label = "practice_server_autonomic"
        allowed_tools = [
            f"mcp__{mcp_label}__list_practices",
            f"mcp__{mcp_label}__switch_practice",
            f"mcp__{mcp_label}__current_practice",
            f"mcp__{mcp_label}__discover_affordances",
            f"mcp__{mcp_label}__invoke_affordance",
        ]
        if self.config.mcp_url:
            server_cfg: dict[str, Any] = {"type": "http", "url": self.config.mcp_url}
        else:
            server_cfg = {
                "type": "stdio",
                "command": _sys.executable,
                "args": ["-m", "practice_theory_implementation.server"],
                "env": _server_env(
                    mode="autonomic",
                    cwd=self._cwd,
                    disable_dispatcher=True,
                    include_service_env=True,
                ),
            }
        options = ClaudeAgentOptions(
            system_prompt=self.config.brief,
            model=self._model,
            cwd=self._cwd,
            setting_sources=[],
            strict_mcp_config=True,
            skills=[],
            mcp_servers=cast(Any, {mcp_label: server_cfg}),
            allowed_tools=allowed_tools,
            permission_mode="bypassPermissions",
            max_turns=self._max_turns,
        )
        self._client = ClaudeSDKClient(options=options)
        await self._client.__aenter__()
        await self._client.query("Begin.")
        await self._drain()

    async def dispatch(self, work: WorkItem) -> str | None:
        if self._client is None:
            raise RuntimeError("AnthropicSDKAdapter.open() not called")
        await self._client.query(work.dispatch_message)
        await self._drain()
        # Consumer id discovered by the run-loop via the trail.
        return None

    async def close(self) -> None:
        if self._client is not None:
            await self._client.__aexit__(None, None, None)
            self._client = None

    async def _drain(self) -> None:
        if self._client is None:
            return
        # Optional `anthropic` extra; see open() — import allowed to be missing.
        from claude_agent_sdk import (  # pyright: ignore[reportMissingImports]
            AssistantMessage,
            ResultMessage,
        )

        async for msg in self._client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    text = getattr(block, "text", None)
                    if text:
                        logger.info("[%s] %s", self.config.role, text.strip())
            elif isinstance(msg, ResultMessage):
                logger.info(
                    "[%s] turn done: in=%s out=%s",
                    self.config.role,
                    (msg.usage or {}).get("input_tokens"),
                    (msg.usage or {}).get("output_tokens"),
                )


# ---------------------------------------------------------------------------
# ClaudeCliAdapter — claude -p subprocess
# ---------------------------------------------------------------------------


CLAUDE_BIN_ENV = "PRACTICE_CLAUDE_BIN"
DEFAULT_CLAUDE_BIN = "claude"


class ClaudeCliAdapter(AutonomicAdapter):
    """Drives Claude via `claude -p` (Claude Code's print mode), subprocess
    per work item.

    The CLI counterpart to AnthropicSDKAdapter — same provider, different
    process shape. Stateless across dispatches (each call spawns a fresh
    `claude` process), no Python SDK dependency, and parallels
    `CodexExecAdapter` so both providers have a subprocess-per-dispatch
    option as well as (for Anthropic) a long-lived in-process option.

    MCP config is passed via `--mcp-config` as JSON; the spawned `claude`
    process reads it and starts the practice server itself (stdio) or
    connects to a long-lived one (HTTP) depending on the config shape.

    Authentication uses whatever `claude` itself has — Claude subscription
    OAuth (the default), or `ANTHROPIC_API_KEY` if set. Note that the
    `--bare` flag would minimise context but explicitly disables OAuth and
    keychain, requiring `ANTHROPIC_API_KEY` only — so this adapter does
    *not* pass `--bare`, to stay compatible with the subscription path.

    Requires the `claude` CLI installed (configurable via PRACTICE_CLAUDE_BIN).
    """

    def __init__(
        self,
        config: AdapterConfig,
        *,
        cwd: Path | None = None,
        model: str | None = None,
        max_budget_usd: float | None = None,
        effort: str | None = None,
        permission_mode: str | None = "bypassPermissions",
    ) -> None:
        super().__init__(config)
        self._cwd = cwd or Path.cwd()
        self._claude_bin = os.environ.get(CLAUDE_BIN_ENV, DEFAULT_CLAUDE_BIN)
        self._model = model
        self._max_budget_usd = max_budget_usd
        self._effort = effort
        # Default preserves the runner's behavior. Pass None to drop
        # --permission-mode entirely and confine the practitioner to exactly
        # the MCP tools in --allowedTools — the hardened path the RemSleep
        # preview and the eval harness use (no shell, no file writes).
        self._permission_mode = permission_mode

    async def open(self) -> None:
        return

    async def dispatch(self, work: WorkItem) -> str | None:
        import json as _json
        import sys as _sys

        mcp_label = "practice_server_autonomic"
        if self.config.mcp_url:
            server_cfg: dict[str, Any] = {"type": "http", "url": self.config.mcp_url}
        else:
            server_cfg = {
                "type": "stdio",
                "command": _sys.executable,
                "args": ["-m", "practice_theory_implementation.server"],
                # Do not put local service secrets into the command-line JSON.
                # The claude subprocess gets them through its process env, and
                # the MCP server it spawns inherits them.
                "env": _server_env(
                    mode="autonomic",
                    cwd=self._cwd,
                    disable_dispatcher=True,
                    include_service_env=False,
                ),
            }
        mcp_config_json = _json.dumps({"mcpServers": {mcp_label: server_cfg}})

        allowed_tools = " ".join(
            f"mcp__{mcp_label}__{name}"
            for name in (
                "list_practices",
                "switch_practice",
                "current_practice",
                "discover_affordances",
                "invoke_affordance",
            )
        )

        prompt = work.dispatch_message
        cmd: list[str] = [
            self._claude_bin,
            "-p",
            "--system-prompt",
            self.config.brief,
            "--mcp-config",
            mcp_config_json,
            "--allowedTools",
            allowed_tools,
            "--output-format",
            "text",
        ]
        if self._permission_mode:
            cmd.extend(["--permission-mode", self._permission_mode])
        if self._model:
            cmd.extend(["--model", self._model])
        if self._max_budget_usd is not None:
            cmd.extend(["--max-budget-usd", str(self._max_budget_usd)])
        if self._effort:
            cmd.extend(["--effort", self._effort])
        cmd.append(prompt)

        def _run() -> subprocess.CompletedProcess[str]:
            return subprocess.run(  # noqa: S603 - claude_bin is operator config
                cmd,
                cwd=self._cwd,
                env=_subprocess_env(self._cwd),
                text=True,
                capture_output=True,
                check=False,
            )

        result = await asyncio.to_thread(_run)
        if result.returncode != 0:
            logger.warning(
                "[%s] claude -p exited %d: %s",
                self.config.role,
                result.returncode,
                result.stderr.strip()[:500],
            )
        else:
            tail = result.stdout.strip().splitlines()[-3:]
            logger.info(
                "[%s] claude -p completed; last lines: %s",
                self.config.role,
                " | ".join(tail),
            )
        return None

    async def close(self) -> None:
        return


# ---------------------------------------------------------------------------
# CodexExecAdapter — codex exec subprocess
# ---------------------------------------------------------------------------


CODEX_BIN_ENV = "PRACTICE_CODEX_BIN"
DEFAULT_CODEX_BIN = "codex"


class CodexExecAdapter(AutonomicAdapter):
    """Drives Codex via `codex exec` subprocess per work item.

    Stateless across dispatches. Each dispatch spawns a fresh `codex exec`
    with the brief as part of the prompt and the work's dispatch_message
    appended. The autonomic MCP server is injected inline via
    `codex exec -c mcp_servers.practice_server_autonomic.…`, so the
    subprocess does not depend on the user's `~/.codex/config.toml` or a
    `.mcp.json` in cwd.

    `mcp_url` on AdapterConfig is unused — Codex always uses the inline
    stdio MCP config the adapter injects.
    """

    def __init__(
        self,
        config: AdapterConfig,
        *,
        cwd: Path | None = None,
        model: str | None = None,
        reasoning_effort: str | None = None,
    ) -> None:
        super().__init__(config)
        self._cwd = cwd or Path.cwd()
        self._codex_bin = os.environ.get(CODEX_BIN_ENV, DEFAULT_CODEX_BIN)
        self._model = model
        self._reasoning_effort = reasoning_effort

    async def open(self) -> None:
        return

    async def dispatch(self, work: WorkItem) -> str | None:
        import sys as _sys

        prompt = f"{self.config.brief}\n\n## Dispatched work\n\n{work.dispatch_message}"
        cmd: list[str] = [
            self._codex_bin,
            "exec",
            "--cd",
            str(self._cwd),
            "--sandbox",
            "danger-full-access",
            "--dangerously-bypass-approvals-and-sandbox",
        ]
        # Inject our autonomic MCP server inline so we don't depend on the
        # user's ~/.codex/config.toml. Also disable any of the user's
        # pre-configured MCP servers that we know fail to connect during
        # autonomic runs — Codex aborts the whole exec on the first MCP
        # connection failure, even servers our prompt won't touch.
        py_quoted = _sys.executable.replace('"', '\\"')
        cmd.extend(
            [
                "-c",
                f'mcp_servers.practice_server_autonomic.command="{py_quoted}"',
                "-c",
                'mcp_servers.practice_server_autonomic.args=['
                '"-m","practice_theory_implementation.server"]',
                "-c",
                'mcp_servers.practice_server_autonomic.env={'
                'PRACTICE_SERVER_MODE="autonomic",'
                'PRACTICE_TRANSPORT="stdio",'
                'PRACTICE_DISABLE_DISPATCHER="1"}',
            ]
        )
        for disabled in os.environ.get(
            "PRACTICE_CODEX_DISABLE_MCP", "cognabot,laputa"
        ).split(","):
            disabled = disabled.strip()
            if disabled:
                cmd.extend(["-c", f"mcp_servers.{disabled}.enabled=false"])
        if self._model:
            cmd.extend(["--model", self._model])
        if self._reasoning_effort:
            cmd.extend(["-c", f'model_reasoning_effort="{self._reasoning_effort}"'])
        cmd.append(prompt)

        def _run() -> subprocess.CompletedProcess[str]:
            return subprocess.run(  # noqa: S603 - codex_bin is operator config
                cmd,
                cwd=self._cwd,
                env=_subprocess_env(self._cwd),
                text=True,
                capture_output=True,
                check=False,
            )

        result = await asyncio.to_thread(_run)
        if result.returncode != 0:
            logger.warning(
                "[%s] codex exec exited %d: %s",
                self.config.role,
                result.returncode,
                result.stderr.strip()[:500],
            )
        else:
            logger.info("[%s] codex exec completed", self.config.role)
        return None

    async def close(self) -> None:
        return


# ---------------------------------------------------------------------------
# Shared run-loop
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class RolePolicy:
    """How to find next work for a role and how to consume it."""

    role: str

    def next_work(self, store: EnactmentStore, *, worker_id: str) -> WorkItem | None:
        if self.role == "judge":
            row = store.next_judge_work(worker_id=worker_id)
            if row is None:
                return None
            return WorkItem(
                primary_id=row.enactment_id,
                role="judge",
                dispatch_message=(
                    f"Examine enactment `{row.enactment_id}` "
                    f"(bundle `{row.bundle_id}`, closed at `{row.closed_at}`). "
                    f"Use read_enactment_steps to see what it did and read_bundle "
                    f"to see what was available, then enact the Judge practice "
                    f"over it: emit_friction for what you find. Examine only this "
                    f"one enactment in this turn, then stop."
                ),
                metadata={
                    "enactment_id": row.enactment_id,
                    "bundle_id": row.bundle_id,
                    "closed_at": row.closed_at,
                },
            )
        if self.role == "smoother":
            row = store.next_smoother_work(worker_id=worker_id)
            if row is None:
                return None
            return WorkItem(
                primary_id=row.friction_id,
                role="smoother",
                dispatch_message=(
                    f"Address Friction `{row.friction_id}` (kind=`{row.kind}`, "
                    f"target enactment `{row.target_enactment_id}`). "
                    f"Use read_pending_friction to find it and read the bundle it "
                    f"names if you need context, then enact the Smoother practice: "
                    f"apply the amendment with the appropriate amend_* affordance "
                    f"and mark_friction_addressed when done. Address only this one "
                    f"Friction in this turn, then stop."
                ),
                metadata={
                    "friction_id": row.friction_id,
                    "target_enactment_id": row.target_enactment_id,
                    "kind": row.kind,
                },
            )
        raise ValueError(f"unknown role {self.role!r}")

    def mark_consumed(
        self,
        store: EnactmentStore,
        primary_id: object,
        consumer_enactment_id: str,
    ) -> None:
        if self.role == "judge":
            store.consume_judge_inbox(
                str(primary_id), consumer_enactment_id=consumer_enactment_id
            )
        elif self.role == "smoother":
            if not isinstance(primary_id, int):
                raise TypeError("smoother inbox primary_id must be an integer")
            store.consume_smoother_inbox(
                primary_id, consumer_enactment_id=consumer_enactment_id
            )


async def drain(
    adapter: AutonomicAdapter,
    policy: RolePolicy,
    store: EnactmentStore,
    *,
    worker_id: str,
    max_items: int = 20,
) -> int:
    """Process up to `max_items` from the inbox, then stop. For the verify/tests.

    Returns the number of items processed. Unlike `run_role_loop`, this does
    not idle-poll — it exits as soon as the inbox is empty.
    """
    await adapter.open()
    processed = 0
    try:
        for _ in range(max_items):
            work = policy.next_work(store, worker_id=worker_id)
            if work is None:
                break
            try:
                consumer_id = await adapter.dispatch(work)
            except Exception:
                logger.exception(
                    "[%s] dispatch failed for %s", adapter.config.role, work.primary_id
                )
                continue
            if consumer_id:
                policy.mark_consumed(store, work.primary_id, consumer_id)
            processed += 1
    finally:
        await adapter.close()
    return processed


def _resolve_consumer_id(
    store: EnactmentStore, bundle_id: str, dispatch_started: str
) -> str | None:
    """Find the consumer enactment id when the adapter cannot tell us.

    Single-tenant heuristic: the most recent enactment of the role's bundle
    opened after the dispatch started is the one the LLM just enacted.
    Works under stdio-MCP-per-adapter (no cross-role races) and HTTP with
    per-session state. Under HTTP with module-level state and concurrent
    roles, this can mis-resolve — but per-session state is the fix, not
    consumer_id resolution.
    """
    for row in store.recent_enactments(limit=20):
        if row.practice_id == bundle_id and row.opened_at >= dispatch_started:
            return row.id
    return None


async def run_role_loop(
    adapter: AutonomicAdapter,
    policy: RolePolicy,
    store: EnactmentStore,
    *,
    stop: asyncio.Event,
    worker_id: str,
    idle_seconds: float = 5.0,
    on_consume: Callable[[object], str | None] | None = None,
) -> None:
    """Generic run-loop: poll inbox, dispatch, mark consumed, repeat.

    `on_consume(primary_id)` is an optional fallback for resolving the
    consumer enactment id when the adapter cannot. If unset, falls back to
    a trail query (`_resolve_consumer_id`) — the SDK adapters return None
    from dispatch, so the fallback is what marks their work consumed.
    """
    from datetime import UTC as _UTC
    from datetime import datetime as _datetime

    await adapter.open()
    try:
        while not stop.is_set():
            work = policy.next_work(store, worker_id=worker_id)
            if work is None:
                with contextlib.suppress(TimeoutError):
                    await asyncio.wait_for(stop.wait(), timeout=idle_seconds)
                continue
            logger.info("[%s] dispatching %s", adapter.config.role, work.primary_id)
            dispatch_started = _datetime.now(_UTC).isoformat(timespec="microseconds")
            try:
                consumer_id = await adapter.dispatch(work)
            except Exception:
                logger.exception(
                    "[%s] dispatch failed for %s", adapter.config.role, work.primary_id
                )
                continue
            if consumer_id is None and on_consume is not None:
                consumer_id = on_consume(work.primary_id)
            if consumer_id is None:
                consumer_id = _resolve_consumer_id(
                    store, adapter.config.bundle_id, dispatch_started
                )
            if consumer_id:
                policy.mark_consumed(store, work.primary_id, consumer_id)
            else:
                logger.warning(
                    "[%s] no consumer id for %s; left for next claim",
                    adapter.config.role,
                    work.primary_id,
                )
    finally:
        await adapter.close()
