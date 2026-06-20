# Design: Escalate-When-Unsure

*Design doc — 20 June 2026 — status: proposed*

The autonomic loop now runs, self-evaluates, self-corrects, and self-ratifies to
`main` with no human in it. The remaining gap between *automated* and *magic you
don't have to think about* is this: when the loop hits something it cannot
resolve, is genuinely unsure about, or is about to do something irreversible, it
should **tap you on the shoulder** — and otherwise stay completely silent.

Silence has to mean *handled*. A tap has to mean *genuine need*. That is the
whole contract.

---

## 1. The problem: the system fails silently

Today the loop has three silent failure modes, and silence is exactly what makes
them dangerous to a "don't think about it" promise:

- **It gives up silently.** A Friction the Smoother can't resolve is retried a
  few times by `friction_reconcile` and then **tombstoned** — a real unresolved
  problem disappears into a closed record nobody sees.
- **It breaks silently.** The `CircuitBreaker` trips on repeated model/quota
  errors and the loop stops; the new load-gate refuses to ratify broken
  substrate. Both leave the system stuck with no signal out.
- **It spins silently.** We watched the loop harden its own `pm_read_pool` rule
  across frictions 666 → 681 → 690 → 694 — busy, locally-coherent, but *not
  converging*. From the outside that is indistinguishable from progress.

A magic box that fails silently isn't magic; it's a liability you discover late.
The fix is not more gates (those put you back *in* the loop). It is a thin,
**push-not-pull** channel that surfaces only the residue self-correction can't
handle.

## 2. Principles

- **Escalate at the *boundary* of self-correction, not during it.** The loop
  already self-corrects with bounded retries. Escalation fires where those bounds
  are *hit* (retry cap, breaker, non-convergence) — never on normal friction.
- **Quiet by default.** Zero notifications when things are fine is a feature, not
  an absence of one. Silence is the trust signal.
- **The LLM's *choice* to escalate is the confidence signal.** We don't build a
  confidence model. We give the Judge/Smoother an `escalate_to_user` affordance
  and let their judgement decide when they're guessing. Invoking it *is* "I'm
  unsure" — judgement stays in the LLM, where it belongs.
- **Notify, don't gate — except for the irreversible.** Most of the loop is
  additive, revertible substrate: surface it *after* (record + undo), never
  block. Reserve a hard *pre-action* gate for the small set of genuinely
  irreversible / high-stakes moves the user wants to be asked about.
- **Human *on* the loop, not *in* it.** Escalation is the inverse of the
  apprenticeship: normally the engagement offers situated awareness *to* the
  model; here the model offers a decision *back* to the human, but only at the
  rare edge of its competence. It's an **offer**, framed as one — never a demand.

## 3. The escalation taxonomy

Four trigger families, each mapped to where it's detected (deterministic code vs.
LLM judgement) and how it's handled (notify vs. gate):

| Family | Meaning | Detected by | Handling |
|---|---|---|---|
| **Stuck** | self-correction exhausted | deterministic detectors | notify |
| **Uncertain** | the LLM is guessing | `escalate_to_user` affordance | notify |
| **Not converging** | busy but not resolving | deterministic detectors | notify |
| **High-stakes** | about to do the irreversible | pre-action gate | **gate** |

### Stuck (deterministic)
- A Friction **tombstoned** by `friction_reconcile` after exhausting retries.
- The **CircuitBreaker** trips (loop halted — quota/auth/repeated model error).
- The janitor's **load-gate** refuses to ratify the same batch N passes running
  (broken substrate is live but can't become durable).
- Repeated **dispatch failures** (the `DISPATCH_FAILED` marker) beyond a count.

### Uncertain (LLM judgement)
- The Judge faces a genuinely borderline quality concern (stall vs. patience) and
  would be guessing.
- The Smoother is handed a Friction it cannot resolve with a bounded amendment,
  or where the right fix is ambiguous or sweeping. Today it guesses or no-ops
  (→ silent tombstone). Instead it **escalates rather than guess or stall.**

This is the most important change: it converts the silent stall→tombstone path
into an explicit, rare *"I need you"*.

### Not converging (deterministic)
- The same substrate id is amended **K times in a window** while the triggering
  concern/friction **still recurs** → "non-converging self-amendment on X".
- An evaluation **concern recurs after** a Smoother fix attempt → "the fix didn't
  take".

### High-stakes (pre-action gate)
- Irreversible **external** actions: sending mail, issuing a calendar change,
  moving money (the somatic practices already gate these per-practice — this
  generalizes the principle and routes the confirmation through one channel).
- **Destructive substrate** ops: tombstoning a core/governing invariant, deleting
  a bundle, rewriting a teleo-affective objective.
- The user defines the high-stakes allowlist; everything off it is notify-only.

## 4. Architecture

Mirrors the self-evaluating-practices split exactly: deterministic detectors +
an LLM affordance + a routing/dispatch layer + a policy. Components:

1. **The `Escalation` record** — a new first-class trail object, sibling to
   `Friction`: `{kind, severity, source, dedup_key, evidence, state,
   created_at, notified_at, acknowledged_at, resolved_at, user_stance}`.
   Idempotent on `dedup_key` so a persistent condition produces **one** open
   escalation, not a stream.
2. **Deterministic detectors** — `escalation_routing.py` (sibling of
   `practice_evaluation_routing.py`): pure scans over the trail/state for the
   *stuck* and *not-converging* families. No LLM. Emit idempotent Escalations.
3. **The `escalate_to_user` affordance + material** — afforded to the Judge,
   Smoother, and scheduled practitioners. Records an Escalation with the reason,
   evidence, and a proposed-options list. Bundle understanding/rules guide *when*:
   *"escalate rather than guess or stall when the resolution is ambiguous,
   sweeping, or beyond a bounded amendment."*
4. **The dispatch + policy loop** — an idle-triggered loop in `autonomic_runner`
   (sibling of `_run_invariant_audit_loop` / `_run_practice_evaluation_loop`):
   reads open Escalations, applies the severity / coalescing / suppression /
   quiet-hours policy, and emits notifications through the **sink**.
5. **The notification sink** — pluggable: `PushNotification` (phone) for the top
   tier, a coalesced email digest for the middle, the status dashboard (pull) for
   the rest. One interface, swappable backends.
6. **The response path** — `acknowledge_escalation(id, stance, steer?)`: the
   human's rare input is recorded on the Escalation and, when they give a steer,
   written as durable guidance/context the loop apprentices from. This closes the
   loop — the human's exceptional judgement becomes substrate, so the *same*
   escalation shouldn't recur.

Hooks into existing terminal states (where the silent failures already are):
- `friction_reconcile` tombstone path → emit a *stuck* Escalation instead of
  silently tombstoning.
- `CircuitBreaker.trip` / `observe_dispatch` stop-signal → emit a *critical*
  Escalation (the loop is down).
- The janitor load-gate refusal (repeated) → emit a *stuck* Escalation.

Determinable/judgement boundary held at every step: detect-stuck (deterministic)
→ decide-uncertain (LLM affordance) → notify (deterministic policy) → human
stance (judgement) → steer-becomes-guidance (the loop apprentices).

## 5. Notification & severity policy (the make-or-break)

"Magic you don't think about" dies on alert fatigue. The policy is therefore
*ruthlessly quiet*:

| Tier | Examples | Channel | Timing |
|---|---|---|---|
| **Critical — "it stopped"** | breaker tripped, quota exhausted, broken substrate live & un-ratifiable | **push (phone)** | immediate, any hour |
| **Attention — "I gave up / I'm unsure"** | tombstoned friction, Smoother escalation, non-convergence | push **coalesced** (≤1/item/day) or daily digest | respect quiet hours |
| **FYI — "for the record"** | "the loop made 23 self-amendments today" | dashboard / weekly digest | **never pushes** |

Guarantees:
- **Dedup**: one open Escalation per `dedup_key`; a persistent condition never
  re-pushes until its state changes or the human acts.
- **Coalesce**: many same-family escalations in a window collapse into one
  notification with a count.
- **Suppress-after-notify**: once notified, an item is silent until its state
  changes (resolved, re-triggered with new evidence, or escalated a tier).
- **Quiet hours / DND**: only Critical breaks them.
- **Self-evaluation of the channel**: the escalation practice is itself subject
  to the §self-evaluating-practices regime — if it ever over- or under-notifies,
  that's a measurable quality concern the loop can surface and the Smoother can
  tune. The notifier watches itself.

## 6. The human response — a thin two-way channel

An escalation is an **offer**, and the reply should cost the human almost
nothing:
- **Acknowledge / "leave it"** — the loop records the stance and stops
  re-surfacing; if it was a *stuck* item, it stays tombstoned with the human's
  blessing on the record.
- **"I'll handle it"** — the loop steps back from that target (won't keep
  re-amending) and marks it human-owned.
- **A one-line steer** — the highest-value reply: the human's rare judgement
  ("prefer X over Y", "this concern is acceptable, stop flagging it"). The steer
  is written as durable guidance the loop apprentices from, so the escalation
  *teaches* and shouldn't recur.

This is what keeps the human *on* the loop: their input is rare, cheap, and
compounding — each exceptional decision becomes part of the situated awareness
the loop carries forward.

## 7. What this is *not*

- Not a dashboard you have to check (that's pull; this is push).
- Not a confidence model (the affordance invocation is the signal).
- Not a new gate on routine work (notify-don't-gate, except the irreversible).
- Not chatty (quiet-by-default; one item, one notification, until state changes).

## 8. Open decisions

1. **Notification backend** — ✅ **LINE.** A push to the phone is exactly the
   "tap on the shoulder": glance, ignore, or reply. Implementation: a LINE
   **Messaging API** bot push (LINE Notify is being sunset), an HTTP POST with a
   channel token to the user's LINE — the escalation sink's primary backend.
   Critical pushes immediately; Attention coalesces into a (still LINE) digest;
   FYI stays on the dashboard. Bonus: LINE is two-way, so the §6 response path
   (acknowledge / steer) can come back as a LINE reply the loop ingests — the
   whole offer-and-reply channel lives in one app on your phone. Open sub-point:
   token/secret storage (env/keychain, like the other service creds) and a small
   inbound webhook for replies.
2. **Quiet hours + digest time** — user-configured window; one daily digest time.
3. **High-stakes allowlist** — exactly which autonomous actions gate vs. notify.
   Default: external sends + destructive substrate ops gate; all else notifies.
4. **Non-convergence thresholds** — K amendments / window before "not converging"
   fires; tuned to avoid false alarms on legitimately iterative hardening.
5. **Does `escalate_to_user` pause the enacting practice** (await a stance) or
   fire-and-continue? Lean fire-and-continue for notify; await only for the
   high-stakes gate.

## 9. Build phasing

1. **Surface the silent terminal states (highest value, lowest risk).**
   ✅ **Mostly done.** `Escalation` trail record (idempotent on `dedup_key`) +
   `escalation.py` (emit + LINE sink, env-gated on `PRACTICE_LINE_TOKEN` /
   `PRACTICE_LINE_TO`). Hooks: the circuit-breaker halt (`trip_and_stop` →
   CRITICAL, pushes now) and the `friction_reconcile` tombstone (→ ATTENTION,
   recorded). CRITICAL pushes immediately; ATTENTION is recorded for the digest.
   *Deferred:* the janitor load-gate-refusal hook (the janitor is bash — needs a
   small marker→Python bridge), and wiring LINE creds to actually push (built,
   not yet live — same pattern as auto-ratify before the token).
2. **The dispatch + policy loop** — severity tiers, dedup, coalescing, quiet
   hours, the FYI digest. Makes it quiet-by-default.
3. **`escalate_to_user` for the Smoother/Judge** — convert silent stall→tombstone
   into explicit "I'm unsure", with bundle guidance on when. The richest
   "unsure" signal.
4. **Non-convergence detection** — the deterministic "spinning on its own tail"
   detector.
5. **The response path** — acknowledge / steer, and the steer-becomes-guidance
   feedback. Closes the teaching loop.
6. **High-stakes pre-action gate** — generalize the per-practice external-action
   gating into the escalation channel for the irreversible allowlist.

---

*Continues the arc: self-evaluating practices gave the loop a measure of itself;
the janitor gave it durable autonomy; this gives it the judgement to know when
its own competence has run out — and the discipline to bother you only then. The
last piece of "ask, and it's just done."*
