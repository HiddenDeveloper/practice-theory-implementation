# Plan — Tailscale `setec` as the shared secrets store

A pickup brief for a fresh session. Self-contained: read this + the linked files
and you have everything needed to implement. Spans **two solutions** under
`~/develop/home/`:

- **`practic-theory-implementation`** — Python, pm2-managed long-running
  processes (the autonomic keeper + MCP servers). *(this repo)*
- **`apprenticeship-cognabot`** — TypeScript/Bun, Docker Compose services (LLM
  harness, LINE webhooks, JIT services).

## Why (decision already made)

Move long-lived credentials off gitignored per-project `.env` files into **one
`setec` server on the tailnet**, shared by both solutions, fetched at process
startup. Rationale (researched 2026-06-21):

- Both solutions already run on a **Tailscale tailnet** → `setec` uses the
  tailnet policy *as* access control, so there is **no "secret zero"** to
  bootstrap (the usual cost of a central secrets manager). This is the deciding
  fit; SOPS+age (no shared store, per-repo encrypted files), 1Password (SaaS),
  and Vault/OpenBao (heavier, still needs client auth) all lose on the
  "one self-hosted store across both solutions" goal.
- `setec` is production-grade and current (Tailscale uses it in prod; server
  updated 2026): encrypted storage, per-access audit log, S3 backups.
- Matches the existing roadmap in
  `apprenticeship-cognabot/docs/jit-services-and-secrets.md` (the "medium term:
  secret-provider abstraction, env-first then backend" + "Tailscale-backed
  option: run setec as a Tailscale Service" steps). **This plan IS those steps.**

Hard rule from that doc, keep it: **resolve secrets in a narrow runtime config
layer at process startup — never via an LLM-facing tool/material.**

## Reference

- setec: <https://github.com/tailscale/setec> · API: <https://github.com/tailscale/setec/blob/main/docs/api.md>
  · server ops: <https://github.com/tailscale/setec/blob/main/docs/server.md>
  · grants/app-capabilities: <https://tailscale.com/docs/features/access-control/grants/grants-app-capabilities>
- Existing roadmap doc: `apprenticeship-cognabot/docs/jit-services-and-secrets.md`
- Current LINE wiring to replace:
  - Python: `practic-theory-implementation/scripts/somatic_scheduler_service.sh`
    (lifts `LINE_CHANNEL_ACCESS_TOKEN`/`LINE_DEFAULT_USER_ID` from the cognabot
    `.env`) and `src/practice_theory_implementation/escalation.py` (reads them
    from env via `_first_env`).
  - Cognabot: `apprenticeship-cognabot/docker-compose.yml` (`${LINE_CHANNEL_ACCESS_TOKEN}`
    interpolation) + `config/stonemonkey/.env`.

## Principle: env-first → setec fallback (no big bang)

Every secret read goes through a tiny provider that resolves **env var first,
then setec**. So nothing breaks during migration: today everything is env; as
setec comes up, the same code transparently starts resolving from it; `.env`
entries are deleted only after the setec path is verified.

```
get_secret("LINE_CHANNEL_ACCESS_TOKEN")
  1. os.environ / process.env  (local dev, current behaviour)  -> return if set
  2. setec HTTP API (if SETEC_URL configured)                  -> return if found
  3. None  (caller degrades gracefully, as escalation already does)
```

---

## Phase 1 — Secret-provider abstraction (no server yet)

Build the indirection in both solutions; behaviour identical to today (still
env), so this is safe to ship immediately.

### 1a. Python (`practic-theory-implementation`) — ✅ DONE 2026-06-21
Shipped: `src/practice_theory_implementation/secret_provider.py` (`get_secret`,
env→setec→default, in-process cache of setec hits only, best-effort, never logs
values); `escalation.py` resolves the LINE creds through it; `tests/
test_secret_provider.py` (11 tests) + existing escalation tests green. Behaviour
identical to today — setec path is dormant until `PRACTICE_SETEC_URL` is set
(Phase 3). setec wire format: POST `{url}/api/get`, header
`Sec-X-Tailscale-No-Browsers: setec`, body `{"Name", "Version": 0}`, response
`{"Value": base64, "Version"}`.


- New `src/practice_theory_implementation/secret_provider.py`:
  - `get_secret(name: str, *, aliases: tuple[str, ...] = (), default: str | None = None) -> str | None`
  - Resolution: env (name + aliases) → setec (if `PRACTICE_SETEC_URL` set) → default.
  - In-process cache; never log values; best-effort on setec errors (fall through).
  - setec fetch = HTTP GET to the tailnet setec service (see Phase 2 for URL/auth);
    keep the HTTP client tiny (httpx, already a dep), short timeout, cached.
- Refactor `escalation.py` `_first_env(...)` calls to
  `secret_provider.get_secret("PRACTICE_LINE_TOKEN", aliases=("LINE_CHANNEL_ACCESS_TOKEN",))`
  and the same for the user id. No behaviour change while env is set.
- Tests: env-hit returns env; setec-hit mocked; both-unset returns None; cache.

### 1b. TypeScript (`apprenticeship-cognabot`) — ✅ DONE 2026-06-21
Shipped: `packages/server/src/shared/services/secret-provider.ts` — `getSecret`
(async, env→setec→default, caches setec hits only, best-effort, never logs
values) plus `getSecretSync` (env-only, for the sync constructor /
`isConfigured()` seams). `LineChannel` resolves its three creds through the
provider: sync env path in the constructor (identical to today), async
`ensureConfigured()` fills any gap from setec and is awaited at the top of
`sendMessage`. `SETEC_URL` added to `config-schema.ts` (infrastructure) for the
Settings UI. Tests: `packages/server/tests/unit/secret-provider.test.ts` (12);
full server suite green (1137). setec dormant until `SETEC_URL` is set (Phase 3).
Note: webhook signature validation reads `channelSecret` synchronously — when
`LINE_CHANNEL_SECRET` migrates to setec (Phase 3), pre-warm with
`await channel.ensureConfigured()` at channel registration in `message-router`.


- Mirror in the server's config layer (where `config-schema.ts` /
  `routes-bun/config.ts` resolve runtime config). A `secretProvider.ts`:
  `getSecret(name, { aliases })` → `process.env` → setec → undefined.
- Cognabot already centralises config; thread secret reads through this provider
  rather than raw `process.env` for the credentials being migrated.

**Acceptance:** both solutions run exactly as now (env still set), tests green.

## Phase 2 — Stand up one `setec` server on the tailnet — ✅ DONE 2026-06-22

> **Runbook:** `docs/runbooks/setec-server-laputa.md` (executable steps + the
> build/network gotchas hit along the way).
>
> Live on laputa: patched setec binary (local Tink KEK, **no AWS** — see
> `setec-local-kek.patch`) at `~/setec/setec`, pm2-managed (`pm2 id 11 "setec"`,
> `pm2 save`d, launchd resurrect on boot). Node `setec` = `100.91.75.119`,
> serving `https://setec.tail82f84.ts.net`. DB encrypted at rest with
> `~/setec/state/kek.json` (AES-256-GCM, 0600); audit log writing to
> `~/setec/state/audit.log`. Tailnet grant added (`tailscale.com/cap/secrets`,
> all members, all actions, all secrets — solo-tailnet shape). Three LINE secrets
> loaded + sha-verified against the cognabot `.env`: `LINE_CHANNEL_ACCESS_TOKEN`,
> `LINE_CHANNEL_SECRET`, `LINE_DEFAULT_USER_ID`.
>
> Gotchas resolved (in runbook): native macOS build needs `CGO_ENABLED=1` (else
> pure-Go resolver fails DNS) + ad-hoc `codesign`; tsnet needs
> `Server.AuthKey = os.Getenv("TS_AUTHKEY")` wired in; **LuLu firewall** silently
> blocked the new binary's outbound to Tailscale control (the original "join
> hangs" cause) — allow `setec` in LuLu.


- Host: laputa (already on the tailnet, already hosts Neo4j/Qdrant). Run the
  `setec server` (Go binary). Decide state dir + enable **S3 backups** + the
  **audit log** file (see server.md).
- Expose it as a tailnet service (Tailscale Service / MagicDNS name, e.g.
  `setec.<tailnet>.ts.net`). Do **not** funnel it publicly.
- **Access control via tailnet grant**: write a policy grant so only the nodes
  that run the keeper / cognabot may read the relevant secrets (capability-based,
  least privilege). This is the "secret zero solved" piece — auth = tailnet
  identity, no token to distribute.
- Bootstrap: load the existing secrets into setec (name + value), e.g.
  `setec put LINE_CHANNEL_ACCESS_TOKEN`, etc. (CLI in the repo).
- Confirm: a tailnet node can `setec get` a secret; a non-granted node cannot.

## Phase 3 — Point the providers at setec + migrate

> **Status 2026-06-22:** Keeper (this repo) MIGRATED + verified. Cognabot code +
> config DONE + tests green; final deploy (rebuild image, bring up, live-verify
> LINE bot) + cognabot `.env` removal is the remaining user-driven step.
>
> **Keeper (DONE):** `scripts/somatic_scheduler_service.sh` now exports
> `PRACTICE_SETEC_URL=https://setec.tail82f84.ts.net` and no longer lifts LINE
> vars from the cognabot `.env`. Verified: the repo's own `get_secret` resolves
> both LINE creds from setec with env unset (sha-matched the source).
>
> **Cognabot (code/config DONE, deploy PENDING):** `docker-compose.yml` adds
> `SETEC_URL` (defaulted to the tailnet URL) to the server + daemon services and
> drops the `${LINE_*}` interpolation. `message-router.ts` made setec-aware:
> LINE registration now `await line.ensureConfigured()` *before* the sync
> `isConfigured()` gate (else a setec-only cred would never register) — this also
> pre-loads `channelSecret` so synchronous webhook validation works. Typecheck +
> lint clean, full server suite (1137) green. Container→setec reachability proven
> (Docker Desktop resolves the MagicDNS name and NATs out under laputa's tailnet
> identity → HTTP 200 + sha match from inside a throwaway container; no sidecar).
>
> **Remaining (user-driven):** rebuild the cognabot server+daemon images (so the
> new setec-aware code ships), `docker compose up`, confirm LINE push + webhook
> work against setec, THEN remove the 3 LINE keys from
> `config/stonemonkey/.env`. Backups taken: `~/setec/backups/{database,kek.json}.*`
> and `config/stonemonkey/.env.pre-setec.*`. NOTE: the compose change already
> stops forwarding `${LINE_*}` to the container, so the rebuilt (setec-aware)
> image is required on next `up` — an old image would lose LINE regardless of the
> `.env`. `LINE_CHANNEL_SECRET` is the one needing the pre-warm (now in place).

- Set `PRACTICE_SETEC_URL` (Python) and the cognabot equivalent so Phase-1
  providers resolve from setec when env is unset.
- For each migrated secret: verify the setec path returns the right value
  (env unset in a test process), THEN remove it from the `.env`.
- First secrets to migrate (shared/highest value):
  1. `LINE_CHANNEL_ACCESS_TOKEN`, `LINE_CHANNEL_SECRET`, `LINE_DEFAULT_USER_ID`
     (shared by escalation push + cognabot LINE bot — the live duplication).
  2. Model provider keys (codex / anthropic).
  3. Neo4j / Qdrant / embedding creds.
- Update the launchers: `somatic_scheduler_service.sh` stops lifting LINE vars
  from the cognabot `.env` once the provider resolves them from setec; cognabot
  `docker-compose.yml` stops interpolating the raw `${LINE_*}` for migrated keys
  (the server fetches at startup via the provider).

## Phase 4 — Hygiene

- Remove migrated keys from all `.env` files; keep `config/example/.env` as
  placeholders/routing only (per the jit doc).
- **Rotate** anything that lived in a committed/exposed file during the .env era.
- Document the grant + the secret names in `jit-services-and-secrets.md`
  (promote it from roadmap to "current").

## Open decisions (confirm at start)

1. setec server host — laputa assumed. State dir + S3 bucket for backups?
2. Tailnet grant shape — which nodes/tags may read which secrets (least
   privilege: keeper node, cognabot node).
3. setec service name / how Python+TS address it (MagicDNS vs tailnet IP).
4. Migration order beyond the LINE creds; whether to do codex/anthropic keys in
   the same pass.
5. Local-dev story: keep env-first so a dev box without tailnet/setec still runs
   off a local `.env` (the provider already supports this).

## Acceptance criteria

- One `setec` server on the tailnet, grant-locked, backups + audit on.
- Both solutions read all migrated secrets through the env-first→setec provider;
  no migrated secret remains in any tracked-or-ignored `.env`.
- LINE escalation push + cognabot LINE bot both work with the `.env` LINE keys
  removed (resolved from setec).
- No secret retrieval reachable from any LLM-facing tool/material.

---

*Origin: 2026-06-21 session. The escalate-when-unsure layer went live on LINE
using the cognabot `.env` LINE creds; this plan moves those (and the rest) into a
shared `setec` store so the secret currently duplicated across both solutions
lives once, tailnet-governed. Pick up here in a fresh session.*
