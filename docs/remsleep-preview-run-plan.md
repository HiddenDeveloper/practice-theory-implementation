# RemSleep preview-first manual run — execution plan

**Status:** planned, not started. Intended to be executed in a fresh session.

## Goal

Manually run the two RemSleep practices — **Memory Recall → Memory Consolidation**
— against the real Neo4j/Qdrant, **preview** the proposed canonical-memory updates,
and **apply** only on explicit approval. Preview-first and *capability-enforced*:
canonical writes are captured, never applied, until an explicit apply step.

RemSleep is now the **sole** canonical keeper — the Cognabot Self-Reflection Agent
is retired. There should be no other writer to the canonical spine.

> **Correction (2026-06-02):** this "SRA retired" claim was *not* true when written.
> Live evidence showed the Cognabot daemon's `self_reflection` task (the Pillar
> Maintainer) was still stamping `last_reviewed_at` on the canonical spine — an
> uncontrolled second writer. It was then explicitly disabled
> (`config/stonemonkey/daemon.json` → `self_reflection.enabled: false`, then
> `curl -X POST localhost:8001/reload`). RemSleep is sole keeper only while that
> flag stays off; a daemon restart from another config re-introduces the second
> writer. Watch `last_reviewed_at` for non-RemSleep writes before relying on this.

## Why (context for a fresh session)

- The canonical memory (`CanonicalSelf` / `CanonicalProfile` / `CanonicalContext` /
  `CanonicalGuidance` in Neo4j) lags the lived work — the "write-only memory /
  compilation gap" AIlumina names in its own reflection. Episodes land in Qdrant;
  the synthesis to canonical lags.
- The *autonomous* fix is a background **HTTP-transport** MCP server running the
  RemSleep loop unattended. **This plan is the manual, on-demand path** that does
  not need that server.
- Recall + Consolidation are autonomic LLM practices (bundles `memory_recall`,
  `memory_consolidation`), driven by an LLM through the autonomic MCP server via a
  provider adapter (claude/codex). They are *judgement*, not deterministic — so a
  meaningful preview needs the real LLM practitioners, not the plumbing-only
  `scripts/remsleep_dry_run.py`.

## Approach A — capability-enforced preview (chosen)

Do not trust the prompt to hold an irreversible boundary; enforce it in the
materials (the lesson from the eval security review). Add a
`PRACTICE_REMSLEEP_PREVIEW` mode honored by the three canonical-mutating materials
so they **capture intended writes to a journal instead of applying them**:

| Material | File | Preview behavior |
|---|---|---|
| `write_non_episodic_memory` | `src/practice_theory_implementation/materials/engagement_context.py` | append the intended write (anchor, content, kind, tags, confidence, memory_id) to the preview journal; return `{"preview": true, ...}`; **no Neo4j write** |
| `ensure_self_rooted_spine` | `engagement_context.py` | record intended spine-edge MERGEs to the journal; no write |
| `remsleep_record_checkpoint` | `src/practice_theory_implementation/materials/remsleep.py` | **no-op** (do not advance the durable checkpoint); note the intended advance in the journal |

Env:
- `PRACTICE_REMSLEEP_PREVIEW=1` → capture mode
- `PRACTICE_REMSLEEP_PREVIEW_PATH` → journal file (jsonl)

The journal **is** the proposed canonical updates (the preview). Apply = replay the
journal entries through the real materials (PREVIEW off) and advance the checkpoint
deliberately.

## Build steps

1. **Preview mode in the 3 materials.** Small, contained. Unit-test the capture
   path: with `PRACTICE_REMSLEEP_PREVIEW=1`, a write appends to the journal and
   makes no store call; with it unset, behavior is unchanged.
2. **`scripts/remsleep_preview.py`:**
   - `os.environ.update(practice_service_env(cwd))` — real Neo4j/Qdrant creds.
   - Set `PRACTICE_REMSLEEP_PREVIEW=1`, `PRACTICE_REMSLEEP_PREVIEW_PATH`, a **temp
     signals path** (isolated preview), and leave the real checkpoint path (preview
     won't advance it).
   - **Drive Memory Recall** — one pass. Build a provider adapter
     (`ClaudeCliAdapter` recommended) with
     `AdapterConfig(role="memory_recall", bundle_id="memory_recall", brief=compose_brief(BUNDLES["memory_recall"], substrate))`;
     `await open()`; `await dispatch(WorkItem(role="memory_recall", dispatch_message=<recall prompt>))`;
     `await close()`. Reuse the recall `dispatch_message` from
     `autonomic_runner._run_memory_recall_loop`.
   - **Drive Memory Consolidation** — one pass, same pattern, role/bundle
     `memory_consolidation`. For the `dispatch_message`: locate the consolidation
     prompt in `autonomic_runner.py` (or write one): read pending signals, compare
     cited evidence with the canonical spine, write/stage source-backed updates,
     mark signals handled. In preview, its writes are captured, not applied.
   - **Print the preview journal** — the proposed canonical updates, grouped by
     anchor (self / profile / context / guidance), each with its sources.
   - **`--apply` flag:** replay the (approved) journal with PREVIEW off — call the
     real `write_non_episodic_memory` / `ensure_self_rooted_spine` — then advance
     the checkpoint deliberately.
3. **Verify.** Preview run → journal shows proposed updates. Confirm the canonical
   nodes are unchanged (read them before/after — identical) and the checkpoint is
   unchanged. Then a deliberate `--apply` on the approved entries.

## Safety invariants

- Canonical writes captured, never applied, until `--apply` (capability-enforced,
  not prompt-trusted).
- Checkpoint never advances in preview (the same episodes stay re-reviewable).
- Provider runs confined to the autonomic MCP tools (`--allowedTools`), **no
  `bypassPermissions`** (per the eval hardening).
- Reads hit the real stores; writes do not.
- This is the **first** time the real RemSleep practitioners run against the real
  canonical graph. Reads are live; writes are captured. Go preview-first.

## Open decisions (confirm with the user at run time)

- **Provider:** `claude` (recommended — verified working in the eval harness) vs `codex`.
- **Signals:** temp/isolated (clean preview) vs the real signals file.
- **Trail:** real (audit record) vs isolated. Recommend real.
- **Journal location:** `data/remsleep_preview.jsonl` (inspectable) vs temp.

## Key files

- Materials: `engagement_context.py` (`write_non_episodic_memory`,
  `ensure_self_rooted_spine`), `remsleep.py` (`remsleep_record_checkpoint`,
  dispatch/read signals, recall/graph reads).
- Bundles: `substrate/bundles/memory_recall.md`, `substrate/bundles/memory_consolidation.md`.
- Prompts: `autonomic_runner.py` (`_run_memory_recall_loop` dispatch_message;
  the consolidation prompt).
- Adapters: `autonomic_adapters.py` (`ClaudeCliAdapter` / `CodexExecAdapter`,
  `AdapterConfig`, `compose_brief`, `WorkItem`, `practice_service_env`).
- Plumbing reference: `scripts/remsleep_dry_run.py` (read→dispatch→stage→handle,
  service-env wiring).
- Drive pattern to reuse: `evals/harness.py` (`drive_live`, `_run_claude_somatic`).

## Note on the bigger arc

This manual preview run is the on-ramp. The durable fix is the background HTTP MCP
server running RemSleep on a schedule — once preview/apply is trusted, that loop
keeps the canonicals current without manual triggering. Preview-first now de-risks
turning that loop on later.
