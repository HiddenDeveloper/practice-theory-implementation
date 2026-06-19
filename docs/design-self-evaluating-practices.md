# Design: Self-Evaluating Practices

*Design doc — 19 June 2026 — status: proposed*

How a practice bundle comes to carry its own measure of whether it is delivering
its objective, so the autonomic loop can find — and smooth — quality friction
that today's triage is structurally blind to. No human in the loop.

---

## 1. The problem

The Judge/Smoother loop is caught up and finding nothing, yet a practice can be
going nowhere. The live example: the scheduled `stock_investor` practice for
`proof_fund_001` runs hourly, and every pass is mechanically flawless — it reads
state, fetches a live snapshot, records evidence and valuation, records a
`hold`/`watch` decision with a proper mandate check, writes a report, records
follow-ups, and closes the session. The dashboard reads `judge_inbox: 0,
smoother_inbox: 0, unaddressed_friction: 0`. And yet the fund is 95% idle cash,
the same carried-forward homework is deferred every cycle, and a ledger drift is
re-disclosed in `measurement_gaps` on every valuation without ever being fixed.

The cause is structural. `judge_triage.py` clears each closed enactment through
five deterministic detectors, and the **only** one that escalates a somatic
enactment to the Judge LLM is `recorded_step_error` — a material that returned
`{"error": ...}`. A practice whose every step succeeds falls straight through
`clean_success` to CLEAN, and the Judge never looks at it.

The blind spot, stated generally:

> Triage inspects whether a **single enactment mechanically succeeded**. A
> practice can produce a stream of locally-clean enactments and still **fail to
> deliver its objective** — stagnation, drift faithfully reported but never
> acted on, decisions that never change anything. No step errors, no contract
> violates, so neither attention loop ever fires.

A stock-specific invariant would be whack-a-mole. The fix has to be **generic**:
it must work for any practice bundle. But "generic" runs into a wall — *quality
is practice-relative*. `morning_briefing` repeating its shape daily is the
practice working; `stock_investor` repeating hourly while idle is a stall.
Generic shape-detection cannot tell those apart. **Judgement needs a specific
object to judge, and that object has to come from the practice itself.**

## 2. The idea in one line

**Every practice bundle carries a required `evaluation` layer — its own statement
of how to tell whether it is delivering its objective. The Judge runs it each
cycle; the Smoother smooths what it finds; both run with no human in the loop.**

## 3. Principles this must honour

- **The determinable/judgement boundary is the code/LLM boundary.** Detection of
  the determinable is deterministic; only genuine judgement spends an LLM.
- **Risks (and now, success criteria) belong in the bundle.** A practice's
  understanding, rules, and teleo-affective already name its purpose and risks.
  The measure of the practice is derived from there, not invented elsewhere.
- **No human in the loop.** The autonomic maintenance cycle finds and fixes
  quality friction with no person required. Oversight is *relocated* into
  substrate (trail + invariants + sandbox + the Judge re-examining authoring),
  not removed.
- **Trust rests on the trail.** Every measurement, finding, and fix is an
  inspectable enactment.

## 4. Practices vs. modes (the corrected model this rests on)

Judge, Smoother, and practice_management are **all practices** — bundles enacted
by LLMs. They differ on one axis:

- **Somatic** — a human *may* be in the loop. practice_management is somatic:
  authoring substrate is the kind of thing a human may want to steer, so it is
  gated to a mode where a person can be present.
- **Autonomic** — no human, ever. Judge and Smoother are autonomic.

This axis is load-bearing for the whole design. An autonomic practice cannot
"enact" a somatic one to borrow its capability — that would either drag a
human-in-the-loop practice into the no-human loop or run it stripped of the
human it is gated to expect. Capability is shared through **pooling**, not
through one practice enacting another (see §8).

## 5. The `evaluation` bundle layer

A practice declares how it wants to be judged, as a first-class layer alongside
`understanding`, `rules`, `teleo_affective`, and `affordances`.

- **Required, but honest deferral is allowed.** A bundle must carry an
  `evaluation` layer. Where a practice is genuinely not-yet-evaluable, the layer
  must say so explicitly (`not-yet-evaluable, because …`) — an inspectable
  standing state the loop carries as a TODO, never silent absence. This mirrors
  the system-wide ethos of recording the gap rather than inventing data.
- **Traceable to the teleo-affective objective.** The criteria must exercise the
  practice's *declared* purpose. An `evaluation` layer that does not is a
  vacuous evaluator — itself a friction. This is the cheap answer to "who
  evaluates the evaluators": coverage of the teleo-affective objective is
  checkable.
- **Declarative data, not code.** The layer is a spec the generic engine
  interprets — never a hand-authored executable. (The one piece of evaluation
  *code*, the engine, is written once as infrastructure; see §6.)

What an eval-spec can express (all optional, composed):

| Signal | Example for `stock_investor` |
|---|---|
| Affordance coverage | did the pass read state + fetch a live snapshot before deciding? |
| Outcome-bearing steps | did decisions ever produce orders / state changes, or only `hold`? |
| Follow-up closure rate | are carried-forward items closing, or only re-deferring? |
| Self-disclosed-gap recurrence | is the same `measurement_gap` re-reported N passes running? |
| Threshold checks | cash deployed vs. mandate `minimum_cash_pct`; idle-pass count |
| LLM rubric (fuzzy only) | "does the decision rationale actually engage the live evidence?" |

Most signals are computable from the trail with **zero tokens**. The LLM rubric
is reserved for criteria that genuinely cannot be reduced to telemetry, and is
run by the engine as a scoped sub-evaluation.

## 6. Two-part test suite

The practice owns a suite in two parts, catching different failures:

| | **Unit suite** | **System suite** |
|---|---|---|
| Tests | the practice's *materials* (deterministic I/O) + that the bundle composes/projects | the practice, end-to-end, delivering its objective |
| Nature | deterministic, repeatable, assert-equals | exercise + **evaluate** (the eval-spec is its assertion layer) |
| When | pre-flight / CI / on-amend | continuous (real trails) + on-amend (sandboxed exercise) |
| Catches | broken machinery before it runs | behavioural / quality drift in live operation |
| Already exists? | partly (`tests/test_morning_briefing_materials.py`, …) | no |

The crucial realisation: a practice's core actor is an LLM exercising judgement
over non-deterministic live data, so the system test **cannot** be assert-equals.
It is necessarily *exercise + evaluate*, and the *evaluate* half **is the
eval-spec the Judge runs**. The test suite subsumes the eval-spec rather than
competing with it.

A bundle is mostly *not* code (it is situated-awareness prose + the enacting
LLM), so "unit-test the bundle" means test the *materials it reaches* and
*validate it projects*. The judgement-laden core is unreachable by units — only
the system evaluation reaches the delivered objective.

### When each runs (the one correction worth stating loudly)

Do **not** have the Judge trigger a fresh live enactment every cycle — for
`stock_investor` that mutates the real fund and could submit orders; for
`correspondent` it writes drafts into the user's mailbox. Side effects and cost
both rule it out. Instead:

- **Continuous (Judge, every cycle): evaluate the *real production trail*.** The
  scheduled passes already exercised live data in normal operation; the Judge
  runs the eval-spec over what the practice actually did. No extra side effects,
  measures real behaviour, cheap. *This is "the system test the Judge calls."*
- **On-amend / CI: a sandboxed live-exercise run.** When the bundle changes,
  drive the amended practice against fixtures or live data in a **sandbox**
  (throwaway session, `proof_fund_test`, dry-run order/draft materials, no real
  sends) and evaluate the result, to catch regressions before they go live.
  Bounded to changes, isolated so side effects are contained.
- **Unit suite: deterministic material tests**, in CI / on-amend.

## 7. The engine and how the Judge calls it

One generic material, afforded to the Judge practice:

```
evaluate_quality_for_practice(name) -> findings
```

It projects the named bundle, reads its `evaluation` layer, runs the spec over
that practice's recent **real** trail, and returns structured findings. Written
once, by a developer, as infrastructure — it is the only evaluation *code*.

Each Judge cycle (mirroring the existing idle-triggered `_run_invariant_audit_loop`
in `autonomic_runner.py`):

1. **Deterministic newness check** — set-diff: somatic bundles − bundles-with-a-
   current-eval-spec. A practice missing (or with a stale) spec is detected with
   **no LLM**, and raised as a friction for the Smoother to author/refresh the
   spec. (First rollout notifies for every legacy practice at once — throttle
   one-at-a-time via the existing inbox/reconcile machinery.)
2. **Run the engine** for each practice that has a current spec.
3. **Judge the findings** — the one place an LLM is spent: is a finding real
   quality friction, or acceptable variation (legitimately periodic, patient,
   evidence-bound)? Real friction → Smoother inbox. Nothing → nothing.

Determinable/judgement split end to end: detect-missing (deterministic) →
author-spec (judgement, as data) → run-spec (deterministic engine) →
finding-is-friction? (Judgement).

## 8. Who fixes it — and the pooled authoring capability

The Judge **measures and names** friction; it never fixes. The **Smoother** is
the practice *designed to address friction*, and it is autonomic — so quality
friction, which by the no-human objective must be resolved with no person, is
the Smoother's to address.

But addressing it usually means **authoring substrate** — fix an eval-spec,
tighten a rule, sharpen a teleo-affective, even author a material or test. That
capability lives in practice_management, which is **somatic**. The Smoother
(autonomic) cannot enact it across the mode boundary. The resolution uses the
pooling the substrate already supports:

- **Author the capability once, in the pool** — both the authoring *materials*
  (the code that writes substrate) **and** the authoring *understanding/rules*
  (the expertise of authoring *well*) as pooled elements.
- **Compose them into both practices.** practice_management (somatic) composes
  them as the **human's optional door** to deliberate authoring. The Smoother
  (autonomic) composes them as the **loop's door** to reactive, friction-driven
  authoring. Same materials, same expertise, two compositions differing only in
  mode.

Nothing is duplicated; no mode boundary is crossed. This dissolves the original
worry ("if only practice_management can fix code, and the Smoother already fixes
substrate, we have a split brain"): the *capability and know-how* are shared in
the pool; the *practices* are two doors onto it.

**Pool the understanding, not just the materials.** Affording the Smoother bare
authoring materials without the authoring understanding gives it power without
wisdom — it could write substrate but not write it *right*, turning the Smoother
into a junk-drawer practice. The expertise must travel with the capability.

This also fixes *behavioural* friction the right way. "`stock_investor` is
stalling" is resolved not by patching the LLM in the moment but by the Smoother
**amending the bundle** it apprentices into — tighten a rule, add an
understanding, adjust an affordance. Risks belong in the bundle; so do their
fixes.

### Where the line sits

Keep *amending existing governance* direct for the Smoother (a one-line invariant
tweak shouldn't require composing the full authoring practice); reach for the
pooled authoring composition when *creating new substrate* — eval-specs, test
suites, new materials/affordances/bundles. Draw this line deliberately rather
than letting it blur. *(Open: whether to unify everything under one authoring
path instead — §11.)*

## 9. Why this is safe with no human

Full autonomy does not mean no oversight — it means oversight **relocates from a
person into substrate**:

- Authored artifacts land on the **trail** (inspectable).
- **Invariants** gate them: eval-spec must reference the teleo-affective
  objective; a new material must carry a unit suite; a bundle write must leave a
  current eval-spec; etc.
- The **sandbox** isolates execution; the **promotion gate is mechanical** — an
  artifact must pass its unit suite + sandboxed system exercise before it is
  blessed into production. "No human" and "must pass review" are not in tension;
  the review is deterministic.
- The Smoother's authoring is itself an autonomic enactment, so the **reflective
  loop hands it back to the Judge** to examine. The loop authors, gates, and
  re-judges its own fixes.

And the ground under all of it: **practice_management is subject to its own
`evaluation` layer and suite.** The authoring practice is itself continuously
measured against its objective by the same loop. That — not a human reviewer —
is what makes the Smoother's authoring trustworthy. The mechanism grounds
itself.

**The recursion is already bounded.** The Smoother's authoring enactments ride
governance that exists today: the reflective loop's **watermark** plus
`friction_reconcile`'s **cap-then-tombstone** bound self-amendment spirals. No
new ungoverned loop is created.

## 10. End-to-end shape

```
            ┌─────────────────────────── autonomic, no human ───────────────────────────┐
            │                                                                            │
 practice runs (somatic, real trail)                                                     │
            │                                                                            │
            ▼                                                                            │
   Judge cycle:                                                                          │
     • set-diff: missing/stale eval-spec? ── deterministic ──► friction ─┐              │
     • evaluate_quality_for_practice(name) over real trail               │              │
     • judge findings: real quality friction? ───────────────► friction ─┤              │
            │ nothing → nothing                                          ▼              │
            │                                              Smoother inbox               │
            │                                                    │                       │
            │                                   compose POOLED authoring (materials +    │
            │                                   understanding) — the loop's door         │
            │                                                    │                       │
            │                                   author fix: eval-spec / rule / bundle /   │
            │                                   material / test                          │
            │                                                    │                       │
            │                                   sandbox + invariants + mechanical        │
            │                                   promotion gate                           │
            │                                                    │                       │
            │                                   reflective loop ► Judge re-examines      │
            │                                                    │                       │
            └──────────── next enactment apprentices into improved bundle ◄─────────────┘

 practice_management (somatic) = the human's optional door onto the SAME pool.
```

## 11. Invariants this design needs

- **`bundle_requires_current_evaluation`** — a bundle created or amended without
  a present `evaluation` layer (or an explicit `not-yet-evaluable` declaration)
  raises a friction.
- **`evaluation_must_cover_teleo_affective`** — an eval-spec that does not
  exercise the bundle's declared objective is vacuous → friction.
- **`evaluation_not_stale`** — eval-spec records the bundle version/hash it was
  derived from; on mismatch (bundle moved on), demand a re-sync.
- **`new_material_requires_unit_suite`** — an authored material without a unit
  suite cannot be promoted.
- **`promotion_requires_green_gate`** — no artifact reaches production without
  passing the sandboxed unit + system exercise.

## 12. Open decisions

1. **Smoother authoring line** — ✅ **resolved (lean), Phase 3.** Existing-governance
   amendments stay direct; the pooled authoring covers *new* substrate. The
   Smoother got eval-spec (data) authoring now; new-code/new-bundle creation is
   deferred to Phase 4 with the sandbox + gate. (§8)
2. **Eval-spec schema** — finalise the vocabulary of §5 (signals, thresholds,
   coverage assertions, rubric blocks) and the version/hash pinning format.
3. **Sandbox surface per practice** — how each practice exposes a dry-run /
   sandbox mode (`proof_fund_test`, draft-only label, staged-not-issued
   calendar) so the on-amend system exercise has no real side effects.
4. **Generic stall detector as a floor?** — keep the cheap cross-enactment
   repetition detector as universal baseline coverage for the window *before* a
   practice's eval-spec exists (defence in depth), or rely solely on the
   per-practice evaluation.

## 13. Build phasing

1. **Engine + layer, read-only.** ✅ **Done.** `EvaluationSpec` + `evaluations`
   substrate pool + `Bundle.evaluation_ids` (`types.py`, `substrate_loader.py`);
   the `evaluate_quality_for_practice` engine (`materials/practice_evaluation.py`,
   four generic signal kinds), afforded to the Judge
   (`substrate/affordances/evaluate_practice_quality.md`); first eval-spec
   `substrate/evaluations/eval_stock_investor.md`. Proven over `proof_fund_001`'s
   real trail — surfaced the idle-loop and never-closed-drift concerns. Read-only;
   no Friction emitted.
2. **Close the Judge loop.** ✅ **Done.** `practice_evaluation_routing.py`:
   deterministic, idempotent newness set-diff (`practice_missing_evaluation`) and
   objective-coverage check (`evaluation_objective_uncovered`) — the §11
   invariants, detect-only — plus engine-driven concern collection and the Judge
   dispatch brief. `_run_practice_evaluation_loop` in `autonomic_runner.py`
   (idle-triggered, mirrors the invariant-audit loop) wires it in, **gated off by
   default** (`PRACTICE_PRACTICE_EVAL_ENABLED`) so it cannot churn the Smoother
   before Phases 3-4 give it the pooled authoring to resolve what is routed.
   Concerns are NOT turned into Friction deterministically — the Judge judges
   concern-vs-variation, then `emit_friction`s genuine ones.
   *Deferred within this phase:* the `evaluation_not_stale` invariant (needs
   bundle-revision hashing) and a per-practice concern-dispatch dedup.
3. **Pool the authoring capability.** ✅ **Done.** Shared authoring expertise
   `und_substrate_authoring` (the §8 "wisdom, not just power" — substrate shape
   incl. the evaluations pool, author-data-not-code, trace-to-teleo-affective,
   verify-where-projected) composed into **both** practice_management (somatic)
   and smoother (autonomic). The eval-spec authoring *capability* added as data
   authoring: `write_evaluation` + `pm_create_evaluation`/`pm_amend_evaluation` +
   `author_evaluation`/`amend_evaluation` affordances, composed into both. Also
   fixed a latent round-trip bug — `write_bundle` and the PM bundle materials now
   carry `evaluation_ids`, so an `amend_bundle` no longer silently drops a
   practice's eval-spec link. **Scope (resolving open decision #1, lean):** the
   Smoother gets the *data* authoring (eval-specs) now, since eval-specs are
   validated data and low-risk; new-*code*/new-bundle creation for the Smoother
   (`author_material`/`author_affordance`/`author_bundle`) is deferred to Phase 4
   so it lands together with the sandbox + mechanical promotion gate rather than
   giving the live autonomic Smoother unsandboxed codegen ahead of the gate.
4. **Smoother smooths.** ✅ **Built; go-live is the user's switch.** Mechanical
   promotion gate for eval-specs: `validate_signals` (known kinds + required
   params) rejects a malformed spec at author time, and an objective-coverage
   gate in `pm_create_bundle`/`pm_amend_bundle` refuses to wire a spec into a
   bundle unless its `objective_ref` is one of that bundle's teleo-affective ids
   — so a vacuous evaluator cannot be activated. `rule_smoother_resolve_evaluation_friction`
   guides the Smoother to fix each friction at the right layer, and crucially NOT
   to silence a real quality concern by weakening the measure — a confirmed
   concern is fixed by improving the *practice's* bundle. Enablement is config-
   driven (`practice_evaluation.enabled` in the autonomic config → the gated
   loop), **left off by default**: turning it on lets the loop modify substrate
   autonomously, so it is a deliberate go-live decision rather than a silent
   default flip.
   *Scope note (departure from the original §9 sketch):* no live "system-test
   sandbox" was built, and the Smoother was **not** given new-*code*/new-bundle
   authoring. Two reasons. The continuous loop evaluates *real production trails*
   (§6), so it needs no synthetic live exercise. And the only code the Smoother
   could author is a dynamic material, already confined to the AST-restricted
   `echo`/`constant`/`expression` forms — an existing execution sandbox. Fixing
   evaluation friction needs only data (eval-specs), prose (rules/understanding),
   and validated declarative invariants — all of which the Smoother now holds and
   all of which pass a mechanical gate. A live-exercise sandbox + unsandboxed
   code authoring remain genuine future work, needed only if the Smoother is ever
   to author free-form material code; they are not required to close this loop.
5. **Self-grounding.** Give practice_management its own `evaluation` layer and
   suite; backfill specs for legacy practices via the throttled newness path.

---

*Origin: a working session reviewing `stock_investor` status that surfaced the
locally-clean / collectively-stuck blind spot, then designed the generic remedy
above. Extends "The Apprenticeship and a Strange Loop" (the self-improving
loop) by giving each practice a measure the loop can act on.*
