"""Prove the HTTP server scopes active-practice state per MCP session.

Starts a long-lived autonomic server over streamable HTTP, opens two concurrent
client sessions, switches each to a DIFFERENT practice, and asserts each session
keeps seeing its own active practice through interleaved calls. Under the old
module-global state, one session's switch_practice would clobber the other's;
per-session state keeps them isolated.

    uv run python scripts/verify_http_sessions.py
"""

from __future__ import annotations

import asyncio
import os
import sys
import tempfile
from pathlib import Path

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

PORT = int(os.environ.get("PRACTICE_VERIFY_HTTP_PORT", "7185"))
URL = f"http://127.0.0.1:{PORT}/mcp"


def _value(result: object) -> object:
    import json

    content = getattr(result, "content", None) or []
    for item in content:
        text = getattr(item, "text", None)
        if text is not None:
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return text
    return None


async def _active(session: ClientSession) -> object:
    res = await session.call_tool("current_practice", {})
    value = _value(res)
    if isinstance(value, dict) and isinstance(value.get("practice"), dict):
        return value["practice"].get("id")
    return None


async def _switch(session: ClientSession, practice_id: str) -> object:
    res = await session.call_tool("switch_practice", {"practice_id": practice_id})
    value = _value(res)
    return value.get("active") if isinstance(value, dict) else value


async def _run_checks() -> bool:
    async with (
        streamablehttp_client(URL) as (read_a, write_a, _a),
        streamablehttp_client(URL) as (read_b, write_b, _b),
    ):
        async with (
            ClientSession(read_a, write_a) as a,
            ClientSession(read_b, write_b) as b,
        ):
            await a.initialize()
            await b.initialize()

            ok = True

            # Interleave switches to different practices, then read both back.
            await _switch(a, "judge")
            await _switch(b, "smoother")
            active_a = await _active(a)
            active_b = await _active(b)
            print(f"after A=judge B=smoother -> A sees {active_a!r}, B sees {active_b!r}")
            ok = ok and active_a == "judge" and active_b == "smoother"

            # Now flip B and re-read A — A must NOT change.
            await _switch(b, "memory_recall")
            active_a = await _active(a)
            active_b = await _active(b)
            print(f"after B=memory_recall   -> A sees {active_a!r}, B sees {active_b!r}")
            ok = ok and active_a == "judge" and active_b == "memory_recall"

            # And flip A — B must NOT change.
            await _switch(a, "memory_consolidation")
            active_a = await _active(a)
            active_b = await _active(b)
            print(f"after A=memory_consol.  -> A sees {active_a!r}, B sees {active_b!r}")
            ok = ok and active_a == "memory_consolidation" and active_b == "memory_recall"

            return ok


async def _wait_ready(timeout: float = 20.0) -> bool:
    deadline = asyncio.get_event_loop().time() + timeout
    while asyncio.get_event_loop().time() < deadline:
        try:
            async with streamablehttp_client(URL) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    return True
        except Exception:
            await asyncio.sleep(0.5)
    return False


async def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="http-session-verify-"))
    env = {
        **os.environ,
        "PRACTICE_SERVER_MODE": "autonomic",
        "PRACTICE_TRANSPORT": "http",
        "PRACTICE_HTTP_PORT": str(PORT),
        "PRACTICE_DISABLE_DISPATCHER": "1",
        "PRACTICE_TRAIL_PATH": str(tmp / "trail.db"),
        "PRACTICE_LOG_LEVEL": "ERROR",
    }
    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "practice_theory_implementation.server",
        env=env,
        cwd=str(Path.cwd()),
    )
    try:
        if not await _wait_ready():
            print("SERVER DID NOT BECOME READY")
            return 2
        passed = await _run_checks()
        print("\nRESULT:", "PASS — sessions isolated" if passed else "FAIL — cross-session leak")
        return 0 if passed else 1
    finally:
        proc.terminate()
        try:
            await asyncio.wait_for(proc.wait(), timeout=5)
        except TimeoutError:
            proc.kill()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
