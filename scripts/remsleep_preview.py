"""Preview-first manual RemSleep run — Memory Recall -> Memory Consolidation.

Runs the two real RemSleep practitioners against the real Neo4j/Qdrant, but with
``PRACTICE_REMSLEEP_PREVIEW=1`` so every canonical-mutating material captures its
intended write to a journal instead of applying it (capability-enforced, not
prompt-trusted). Reads are live; writes are captured. The journal **is** the
proposed canonical update.

Two modes:

  preview (default)
    - real service env (Neo4j/Qdrant), real trail (audit record)
    - isolated temp signal files (a clean preview, the real signals untouched)
    - the real checkpoint path stays, so Recall reads the true watermark; the
      preview never advances it (the material no-ops the write)
    - drives one Memory Recall pass, then one Memory Consolidation pass per
      dispatched signal; prints the journal and proves canonicals + checkpoint
      are byte-for-byte unchanged

  --apply
    - replays the (approved) journal with preview OFF: real
      write_non_episodic_memory / ensure_self_rooted_spine, then advances the
      checkpoint deliberately as the last step

Usage:
    uv run python -m scripts.remsleep_preview                # preview
    uv run python scripts/remsleep_preview.py --apply        # apply approved journal

The provider is Claude via `claude -p`, confined to the autonomic MCP tools by
--allowedTools with NO bypassPermissions (the eval-hardened path).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from practice_theory_implementation.autonomic_adapters import (
    AdapterConfig,
    ClaudeCliAdapter,
    WorkItem,
    compose_brief,
    practice_service_env,
)
from practice_theory_implementation.bundles import BUNDLES
from practice_theory_implementation.materials import (
    engagement_context,
    remsleep,
    remsleep_preview,
)
from practice_theory_implementation.pools import substrate

logger = logging.getLogger("remsleep_preview")

# The recall/consolidation dispatch prompts mirror the autonomic runner's
# scheduled loops (autonomic_runner._run_memory_recall_loop and
# _run_memory_consolidation_signal_loop) so the manual preview drives the
# practitioners exactly as the unattended background loop would.
_RECALL_DISPATCH = (
    "Run one RemSleep memory-recall pass. Switch to `memory_recall`, then read "
    "the checkpoint, the current canonical/user context, the unreviewed episodes "
    "after the checkpoint, and the non-canonical graph nodes updated after the "
    "graph watermark. Judge what you read and dispatch memory_signals "
    "accordingly. Stop after one recall pass."
)


def _backfill_recall_dispatch(since: str) -> str:
    """A recall prompt that reviews the whole episodic window from `since` forward.

    The window boundary is I/O the script sets; the judgement of what (if
    anything) belongs in canonical memory stays entirely with the practitioner.
    """
    return (
        "Run a RemSleep memory-recall BACKFILL pass. Switch to `memory_recall`. "
        "There is no usable checkpoint — you are catching up canonical memory "
        f"after a period with no RemSleep review. Review EVERY episodic turn from "
        f"{since} forward up to now. Use `recall_unreviewed_episodes` with "
        f"date_from='{since}'; it returns newest-first, max 20 per call, so page "
        "the whole window by repeatedly lowering date_to to the oldest turn you "
        f"have seen until you reach {since}. Do not stop after one batch. Also "
        "read the current canonical/user context and the non-canonical graph "
        "nodes. Judge what you read against the canonical spine and dispatch "
        "bounded, source-backed memory_signals for anything that belongs in "
        "canonical memory — quote real turn ids as evidence. When done, state how "
        "far back you actually reached and roughly how many turns/conversations "
        "you reviewed. Do not write canonical memory and do not record a "
        "checkpoint in this pass — recall only dispatches signals."
    )
_CONSOLIDATION_DISPATCH_PREFIX = (
    "Run one RemSleep memory-consolidation pass. Switch to `memory_consolidation`. "
    "Consume the following memory_signal by reading any cited evidence, comparing "
    "it with canonicals, and then either writing additive non-episodic memory, "
    "staging an ambiguous/high-impact candidate, or recording why no canonical "
    "change is warranted. Only after the signal has been handled should you mark "
    "it handled and record the checkpoint if the review range is complete. Stop "
    "after this signal."
)


def _service_summary(env: dict[str, str]) -> str:
    neo4j = any(k in env for k in ("PRACTICE_NEO4J_AUTH", "NEO4J_AUTH"))
    return (
        f"neo4j={'yes' if neo4j else 'no'} "
        f"qdrant={'yes' if env.get('PRACTICE_QDRANT_URL') else 'default'} "
        f"embed={'yes' if env.get('PRACTICE_EMBED_URL') else 'default'}"
    )


def _canonical_snapshot() -> dict[str, Any]:
    """Read the three canonical landing nodes (live read, no write)."""
    return {
        "self": engagement_context.consult_canonical_self(),
        "profile": engagement_context.consult_canonical_profile(),
        "context": engagement_context.consult_canonical_context(),
    }


def _checkpoint_snapshot() -> dict[str, Any]:
    return remsleep.remsleep_read_checkpoint()


def _stable(value: Any) -> str:
    return json.dumps(value, sort_keys=True)


async def _drive_role(role: str, dispatch_message: str, args: argparse.Namespace) -> None:
    """Run one practitioner pass for `role` via the no-bypass Claude CLI adapter."""
    if role not in BUNDLES:
        raise SystemExit(f"bundle {role!r} is not loaded; cannot drive RemSleep")
    adapter = ClaudeCliAdapter(
        AdapterConfig(
            role=role, bundle_id=role, brief=compose_brief(BUNDLES[role], substrate)
        ),
        model=args.model,
        effort=args.effort,
        permission_mode=None,  # confine to --allowedTools; no bypassPermissions
    )
    logger.info("DRIVE %s", role)
    await adapter.open()
    try:
        await adapter.dispatch(
            WorkItem(
                primary_id=datetime.now(UTC).isoformat(timespec="seconds"),
                role=role,
                dispatch_message=dispatch_message,
            )
        )
    finally:
        await adapter.close()


def _prepare_preview_env(journal_path: Path, signals_dir: Path | None = None) -> Path:
    """Set the service + preview env. Returns the dir holding the signal files.

    With no `signals_dir`, isolates signals in a fresh temp dir (a clean
    one-shot preview). With one, uses that persistent dir so a `--recall-only`
    pass and a later `--skip-recall` consolidation share the same signals.
    """
    os.environ.update(practice_service_env(Path.cwd()))
    os.environ[remsleep_preview.PREVIEW_ENABLED_ENV] = "1"
    os.environ[remsleep_preview.PREVIEW_PATH_ENV] = str(journal_path)
    # The real checkpoint path is deliberately left alone: Recall must read the
    # true watermark, and preview no-ops its write.
    if signals_dir is None:
        sig_dir = Path(tempfile.mkdtemp(prefix="remsleep-preview-"))
    else:
        sig_dir = signals_dir
        sig_dir.mkdir(parents=True, exist_ok=True)
    os.environ[remsleep.MEMORY_SIGNALS_PATH_ENV] = str(sig_dir / "memory_signals.jsonl")
    os.environ[remsleep.HANDLED_SIGNALS_PATH_ENV] = str(sig_dir / "handled_signals.jsonl")
    os.environ[remsleep.STAGED_CANDIDATES_PATH_ENV] = str(
        sig_dir / "staged_candidates.jsonl"
    )
    return sig_dir


def _print_journal(journal_path: Path) -> list[dict[str, Any]]:
    entries = remsleep_preview.read_journal(journal_path)
    print(f"\n=== PREVIEW JOURNAL — {len(entries)} entries — {journal_path} ===")
    if not entries:
        print("  (empty: the practitioners proposed no canonical change)")
        return entries

    writes = [e for e in entries if e.get("material") == "write_non_episodic_memory"]
    by_anchor: dict[str, list[dict[str, Any]]] = {}
    for entry in writes:
        by_anchor.setdefault(str(entry.get("anchor", "?")), []).append(entry)
    for anchor in sorted(by_anchor):
        print(f"\n  ┌─ anchor: {anchor} ({len(by_anchor[anchor])} proposed) ─")
        for entry in by_anchor[anchor]:
            print(f"  │ [{entry.get('kind')}] {entry.get('content')}")
            meta = (
                f"source={entry.get('source')!r} tags={entry.get('tags')} "
                f"confidence={entry.get('confidence')} id={entry.get('memory_id')}"
            )
            print(f"  │    {meta}")

    field_updates = [
        e for e in entries if e.get("material") == "update_canonical_field"
    ]
    for entry in field_updates:
        print(
            f"\n  ┌─ landing-node field update — {entry.get('anchor')}"
            f".{entry.get('field')} ({entry.get('op')}) ─"
        )
        print(f"  │ {_stable(entry.get('value'))}")
        if entry.get("sources"):
            print(f"  │    sources: {entry.get('sources')}")

    spine = [e for e in entries if e.get("material") == "ensure_self_rooted_spine"]
    for entry in spine:
        print("\n  ┌─ spine root (CanonicalSelf) ─")
        for edge in entry.get("intended_edges", []):
            print(
                f"  │ MERGE (Self)-[:{edge.get('edge')}]->"
                f"({edge.get('target_label')} {edge.get('target_id')})"
            )

    checkpoints = [
        e for e in entries if e.get("material") == "remsleep_record_checkpoint"
    ]
    for entry in checkpoints:
        print("\n  ┌─ checkpoint advance (NOT applied in preview) ─")
        print(f"  │ {_stable(entry.get('intended_checkpoint'))}")
    return entries


def _print_invariants(
    before_canon: dict[str, Any],
    after_canon: dict[str, Any],
    before_cp: dict[str, Any],
    after_cp: dict[str, Any],
) -> bool:
    canon_ok = _stable(before_canon) == _stable(after_canon)
    cp_ok = _stable(before_cp) == _stable(after_cp)
    print("\n=== SAFETY INVARIANTS ===")
    print(f"  canonical nodes unchanged: {'PASS' if canon_ok else 'FAIL'}")
    print(f"  checkpoint unchanged:      {'PASS' if cp_ok else 'FAIL'}")
    if not canon_ok:
        print("  !! canonical drift detected — preview LEAKED a write:")
        print(f"     before: {_stable(before_canon)}")
        print(f"     after:  {_stable(after_canon)}")
    if not cp_ok:
        print("  !! checkpoint advanced during preview:")
        print(f"     before: {_stable(before_cp)}")
        print(f"     after:  {_stable(after_cp)}")
    return canon_ok and cp_ok


def _print_signals(pending: list[dict[str, Any]]) -> None:
    print(f"\n=== RECALL DISPATCHED {len(pending)} memory_signal(s) ===")
    for i, sig in enumerate(pending, 1):
        print(
            f"\n  [{i}] kind={sig.get('kind')} conf={sig.get('confidence')} "
            f"anchor={sig.get('suggested_anchor')} id={sig.get('id')}"
        )
        print(f"      {sig.get('content')}")
        src = sig.get("source_ids")
        if src:
            print(f"      sources: {src}")


async def _preview(journal_path: Path, args: argparse.Namespace) -> int:
    signals_dir = Path(args.signals_dir) if args.signals_dir else None
    sig_dir = _prepare_preview_env(journal_path, signals_dir)
    # Fresh journal: this run's proposal only.
    if journal_path.exists():
        journal_path.unlink()

    print(f"PREVIEW journal={journal_path}")
    print(f"PREVIEW signals_dir={sig_dir}")
    print(f"SERVICE_ENV {_service_summary(practice_service_env(Path.cwd()))}")
    if args.since:
        print(f"BACKFILL window: episodes from {args.since} forward")

    before_canon = _canonical_snapshot()
    before_cp = _checkpoint_snapshot()
    print(f"CHECKPOINT_BEFORE {_stable(before_cp)}")

    if not args.skip_recall:
        dispatch = _backfill_recall_dispatch(args.since) if args.since else _RECALL_DISPATCH
        await _drive_role("memory_recall", dispatch, args)

    signals = remsleep.remsleep_read_memory_signals(limit=args.max_signals)
    pending = signals.get("signals", []) if isinstance(signals, dict) else []
    _print_signals(pending)

    if args.recall_only:
        print(
            "\n--recall-only: signals dispatched, NOT consolidated. To consolidate "
            "them (preview-captured):\n"
            f"    uv run python scripts/remsleep_preview.py --skip-recall "
            f"--signals-dir {sig_dir} --journal {journal_path}"
        )
        return 0

    for signal in pending:
        message = (
            f"{_CONSOLIDATION_DISPATCH_PREFIX}\n\n"
            f"memory_signal:\n{json.dumps(signal, sort_keys=True)}"
        )
        await _drive_role("memory_consolidation", message, args)

    after_canon = _canonical_snapshot()
    after_cp = _checkpoint_snapshot()

    _print_journal(journal_path)
    invariants_ok = _print_invariants(
        before_canon, after_canon, before_cp, after_cp
    )
    print(
        "\nReview the journal above. To apply the approved proposals:\n"
        f"    uv run python scripts/remsleep_preview.py --apply --journal {journal_path}"
    )
    return 0 if invariants_ok else 1


def _apply_entry(entry: dict[str, Any]) -> dict[str, Any]:
    material = entry.get("material")
    if material == "write_non_episodic_memory":
        return engagement_context.write_non_episodic_memory(
            str(entry["content"]),
            memory_id=entry.get("memory_id"),
            kind=str(entry.get("kind", "note")),
            source=str(entry.get("source", "user_engagement")),
            tags=list(entry.get("tags") or []),
            confidence=entry.get("confidence"),
            anchor=str(entry.get("anchor", "context")),
        )
    if material == "update_canonical_field":
        return engagement_context.update_canonical_field(
            str(entry["field"]),
            entry.get("value"),
            anchor=str(entry.get("anchor", "context")),
            op=str(entry.get("op", "append")),
            sources=list(entry.get("sources") or []),
        )
    if material == "ensure_self_rooted_spine":
        return engagement_context.ensure_self_rooted_spine()
    if material == "remsleep_record_checkpoint":
        checkpoint = entry.get("intended_checkpoint") or {}
        return remsleep.remsleep_record_checkpoint(
            episode_sequence=checkpoint.get("episode_sequence"),
            episode_date_time=checkpoint.get("episode_date_time"),
            graph_updated_at=checkpoint.get("graph_updated_at"),
            reviewed_at=checkpoint.get("reviewed_at"),
            notes=checkpoint.get("notes"),
        )
    return {"skipped": True, "reason": f"unknown material {material!r}"}


def _apply(journal_path: Path) -> int:
    # Apply must NOT be in preview mode — these calls hit the real stores.
    os.environ.pop(remsleep_preview.PREVIEW_ENABLED_ENV, None)
    os.environ.pop(remsleep_preview.PREVIEW_PATH_ENV, None)
    os.environ.update(practice_service_env(Path.cwd()))

    entries = remsleep_preview.read_journal(journal_path)
    if not entries:
        print(f"no journal entries at {journal_path}; nothing to apply")
        return 0

    # Writes and spine first; advance the checkpoint last so a crash mid-apply
    # leaves the same range re-reviewable rather than skipped.
    checkpoints = [e for e in entries if e.get("material") == "remsleep_record_checkpoint"]
    others = [e for e in entries if e.get("material") != "remsleep_record_checkpoint"]
    print(f"APPLY {len(others)} write/spine + {len(checkpoints)} checkpoint from {journal_path}")
    for entry in [*others, *checkpoints]:
        result = _apply_entry(entry)
        status = "ERROR" if isinstance(result, dict) and result.get("error") else "OK"
        print(f"  {status} {entry.get('material')}: {_stable(result)[:240]}")
    return 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--journal",
        default=str(remsleep_preview._DEFAULT_PREVIEW_PATH),
        help="preview journal path (jsonl)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="replay the approved journal with preview OFF (real canonical writes)",
    )
    parser.add_argument("--model", default=None, help="override the claude model")
    parser.add_argument(
        "--effort", default=None, help="claude effort (e.g. low/medium/high)"
    )
    parser.add_argument(
        "--max-signals",
        type=int,
        default=50,
        help="max recall signals to read/consolidate in one preview",
    )
    parser.add_argument(
        "--since",
        default=None,
        help="backfill: review episodes from this date forward (e.g. 2026-05-23)",
    )
    parser.add_argument(
        "--recall-only",
        action="store_true",
        help="dispatch recall signals and stop (do not consolidate)",
    )
    parser.add_argument(
        "--skip-recall",
        action="store_true",
        help="consolidate already-dispatched signals from --signals-dir (no recall)",
    )
    parser.add_argument(
        "--signals-dir",
        default=None,
        help="persist signal files here (default: isolated temp); needed to share "
        "signals between a --recall-only pass and a later --skip-recall pass",
    )
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    args = _parse_args()
    journal_path = Path(args.journal)
    if args.apply:
        raise SystemExit(_apply(journal_path))
    raise SystemExit(asyncio.run(_preview(journal_path, args)))


if __name__ == "__main__":
    main()
