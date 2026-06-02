"""One-off: capture the two factual canonical rewords as field updates.

Routes the staged-but-uncontested rewords (files-as-substrate; "third essay" ->
four-part series) through the new preview-gated `update_canonical_field`
material rather than a hand-written Cypher SET. Runs under
PRACTICE_REMSLEEP_PREVIEW, so every edit is captured to a journal and applied
only via:

    uv run python scripts/remsleep_preview.py --apply --journal data/remsleep_rewords.jsonl

The wording here was reviewed with the user; this script only applies the
already-decided field edits (deterministic I/O — no practitioner judgement).
The identity reword (MonyetBatu handle) is deliberately NOT included; it stays
staged until the user confirms it.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from practice_theory_implementation.autonomic_adapters import practice_service_env
from practice_theory_implementation.materials import engagement_context, remsleep_preview

JOURNAL = Path("data") / "remsleep_rewords.jsonl"

_FOUR_ESSAY_SUMMARY_CLAUSE = (
    "Companion to a four-part practice-theory series — essays 1 (The Meaning "
    "Layer) and 2 (Apprenticeship and a Strange Loop) published to Zenodo "
    "2026-05-23; the worked-example and implementation essays are the current "
    "writing."
)
_SUBSTRATE_SUMMARY_CLAUSE = (
    " The substrate itself is now markdown+YAML files under substrate/ as the "
    "single source of truth (was a Python seed + SQLite overlay)."
)
_SUBSTRATE_DECISION = (
    "Adopt files-as-substrate: substrate/ markdown+YAML files are the single "
    "source of truth (replacing the Python seed + SQLite overlay), with a "
    "write-path persisting PM/Smoother amendments back to files (atomic write + "
    "hermetic verify against a temp copy), a _SAFE_STEM path guard, and a "
    "source-reload PM affordance."
)
_FOUR_ESSAY_PROJECT = (
    "Practice-theory essay series — four parts; implementation + worked-example "
    "essays the current writing (doc and code in lockstep)"
)
_SOURCES = [
    "claude-code-29a4311c-turn-1",
    "codex-019e6718-turn-0",
    "memory-signal-20260602035831790284",
    "memory-signal-20260602035840029110",
]


def _swap_element(items: list[str], needle: str, replacement: str) -> list[str] | None:
    """Return items with the first element containing `needle` replaced; None if absent."""
    out = list(items)
    for i, el in enumerate(out):
        if needle.lower() in el.lower():
            out[i] = replacement
            return out
    return None


def main() -> None:
    os.environ.update(practice_service_env(Path.cwd()))
    os.environ[remsleep_preview.PREVIEW_ENABLED_ENV] = "1"
    os.environ[remsleep_preview.PREVIEW_PATH_ENV] = str(JOURNAL)
    if JOURNAL.exists():
        JOURNAL.unlink()

    ctx = engagement_context.consult_canonical_context()
    summary = str(ctx.get("summary", ""))
    active_projects = list(ctx.get("active_projects", []))
    next_actions = list(ctx.get("next_actions", []))

    edits: list[dict[str, object]] = []

    # 1) summary (replace) — both rewords folded into one scalar.
    new_summary = summary.replace(
        "Companion to the third essay in the practice-theory series.",
        _FOUR_ESSAY_SUMMARY_CLAUSE,
    )
    if _SUBSTRATE_SUMMARY_CLAUSE.strip() not in new_summary:
        new_summary = new_summary.rstrip() + _SUBSTRATE_SUMMARY_CLAUSE
    edits.append({"field": "summary", "op": "replace", "value": new_summary, "before": summary})

    # 2) recent_decisions (append) — the files-as-substrate decision.
    edits.append(
        {"field": "recent_decisions", "op": "append", "value": _SUBSTRATE_DECISION, "before": None}
    )

    # 3) active_projects (replace whole list) — swap the "third essay" entry.
    new_projects = _swap_element(active_projects, "third essay", _FOUR_ESSAY_PROJECT)
    if new_projects is not None:
        edits.append(
            {
                "field": "active_projects",
                "op": "replace",
                "value": new_projects,
                "before": active_projects,
            }
        )

    # 4) next_actions (replace whole list) — rename "third essay" -> implementation essay.
    new_actions = _swap_element(
        next_actions,
        "third essay",
        "Reflect the Self-rooting and situated-awareness framing in the "
        "implementation essay — keep doc and code in lockstep",
    )
    if new_actions is not None:
        edits.append(
            {"field": "next_actions", "op": "replace", "value": new_actions, "before": next_actions}
        )

    print(f"PREVIEW journal={JOURNAL}\n")
    for e in edits:
        result = engagement_context.update_canonical_field(
            str(e["field"]),
            e["value"],
            anchor="context",
            op=str(e["op"]),
            sources=_SOURCES,
        )
        status = "captured" if result.get("preview") else f"UNEXPECTED: {result}"
        print(f"── CanonicalContext.{e['field']} ({e['op']}) — {status} ──")
        if e["field"] in ("summary",):
            print(f"  BEFORE: {e['before']}")
            print(f"  AFTER : {e['value']}")
        elif e["op"] == "append":
            print(f"  APPEND: {e['value']}")
        else:
            print(f"  BEFORE: {json.dumps(e['before'], ensure_ascii=False)}")
            print(f"  AFTER : {json.dumps(e['value'], ensure_ascii=False)}")
        print()

    print(f"Captured {len(edits)} field edits to {JOURNAL}.")
    print("Review the before/after above. To apply on approval:")
    print(f"    uv run python scripts/remsleep_preview.py --apply --journal {JOURNAL}")


if __name__ == "__main__":
    main()
