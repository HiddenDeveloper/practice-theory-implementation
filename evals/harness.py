"""Eval harness: stage a fixture, run a practitioner, grade the trail.

One temp workspace isolates everything: the trail lives at
`<tmp>/data/trail.db`, reached three consistent ways — our own `EnactmentStore`
opens it by path, the stdio MCP server inherits `PRACTICE_TRAIL_PATH`, and a
`codex exec` subprocess resolves the same file via `cwd=<tmp>` (the trail path is
cwd-relative and the substrate is package-absolute). Substrate is the real repo
substrate in every case.

Two practitioner drivers:
  - `drive_judge_scripted` — no LLM. Walks the real Judge read affordances over
    the MCP server, applies a deterministic detector, and emits friction through
    the server's own affordance. This validates the harness mechanics and the
    seed/route/grade path end to end without spending a model call. The detector
    is test scaffolding, not situated cognition — it stands in for the Judge only
    so the plumbing can be checked.
  - `drive_live` — the real thing: hands the work to a provider adapter
    (codex/claude), which connects its own server instance and judges for itself.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import os
import shutil
import sys
import tempfile
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from evals.cases import Case
from practice_theory_implementation.autonomic_adapters import (
    AdapterConfig,
    AutonomicAdapter,
    ClaudeCliAdapter,
    CodexExecAdapter,
    RolePolicy,
    compose_brief,
    drain,
)
from practice_theory_implementation.autonomic_dispatcher import route_now
from practice_theory_implementation.bundles import BUNDLES
from practice_theory_implementation.pools import substrate
from practice_theory_implementation.trail import TRAIL_PATH_ENV, EnactmentStore

# Affordances whose output proposes a judgement the practitioner must weigh.
# Kept here (not in the substrate) because this is the eval's stand-in detector.
RANKING_AFFORDANCES = {"recall_relevant_episodes"}
EVALUATION_AFFORDANCES: set[str] = set()  # none modelled yet; a select/compare step would land here


@contextlib.contextmanager
def temp_workspace() -> Iterator[tuple[EnactmentStore, Path]]:
    """Yield an isolated (store, cwd). Trail at <tmp>/data/trail.db, reachable by
    path, by inherited PRACTICE_TRAIL_PATH, and by cwd-relative resolution."""
    tmp = Path(tempfile.mkdtemp(prefix="practice-eval-"))
    (tmp / "data").mkdir(parents=True, exist_ok=True)
    trail_path = tmp / "data" / "trail.db"
    prior = os.environ.get(TRAIL_PATH_ENV)
    os.environ[TRAIL_PATH_ENV] = str(trail_path)
    try:
        yield EnactmentStore(trail_path), tmp
    finally:
        if prior is None:
            os.environ.pop(TRAIL_PATH_ENV, None)
        else:
            os.environ[TRAIL_PATH_ENV] = prior
        shutil.rmtree(tmp, ignore_errors=True)


def _server_params() -> StdioServerParameters:
    return StdioServerParameters(
        command=sys.executable,
        args=["-m", "practice_theory_implementation.server"],
        env={
            **os.environ,
            "PRACTICE_SERVER_MODE": "autonomic",
            "PRACTICE_DISABLE_DISPATCHER": "1",
        },
    )


def _value(content_list: list[Any]) -> Any:
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


async def drive_judge_scripted(target_eid: str, target_bundle: str) -> None:
    """Walk the Judge read affordances over the live server, then emit friction
    through the server if the deterministic detector finds an unevaluated proposal."""
    async with stdio_client(_server_params()) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            await session.call_tool("switch_practice", {"practice_id": "judge"})

            r = await session.call_tool(
                "invoke_affordance",
                {
                    "affordance_id": "read_enactment_steps",
                    "material_name": "judge_read_enactment_steps",
                    "arguments": {"enactment_id": target_eid},
                },
            )
            raw = _value(r.content)
            steps = raw if isinstance(raw, list) else ([raw] if raw else [])
            used = [str(s.get("affordance_id")) for s in steps if isinstance(s, dict)]

            ranking = [a for a in used if a in RANKING_AFFORDANCES]
            evaluated = any(a in EVALUATION_AFFORDANCES for a in used)
            if ranking and not evaluated:
                await session.call_tool(
                    "invoke_affordance",
                    {
                        "affordance_id": "emit_friction",
                        "material_name": "judge_emit_friction",
                        "arguments": {
                            "target_enactment_id": target_eid,
                            "kind": "unevaluated_proposal",
                            "content": (
                                f"Enactment of {target_bundle!r} invoked ranking "
                                f"affordance(s) {ranking} and acted on the output "
                                f"with no step that evaluated or selected against "
                                f"the ranking — a verdict forwarded, not judged."
                            ),
                            "observation_data": {
                                "ranking_affordances": ranking,
                                "used_affordances": used,
                            },
                        },
                    },
                )


# Live providers that hand the work to a real practitioner. Both adapters take
# (config, cwd=...) and isolate to the temp workspace: codex via cwd (its server
# gets a fixed inline env), claude via the inherited PRACTICE_TRAIL_PATH (its
# server inherits the process env). The in-process AnthropicSDKAdapter is the
# same provider as 'claude' but needs the optional `anthropic` extra installed;
# the CLI path needs no extra, so it is the default Anthropic option here.
def _build_live_adapter(provider: str, role: str, cwd: Path) -> AutonomicAdapter:
    config = AdapterConfig(
        role=role, bundle_id=role, brief=compose_brief(BUNDLES[role], substrate)
    )
    if provider == "codex":
        return CodexExecAdapter(config, cwd=cwd)
    if provider == "claude":
        return ClaudeCliAdapter(config, cwd=cwd)
    raise ValueError(f"unknown live provider {provider!r}")


async def drive_live(provider: str, role: str, store: EnactmentStore, cwd: Path) -> int:
    """Run one real practitioner pass via a provider adapter, isolated to `cwd`."""
    adapter = _build_live_adapter(provider, role, cwd)
    route_now(store)
    return await drain(
        adapter, RolePolicy(role=role), store, worker_id=f"eval-{role}", max_items=1
    )


async def run_case(case: Case, *, provider: str) -> dict[str, Any]:
    """Stage → run practitioner → grade. provider: 'scripted', 'codex', or 'claude'."""
    with temp_workspace() as (store, cwd):
        target_eid = case.seed(store)
        if provider == "scripted":
            if case.role != "judge":
                raise ValueError(f"scripted driver only supports judge cases, not {case.role!r}")
            await drive_judge_scripted(target_eid, case.target_bundle)
        elif provider in ("codex", "claude"):
            await drive_live(provider, case.role, store, cwd)
        else:
            raise ValueError(f"unknown provider {provider!r}")
        passed, evidence = case.grade(store, target_eid)
        return {
            "case": case.id,
            "provider": provider,
            "passed": passed,
            "target_enactment_id": target_eid,
            "evidence": evidence,
        }


def run_case_sync(case: Case, *, provider: str) -> dict[str, Any]:
    return asyncio.run(run_case(case, provider=provider))
