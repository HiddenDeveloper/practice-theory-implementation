"""Engagement-enactment lifecycle: no phantom enactment is opened at import.

The somatic server projects the engagement at session scope. Earlier, the
module-import projection refresh opened a `continuous_self` enactment against
the stdio session key as a side effect. Under HTTP that key is never a real
client and the idle reaper skips it, so every process start leaked one open
zero-step engagement enactment. These tests pin the fix: importing the server
prepares the projection but opens nothing; the enactment opens only when a real
session first interacts.
"""

from __future__ import annotations

import importlib
import sys

import pytest


@pytest.fixture
def somatic_server(tmp_path, monkeypatch):
    """Import a fresh somatic server bound to a throwaway trail DB."""
    monkeypatch.setenv("PRACTICE_SERVER_MODE", "somatic")
    monkeypatch.setenv("PRACTICE_TRANSPORT", "stdio")
    monkeypatch.setenv("PRACTICE_TRAIL_PATH", str(tmp_path / "trail.db"))
    # Drop any already-imported copy so module-level startup re-runs against the
    # throwaway DB and the patched environment.
    sys.modules.pop("practice_theory_implementation.server", None)
    server = importlib.import_module("practice_theory_implementation.server")
    yield server
    sys.modules.pop("practice_theory_implementation.server", None)


def _open_enactments(server) -> list:
    with server._trail._cursor() as cur:  # noqa: SLF001 — test inspects the trail
        cur.execute("SELECT id, practice_id FROM enactments WHERE closed_at IS NULL")
        return cur.fetchall()


def test_import_opens_no_engagement_enactment(somatic_server):
    """Importing the somatic server must not open a phantom engagement enactment."""
    assert _open_enactments(somatic_server) == []
    assert somatic_server._session().engagement_enactment_id is None
    # The projection itself is prepared and ready for resource/tool reads.
    assert somatic_server._session().engagement is not None


def test_first_interaction_opens_engagement_enactment(somatic_server):
    """A real session touching a tool opens the engagement enactment lazily."""
    somatic_server.list_practices()
    somatic_server._refresh_engagement_projection()
    s = somatic_server._session()
    assert s.engagement_enactment_id is not None
    open_rows = _open_enactments(somatic_server)
    assert len(open_rows) == 1
    assert open_rows[0]["practice_id"] == s.engagement.id
