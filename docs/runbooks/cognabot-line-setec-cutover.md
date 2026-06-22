# Runbook — cut cognabot's LINE creds over to setec (Phase 3, cognabot side)

Finishes Phase 3 for apprenticeship-cognabot: the LINE bot stops reading its
credentials from `config/stonemonkey/.env` and resolves them from the shared
`setec` store instead. Run from `~/develop/home/apprenticeship-cognabot`.

> ⚠️ **Do NOT use `make restart` or `make down`.** Both run `stop-data`
> (`docker compose stop`), which bounces the shared **neo4j + qdrant** containers
> that practic-theory-implementation owns and depends on. Restart only the native
> server+daemon: `pm2 restart cognabot-server cognabot-daemon` (pm2 mode) or
> `make stop-native start-native` (direct mode). `make up` is safe — `start-data`
> is `docker compose up -d`, idempotent, so it will not restart already-running
> data containers.

**Already in place (this session):**
- `SETEC_URL=https://setec.tail82f84.ts.net` added to `config/stonemonkey/native.env`
  (the native server/daemon source `.env` then `native.env` with `set -a`).
- `message-router.ts` is setec-aware: LINE registration `await`s
  `ensureConfigured()` (env→setec) before the sync `isConfigured()` gate, so a
  setec-only credential still registers and `channelSecret` is loaded before any
  webhook validation.
- The 3 LINE keys are still in `.env` (fallback). Backup:
  `config/stonemonkey/.env.pre-setec.<ts>`.
- Runtime fact: `dev-server.sh` does `exec bun run src/...` → runs from source,
  **no image build needed**; a restart picks up the new code.

**Scope — all three LINE keys are now safe to remove from `.env`:**
| Key | Remove? | Why |
|-----|---------|-----|
| `LINE_CHANNEL_ACCESS_TOKEN` | ✅ yes | only `LineChannel` reads it at runtime (provider-routed) |
| `LINE_CHANNEL_SECRET` | ✅ yes | only `LineChannel` reads it (pre-warm in place) |
| `LINE_DEFAULT_USER_ID` | ✅ yes | its 3 direct readers (`resolver-registry.ts`, `outreach-tools.ts`, `daemon/notifier.ts`) now resolve via `getSecret('LINE_DEFAULT_USER_ID')` (env-first → setec) |

---

## Step 0 — pre-flight (confirm store + secrets reachable)

```bash
# setec answers and the two creds are present (200 each). From the cognabot dir:
for k in LINE_CHANNEL_ACCESS_TOKEN LINE_CHANNEL_SECRET; do
  curl -sS --max-time 15 -o /dev/null -w "$k -> %{http_code}\n" \
    -X POST -H "Sec-X-Tailscale-No-Browsers: setec" -H "Content-Type: application/json" \
    -d "{\"Name\":\"$k\",\"Version\":0}" https://setec.tail82f84.ts.net/api/get
done   # expect 200, 200
```

## Step 1 — start cognabot with the new code, `.env` UNCHANGED (baseline)

This proves the setec-aware code didn't break anything while creds still come from
env (env-first wins, so setec isn't consulted yet).

```bash
# If neo4j/qdrant are already up, start only the native side:
make start-native        # (or: make pm2-up for autorestart — also idempotent on data)
# If the data services are NOT running yet, `make up` is safe (idempotent up -d).
make status              # wait until server is healthy
grep -i "LINE.*registered" /tmp/cognabot-server.log    # expect: "registered (env/setec)"
```

Functional baseline: from your phone, send the LINE bot a message → expect its
normal reply. (Still using `.env` values.) If this fails, it's the code change —
stop and check `make server-logs`; do NOT proceed to Step 2.

## Step 2 — migrate all three LINE keys (remove from `.env`, resolve from setec)

```bash
# Remove (or comment) all three lines from config/stonemonkey/.env:
#   LINE_CHANNEL_ACCESS_TOKEN=...
#   LINE_CHANNEL_SECRET=...
#   LINE_DEFAULT_USER_ID=...
# (the values live in setec + the .env.pre-setec backup)

# Restart ONLY the native server+daemon (does not touch neo4j/qdrant):
pm2 restart cognabot-server cognabot-daemon    # pm2 mode
# — or, direct mode:  make stop-native start-native
make status
grep -i "LINE.*registered" /tmp/cognabot-server.log    # still "registered (env/setec)"
```

**Verify the setec path is live** — one phone round-trip exercises all three:
- Send the bot a message from LINE → it must reply.
  - Inbound webhook accepted ⇒ `LINE_CHANNEL_SECRET` resolved from setec (validation).
  - Reply delivered ⇒ `LINE_CHANNEL_ACCESS_TOKEN` resolved from setec (push).
- Trigger an outbound notify (daemon notification or `notify_user`) with no explicit
  `user_id` ⇒ exercises `LINE_DEFAULT_USER_ID` via the provider.
- Cross-check the audit log on laputa shows fresh `get` actions:
  `tail -f ~/setec/state/audit.log` (look for the three names around your test).

## Step 3 — done

All three LINE keys are off disk and resolved from setec by both solutions (keeper
already migrated). No LINE secret remains in `config/stonemonkey/.env`.

## Rollback (if anything misbehaves)

```bash
cp config/stonemonkey/.env.pre-setec.<ts> config/stonemonkey/.env
pm2 restart cognabot-server cognabot-daemon    # or: make stop-native start-native
```

---

## Follow-ups to fully close Phase 3 / 4

- Migrate the remaining higher-value secrets the plan lists (model provider keys:
  anthropic/codex; then Neo4j/Qdrant) — `setec put` each, confirm the provider
  resolves it, remove from `.env`.
- Phase 4: rotate any credential exposed during the `.env` era; promote
  `apprenticeship-cognabot/docs/jit-services-and-secrets.md` from roadmap to
  "current" with the grant + secret names.
