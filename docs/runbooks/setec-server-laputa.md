# Runbook — stand up `setec` on laputa (Phase 2)

Executable steps for the server half of `docs/plans/setec-secrets-setup.md`.
Phase 1 (the env-first→setec providers) is already shipped in both solutions and
dormant until `SETEC_URL` / `PRACTICE_SETEC_URL` is set (Phase 3). This runbook
brings up the one shared `setec` server, grant-locks it, and loads the first
secrets. Run it on **laputa** (already on the tailnet, already hosting
Neo4j/Qdrant).

> Nothing here touches the running apps. The providers don't resolve from setec
> until Phase 3 flips the URL on, so you can build and verify the server in
> isolation first.

---

## 0. Decisions to settle before you start

Fill these in; the commands below reference them as `<...>` placeholders.

| # | Decision | Default / suggestion |
|---|----------|----------------------|
| 1 | Tailnet name (MagicDNS suffix) | `<tailnet>.ts.net` — find via `tailscale status --json \| jq -r .MagicDNSSuffix` |
| 2 | setec hostname (becomes the MagicDNS node name) | `setec` → `https://setec.<tailnet>.ts.net` |
| 3 | State dir on laputa | `/var/lib/setec` (or `$HOME/setec-state` for a user-level run) |
| 4 | **AWS KMS key ARN** (production encryption — see note) | *required for prod mode* |
| 5 | S3 backup bucket + region | e.g. `home-setec-backup` / `ap-northeast-1` |
| 6 | Tailscale tags for the reader nodes | `tag:keeper` (laputa/keeper), `tag:cognabot` (cognabot host) |

### Decision taken (2026-06-21): local Tink KEK, no AWS

We chose **local-KEK** over AWS KMS and over `--dev`. setec upstream only wires
AWS KMS for production, so this needed a small patch (`docs/runbooks/
setec-local-kek.patch`, ~40 lines on `cmd/setec/setec.go`): a `--local-kek
<path>` flag that loads-or-creates a Tink AES-256-GCM keyset and uses it as the
DB encryption key. The keyset is stored **cleartext at 0600** — protection is the
FileVault-encrypted disk + file perms, so there is **no passphrase and no cloud
KMS = no secret-zero**, matching the plan's whole rationale. The DB is genuinely
AES-256-GCM encrypted at rest (a foreign keyset cannot decrypt it — verified by
`setec-localkek_test.go`). S3 backups are dropped (they were the AWS-coupled
part); back up `state/` to your existing backup instead.

**Status on laputa (done):** Go 1.26 installed (brew); patched binary built
(cross-compiled darwin/arm64 in Docker to dodge a flaky host IPv6 route to the Go
proxy) and installed at `~/setec/setec` (version string ends `+dirty`); state dir
`~/setec/state/`; KEK generated at `~/setec/state/kek.json`; launcher
`~/setec/start.sh`. The server reaches the tailnet-login step cleanly but needs a
`TS_AUTHKEY` to join (this tsnet build doesn't print the interactive URL).
**Remaining = Tailscale-admin actions only** (see "Hand-off" below).

To rebuild the binary later (any host with Docker + the cloned setec repo):
```bash
git clone https://github.com/tailscale/setec && cd setec
git apply /path/to/setec-local-kek.patch
docker run --rm -v "$PWD":/src -w /src \
  -e GOOS=darwin -e GOARCH=arm64 -e CGO_ENABLED=0 -e GOFLAGS=-mod=mod \
  golang:1.26 go build -o setec-darwin ./cmd/setec
```

### (Historical) why upstream production mode requires AWS KMS

setec protects its local encrypted DB with a key fetched from **AWS KMS** (ARN via
`--kms-key-name`); production needs AWS API access (IAM role or env creds) plus an
S3 bucket for backups. This reintroduces a small AWS dependency on the *server
host only*. It is **not** a "secret zero" for clients — client access is still
pure tailnet identity (the deciding rationale holds) — but the laputa host needs
AWS credentials to KMS + S3. There is a `--dev` mode that uses a dummy static key
and **no** AWS; it is explicitly **not secure for production** (use only to smoke-
test the integration end to end before wiring KMS).

If you'd rather avoid AWS entirely, that's a real fork in the plan — raise it
before Phase 3. The rest of this runbook assumes the KMS path (what the plan's
"production-grade, backups + audit" acceptance criterion implies), with a `--dev`
shortcut called out for the dry run.

---

## Hand-off — finish the join (local-KEK path, laputa)

Everything that doesn't need the Tailscale admin console is done. Remaining steps,
in order:

**A. (you, console)** Admin console → Settings → Keys → **Generate auth key**.
Untagged is fine on this single-user tailnet; leave it non-ephemeral so the node
persists; single-use is enough. Copy the `tskey-auth-…`.

**B. (join)** Run the launcher once with that key — do it via the `!` prefix so the
key stays out of the assistant's context:
```
! TS_AUTHKEY=tskey-auth-xxxxxxxx ~/setec/start.sh
```
It joins as node `setec`, gets a cert for `setec.tail82f84.ts.net`, and starts
serving. Leave it running (Ctrl-C to stop; we pm2-ify it after verifying). Tell me
when it's up and I'll read the node's tailnet IP from `tailscale status`.

**C. (you, console)** Add the access grant (I'll fill in the IP after step B). On a
solo tailnet where the keeper, cognabot, and setec all run on laputa under one
identity, a single user-scoped grant is the honest shape — tag-based
least-privilege buys no isolation when there's one identity and one host:
```jsonc
"grants": [
  { "src": ["autogroup:member"],
    "dst": ["<setec-node-ip>"],
    "app": { "tailscale.com/cap/secrets": [
      { "action": ["get", "info", "put", "create-version", "activate", "delete"],
        "secret": ["*"] } ] } }
]
```

**D. (me)** Bootstrap the LINE creds from `~/develop/home/apprenticeship-cognabot/
config/stonemonkey/.env` (all 3 keys present), `setec get` to verify, then start it
under pm2 (`pm2 start ~/setec/start.sh --name setec`) for durability.

---

## 1. Install setec on laputa

```bash
# Go toolchain present on laputa? `go version`. If not, install Go first.
go install github.com/tailscale/setec/cmd/setec@latest
# binary lands in $(go env GOPATH)/bin/setec — put that on PATH
setec --help
```

## 2. (Dry run, optional) prove the integration in --dev mode

No AWS, insecure key — just to confirm the binary joins the tailnet and the
HTTP API answers before you provision KMS/S3.

```bash
sudo mkdir -p /var/lib/setec && sudo chown "$USER" /var/lib/setec
TS_AUTHKEY=tskey-auth-xxxxx setec server \
  --dev \
  --hostname=setec-dev \
  --state-dir=/var/lib/setec-dev
```

In another shell, from laputa or any tailnet node:

```bash
setec -s https://setec-dev.<tailnet>.ts.net put dev/hello
# (paste a value, Ctrl-D)
setec -s https://setec-dev.<tailnet>.ts.net get dev/hello
```

Tear the dev node down once that round-trips (delete the dev node from the admin
console and `rm -rf /var/lib/setec-dev`).

## 3. Provision AWS (production path)

- Create a **KMS key** (symmetric, ENCRYPT_DECRYPT). Note its ARN → decision #4.
- Create an **S3 bucket** for backups (decision #5); block public access.
- Give laputa credentials to use both: an IAM role if laputa is EC2, otherwise an
  IAM user whose access key is exported to the setec process environment
  (`AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_REGION`), or via
  `aws-vault exec`. Least-privilege policy: `kms:Decrypt`/`kms:Encrypt` on the one
  key, `s3:PutObject`/`s3:GetObject`/`s3:ListBucket` on the one bucket.

## 4. Generate a tailnet auth key

Admin console → Settings → Keys → generate an **auth key**. Tag it with the
server's tag (e.g. `tag:setec`) so the node comes up pre-tagged and reusable if
you re-provision. This `TS_AUTHKEY` is used only on first run; afterwards setec
uses cached creds in the state dir.

## 5. Run the server (production)

```bash
sudo mkdir -p /var/lib/setec && sudo chown "$USER" /var/lib/setec
TS_AUTHKEY=tskey-auth-xxxxx \
AWS_REGION=<region> \
setec server \
  --hostname=setec \
  --state-dir=/var/lib/setec \
  --kms-key-name=arn:aws:kms:<region>:<acct>:key/<id> \
  --backup-bucket=<bucket> \
  --backup-bucket-region=<region>
```

What this gives you (acceptance criteria):
- MagicDNS endpoint `https://setec.<tailnet>.ts.net` (the value of `SETEC_URL`).
- **Audit log**: appended to `<state-dir>/audit.log` automatically (every access).
- **Backups**: encrypted snapshot to S3 up to once/minute when contents change.

### Make it durable (pick one; laputa ops are make+pm2)

**pm2** (matches the existing keeper/MCP ops):
```bash
pm2 start setec --name setec -- server \
  --hostname=setec --state-dir=/var/lib/setec \
  --kms-key-name=arn:aws:kms:<region>:<acct>:key/<id> \
  --backup-bucket=<bucket> --backup-bucket-region=<region>
pm2 env 0  # confirm TS_AUTHKEY (first run only) + AWS_* are present
pm2 save
```
Put `TS_AUTHKEY` (first boot) and `AWS_*` in pm2's env, not in the repo. After the
first successful join you can drop `TS_AUTHKEY`.

**systemd** alternative: a unit with `Environment=AWS_REGION=...`, an
`EnvironmentFile=` (mode 600) for the AWS creds, `ExecStart=/…/setec server …`,
`Restart=on-failure`.

## 6. Lock it down — tailnet ACL grant

Edit the tailnet policy (admin console → Access controls). Three grants:
admin = full control; the two reader nodes = `get`+`info` only, scoped to the
secret name prefixes they actually use. Replace `<setec-ip>` with the setec
node's tailnet IP (`tailscale status` shows it) or use `tag:setec` as `dst`.

```jsonc
"grants": [
  // Admins (your laptop) manage all secrets.
  {
    "src": ["autogroup:admin"],
    "dst": ["tag:setec"],
    "app": {
      "tailscale.com/cap/secrets": [
        { "action": ["get", "info", "put", "create-version", "activate", "delete"],
          "secret": ["*"] }
      ]
    }
  },
  // Keeper node (practic-theory-implementation): read only what it needs.
  {
    "src": ["tag:keeper"],
    "dst": ["tag:setec"],
    "app": {
      "tailscale.com/cap/secrets": [
        { "action": ["get", "info"],
          "secret": ["LINE_CHANNEL_ACCESS_TOKEN", "LINE_DEFAULT_USER_ID",
                     "PRACTICE_LINE_TOKEN", "PRACTICE_LINE_TO"] }
      ]
    }
  },
  // Cognabot node: LINE + its provider/model + infra creds (scope as migrated).
  {
    "src": ["tag:cognabot"],
    "dst": ["tag:setec"],
    "app": {
      "tailscale.com/cap/secrets": [
        { "action": ["get", "info"],
          "secret": ["LINE_*", "ANTHROPIC_API_KEY", "OPENAI_API_KEY",
                     "NEO4J_PASSWORD", "QDRANT_API_KEY"] }
      ]
    }
  }
]
```

Tag the nodes accordingly (admin console device settings, or in the auth keys
used to bring them up): laputa/keeper → `tag:keeper`, the cognabot host →
`tag:cognabot`. Action vocabulary (from setec's ACL): `get`, `info`, `put`,
`create-version`, `activate`, `delete`. Readers get only `get`+`info`.

## 7. Bootstrap the first secrets

Load the live duplication first (the LINE creds shared by escalation push +
cognabot bot). Run from an admin node. `setec put` reads the value from stdin so
it never lands in shell history.

```bash
export SETEC_SERVER=https://setec.<tailnet>.ts.net   # or pass -s each time

# canonical names + the project-wide aliases the providers already check
printf %s "$LINE_TOKEN_VALUE"   | setec put LINE_CHANNEL_ACCESS_TOKEN
printf %s "$LINE_USERID_VALUE"  | setec put LINE_DEFAULT_USER_ID
printf %s "$LINE_SECRET_VALUE"  | setec put LINE_CHANNEL_SECRET
```

Source values: pull them from the current `apprenticeship-cognabot/config/
stonemonkey/.env` (the file the launchers lift today). Don't echo them.

The providers resolve `PRACTICE_LINE_TOKEN` with alias `LINE_CHANNEL_ACCESS_TOKEN`
(Python) and `LINE_CHANNEL_ACCESS_TOKEN` directly (cognabot), so storing under the
`LINE_CHANNEL_ACCESS_TOKEN` / `LINE_DEFAULT_USER_ID` names covers both. Later
passes: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, then Neo4j/Qdrant creds.

## 8. Verify access control

```bash
# Granted node (keeper or cognabot) — succeeds:
setec -s https://setec.<tailnet>.ts.net get LINE_CHANNEL_ACCESS_TOKEN

# A non-granted node (or one without the tag) — must 403:
setec -s https://setec.<tailnet>.ts.net get LINE_CHANNEL_ACCESS_TOKEN
#   -> expect "permission denied"
```

Confirm `<state-dir>/audit.log` recorded both attempts, and that an S3 object
appeared in `<bucket>`.

---

## Done = Phase 2 acceptance

- [ ] `setec server` durable on laputa (pm2/systemd), reachable at
      `https://setec.<tailnet>.ts.net`.
- [ ] KMS-encrypted state, `audit.log` writing, S3 backups landing.
- [ ] Grant in the policy: admin full; `tag:keeper` + `tag:cognabot` get/info on
      their scoped prefixes; an untagged node is denied.
- [ ] LINE creds loaded; granted `setec get` returns them.

## Next — Phase 3 (separate pass, gated)

For each secret: set `PRACTICE_SETEC_URL` (Python) / `SETEC_URL` (cognabot) on the
respective host, verify the provider returns the right value **with the env var
unset in a throwaway process**, then remove it from the `.env`. Update the
launchers (`scripts/somatic_scheduler_service.sh` stops lifting the LINE vars;
cognabot `docker-compose.yml` stops interpolating `${LINE_*}` for migrated keys).
Then Phase 4: rotate anything that lived in a committed/exposed `.env`, and
promote `apprenticeship-cognabot/docs/jit-services-and-secrets.md` from roadmap to
current with the grant + secret names. See the plan for the full sequence.
