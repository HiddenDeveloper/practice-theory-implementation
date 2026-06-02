"""CodexExecAdapter transport selection — HTTP via mcp_url, else inline stdio."""

from __future__ import annotations

import asyncio
import subprocess
from typing import Any

import pytest

from practice_theory_implementation import autonomic_adapters
from practice_theory_implementation.autonomic_adapters import (
    AdapterConfig,
    CodexExecAdapter,
    WorkItem,
)


def _capture_cmd(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    captured: dict[str, Any] = {}

    def _fake_run(cmd: list[str], **_: Any) -> subprocess.CompletedProcess[str]:
        captured["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(autonomic_adapters.subprocess, "run", _fake_run)
    return captured


def _run_dispatch(adapter: CodexExecAdapter) -> None:
    asyncio.run(
        adapter.dispatch(
            WorkItem(primary_id="x", role="judge", dispatch_message="do it")
        )
    )


def test_codex_points_at_http_url_when_mcp_url_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = _capture_cmd(monkeypatch)
    adapter = CodexExecAdapter(
        AdapterConfig(
            role="judge",
            bundle_id="judge",
            brief="brief",
            mcp_url="http://127.0.0.1:7181/mcp",
        )
    )
    _run_dispatch(adapter)
    joined = " ".join(captured["cmd"])
    assert (
        'mcp_servers.apprenticeship_autonomic.url="http://127.0.0.1:7181/mcp"' in joined
    )
    # No stdio injection when on HTTP.
    assert "apprenticeship_autonomic.command=" not in joined
    assert "apprenticeship_autonomic.env=" not in joined


def test_codex_injects_stdio_when_no_mcp_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = _capture_cmd(monkeypatch)
    adapter = CodexExecAdapter(
        AdapterConfig(role="judge", bundle_id="judge", brief="brief")
    )
    _run_dispatch(adapter)
    joined = " ".join(captured["cmd"])
    assert "apprenticeship_autonomic.command=" in joined
    assert "apprenticeship_autonomic.args=" in joined
    # No HTTP url when spawning stdio.
    assert "apprenticeship_autonomic.url=" not in joined
