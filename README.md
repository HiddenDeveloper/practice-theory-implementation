# practice-theory-implementation

[![DOI](https://zenodo.org/badge/1249919423.svg)](https://doi.org/10.5281/zenodo.20405235)

A working implementation of the AI-trust-via-practice-theory architecture described in the essay series. The series names the missing layer in current agents as **situated awareness** (in Suchman's sense — a practitioner's grasp of where they are in the work, what the goal is, what is at hand, what would be a legitimate next step), and the practice bundle's five elements (teleo-affective, understanding, rules, affordances, materials) as the captured structure that delivers it. See `docs/`:

1. *AI Trust and Situated Awareness: A Practice Theory Reframe*
2. *Practice Theory — The Apprenticeship and a Strange Loop*
3. *Practice Theory — The Implementation* (this repo's companion paper; the twelve-step build)
4. *Practice Theory — A Worked Example (Calendar Stewardship)* — one practice against the calendar-move failure mode

The repository reflects the final state at the end of step 12 — every file an early step names exists at HEAD in its fully-evolved form. The journey is in the prose; the artifact is here.

## Quick start

```bash
uv sync
uv run python -m practice_theory_implementation
```

That runs the verify: somatic walk → autonomic Judge → autonomic Smoother, all via the `ScriptedAdapter` so no API keys or external tooling are needed. The verify is **hermetic by default** — it creates a fresh temp directory for the trail and substrate every run, so the printed walk matches the documented narrative every time. Set `PRACTICE_TRAIL_PATH` and `PRACTICE_SUBSTRATE_PATH` to persist state across runs (the persistent-trail story essay 3 names lives there; for the deterministic demo, the hermetic default is the right choice).

## Running with a real LLM

The autonomic loop can drive a real LLM via one of three adapters. The somatic surface is consumed by whichever harness you point at it (Claude Code, Codex, Cursor, etc.) via the `.mcp.json` at the repo root.

### Anthropic SDK (stdio default)

```bash
PRACTICE_AUTONOMIC_PROVIDER=anthropic \
  uv run --extra anthropic python -m practice_theory_implementation.autonomic_runner
```

Each adapter instance spawns its own stdio MCP server subprocess. A long-lived HTTP server is still experimental because active practice state is not yet per-session; start it only with `PRACTICE_EXPERIMENTAL_HTTP=1` and use one client per server process until that lands.

### Claude CLI

```bash
PRACTICE_AUTONOMIC_PROVIDER=anthropic_cli \
  uv run python -m practice_theory_implementation.autonomic_runner
```

Requires the `claude` binary on PATH.

### Codex CLI

```bash
PRACTICE_AUTONOMIC_PROVIDER=codex \
  PRACTICE_CODEX_MODEL=gpt-5.3-codex \
  uv run python -m practice_theory_implementation.autonomic_runner
```

Requires the `codex` binary on PATH. **Model gotcha:** with ChatGPT-account auth, Codex rejects most generic model names (`gpt-5`, `gpt-5-mini`, `o4-mini`, etc.) with a 400 `invalid_request_error`. `gpt-5.3-codex` works. If you hit `codex exec exited 1` with only the banner in the log, `codex login status` and run a one-off `codex exec --model <name> "hi"` to confirm the model is accepted. If your `~/.codex/config.toml` default is bogus, the adapter inherits it whenever `PRACTICE_CODEX_MODEL` is unset.

## Stopping the runner

Either Ctrl-C, or:

```bash
touch /tmp/practice-autonomic-quit
```

The runner finishes any in-flight `codex exec` / `claude -p` / SDK call and exits cleanly.

## RemSleep memory recall and consolidation

The autonomic runner can also run RemSleep as two autonomic practices. Memory
Recall runs on a schedule and dispatches source-backed `memory_signal` rows;
Memory Consolidation polls those signals and handles them by writing, staging,
or explicitly skipping the candidate. It is off by default:

```bash
PRACTICE_AUTONOMIC_PROVIDER=codex \
  PRACTICE_REMSLEEP_ENABLED=1 \
  PRACTICE_REMSLEEP_INTERVAL_SECONDS=21600 \
  uv run python -m practice_theory_implementation.autonomic_runner
```

RemSleep stores its checkpoint at `data/remsleep_checkpoint.json` and staged
review candidates at `data/remsleep_staged_candidates.jsonl` by default. Memory
signals live in `data/remsleep_memory_signals.jsonl`, with handled markers in
`data/remsleep_handled_signals.jsonl`. Override those with
`PRACTICE_REMSLEEP_CHECKPOINT_PATH`, `PRACTICE_REMSLEEP_STAGED_CANDIDATES_PATH`,
`PRACTICE_REMSLEEP_MEMORY_SIGNALS_PATH`, and
`PRACTICE_REMSLEEP_HANDLED_SIGNALS_PATH`.

For a staging-only dry run that uses the local `.codex/config.toml` service env
without advancing the real checkpoint:

```bash
uv run python scripts/remsleep_dry_run.py
```

## Operational notes

### Stale claims after a crash or kill

The inbox tables use a 10-minute claim lease. If a runner is killed mid-dispatch, the rows it claimed stay claimed until the lease expires. Restarting the runner under the same `worker_id` (`{provider}-judge`, `{provider}-smoother`) does *not* reclaim them — the claim scheme is intentionally multi-worker safe. To clear stale claims immediately:

```bash
uv run python -c "
import sqlite3
conn = sqlite3.connect('data/trail.db')
for t in ('judge_inbox', 'smoother_inbox'):
    n = conn.execute(f'UPDATE {t} SET claimed_at=NULL, claimed_by=NULL, claim_expires_at=NULL WHERE consumed_at IS NULL').rowcount
    print(f'{t}: cleared {n}')
conn.commit()
"
```

### Monitoring a running runner

Inbox counts:

```bash
uv run python -c "from practice_theory_implementation.trail import EnactmentStore; s=EnactmentStore(); print('judge:', s.pending_judge_inbox_count(), 'smoother:', s.pending_smoother_inbox_count()); s.close()"
```

Friction observations:

```bash
uv run python -c "from practice_theory_implementation.trail import EnactmentStore; s=EnactmentStore()
for f in s.all_friction():
    print(f.id, f.kind, '->', f.target_enactment_id[:8], 'addressed' if f.addressed_at else 'pending')
s.close()"
```

What's currently being dispatched (live):

```bash
ps aux | grep -E "codex exec|claude -p" | grep -v grep
```

### Resetting the trail and substrate

The verify uses a temp directory by default (hermetic), so there's nothing to reset between verify runs.

If you've set `PRACTICE_TRAIL_PATH` and `PRACTICE_SUBSTRATE_PATH` to persistent local paths and want to start fresh, delete the files at exactly those paths (and SQLite's WAL/SHM siblings if present). For example, if you set them inside `data/`:

```bash
rm -f "$PRACTICE_TRAIL_PATH" "$PRACTICE_TRAIL_PATH"-shm "$PRACTICE_TRAIL_PATH"-wal "$PRACTICE_SUBSTRATE_PATH"
```

The next run recreates both from the seed pools. Note: the trail and substrate must be paired — the verify requires both env vars to be set together, or neither (mixed persistent/temp setups leak stale state and are rejected at startup).

## Layout

```
src/practice_theory_implementation/
  types.py                 # Bundle, Substrate, PoolElement, Affordance, Material
  pools.py                 # compatibility shim exposing the loaded substrate
  registry.py              # binds Material.name to executable code
  projection.py            # project(bundle, substrate, registry, engagement?) -> ProjectedPractice
  server.py                # FastMCP surface, instructions, practice://* resources
  substrate_loader.py      # reads markdown + YAML-frontmatter substrate files
  substrate_writer.py      # persists Practice Management amendments to substrate/
  trail.py                 # enactments, steps, friction_observations, judge_inbox, smoother_inbox
  autonomic_dispatcher.py  # routes closed enactments and Friction into the inboxes
  autonomic_adapters.py    # ScriptedAdapter, AnthropicSDKAdapter, ClaudeCliAdapter, CodexExecAdapter
  autonomic_runner.py      # drives Judge, Smoother, and optional RemSleep workers
  __main__.py              # verify
  bundles/                 # Activities Management, Reflection, Practice Management,
                           # Judge, Smoother, plus the engagement bundle
  materials/               # the executables each material's name resolves to
```

## License

Apache-2.0 — see [`LICENSE`](LICENSE). The essays deposited on Zenodo carry their own deposit licenses (typically CC-BY-4.0); the source tree here is Apache-2.0.
