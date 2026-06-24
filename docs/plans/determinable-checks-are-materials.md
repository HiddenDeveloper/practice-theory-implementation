# Plan: determinable checks are materials

Status: **proposed (re-aimed)** — supersedes the earlier
"invariants → affordance preconditions" framing. Phases 1-3 of that earlier
framing already landed (the free-floating `invariants` pool is gone and contracts
are homed on affordances); this plan treats that as a **transitional state** and
re-aims at the correct target.
Author: Claude Code session 2026-06-25

## The governing principle

The system's founding boundary: **the determinable/judgement split is the
code/LLM split.** Deterministic logic in this architecture is a **material** — a
function in the registry, resolved by name, authored (including autonomously) via
the materials machinery. A determinable check is just a deterministic function
over an enactment's step history. **Therefore a check is a material**, and the
affordance it governs **references it by name**, exactly as an affordance
references its action materials.

## Why the invariant situation occurred (the root cause this corrects)

Autonomous creation of deterministic enforcement was *correct* — that is the
"intelligence only where judgement is needed" objective working. The fault was
that, on 2026-06-04, the deterministic check was built as a **bespoke parallel
subsystem** — a sixth `invariants` pool + a `forbid_when` predicate DSL + its own
`invariant_engine` — instead of as a **material**.

It diverged for a concrete reason: the dynamic-material authoring sandbox
(`registry._compile_dynamic_expression`) allows only literals + `args` (no loops,
no step access), and normal materials are invoked *mid-enactment with call args*,
whereas a check must run *post-close over the whole step list*. Faced with "the
material layer can't express or invoke a step-history predicate," the path taken
was to build a parallel pool+engine rather than to **extend the materials layer**
with a step-predicate authoring kind and a check-invocation context.

Everything downstream followed from that one mis-modeling: because the check was
not a material, it did not inherit the registry, name-resolution, validation, or
the `read_pool` read surface — so there was no dedup, hence the sprawl; and it sat
as a pool peer-to-`rules`, hence the drift from the 5-element model.

## Target architecture

- **Check-material** — a deterministic function `check(steps) -> Violation | None`
  registered in the function registry by name, like every other material.
  Self-contained: it knows its own trigger and predicate and returns the friction
  to raise. Authored via the existing dynamic-material path with a new
  implementation `kind: enactment_check` whose body carries
  `{trigger, forbid_when, friction_kind, message}`. `build_dynamic_material_function`
  builds the callable by **reusing `evaluate_predicate`** — the predicate DSL is
  kept as the safe authoring language for this material kind, now plumbed through
  the materials layer rather than a separate pool.

- **Affordance precondition** — a **name reference** to one or more check-materials
  the affordance is governed by (`preconditions: [check_list_before_detail]`), not
  an embedded predicate. The wiring (which checks govern this afforded capability)
  lives on the affordance; the *logic* lives in the material.

- **Engine** — an enactment-check runner (replacing `run_invariants`'s pool scan):
  on close, resolve the check-materials referenced by affordances, invoke each over
  the enactment's steps, and raise+resolve any returned violation
  deterministically. Firing identity is simply the **check-material name** (no
  composite id needed).

Two wins fall out for free:
- **Multi-owner dissolves.** The `garmin_get_activity` "list before detail"
  contract is *one* check-material referenced by both `activity_detail` and
  `intermittent_walking_analysis`. One function, two references — no duplication,
  no judgement call (the earlier "decision 1(a)").
- **Dedup is structural.** Check-materials are in the `materials` pool, which
  `read_pool` exposes — so "does a check for this contract already exist?" is
  answerable before authoring, and a duplicate collides on the material name. The
  original "why didn't the Smoother check for duplicates?" gap closes by
  construction.

## Dual invocation, one registry

Action materials are invoked with `**arguments` mid-enactment (the MCP
affordance-invocation path). Check-materials are invoked with the enactment's
`steps` post-close (the check runner). Both live in the one `name -> callable`
registry; the call sites differ. A material's kind marks which invocation it
supports, and `validate_against` is extended so a check-material is never invoked
as an action (and vice versa).

## What is reused vs. retired

Reused (relocated into the materials layer):
- `invariant_engine.evaluate_predicate` / `validate_predicate` / the leaf ops
  (`step_exists`, `any_earlier_step_result_contains`, `arg_present`, `arg_nonempty`,
  `all`/`any`/`not`) and `EvalContext` — become the runtime + validator of the
  `enactment_check` material kind.
- `registry.build_dynamic_material_function` / `register` / `resolve` /
  `register_dynamic_material` — gain the `enactment_check` kind.
- the trail `invariant_firings` table + idempotency + the audit loop — kept, keyed
  on the check-material name.

Retired:
- `types.Invariant` and `Substrate.invariants` (already tombstoned/empty).
- the transitional `Check` dataclass with an **embedded** `forbid_when`
  (Phase 1-3 shape) — replaced by check-material name references.
- the standalone `run_invariants` pool scan — replaced by the check runner.
- the Smoother's `author_invariant` / `amend_invariant` / `tombstone_invariant`
  affordances — replaced by authoring a check-*material* (existing dynamic-material
  authoring) + wiring a reference (existing affordance amendment).

## Touch-point inventory (file:symbol)

- `registry.py` — add `enactment_check` to `build_dynamic_material_function`;
  the check-callable signature (`check(steps) -> Violation | None`); a
  check-invocation entry point; extend `validate_against` for the kind split.
- `invariant_engine.py` — keep the predicate evaluator/validator; replace
  `run_invariants` with `run_enactment_checks(store, enactment)` that resolves
  affordance-referenced check-materials and invokes them.
- `substrate_loader.py` — `_load_dynamic_materials` already builds dynamic-material
  callables; it will build `enactment_check` ones. Change `Affordance.preconditions`
  parsing from embedded `Check` to name references.
- `types.py` — `Affordance.preconditions: tuple[str, ...]` (check-material names);
  retire `Check` (embedded form) and `Invariant`.
- `substrate_writer.py` — write affordance `preconditions` as a name list; write
  check-materials as dynamic-material files (reuse the dynamic-material writer).
- `judge_triage.py:257` — `run_invariants(...)` becomes `run_enactment_checks(...)`.
- `autonomic_runner.py` — `_run_invariant_audit_loop` / `_invariant_audit_brief`
  resolve a check-material (by name) instead of `substrate.invariants[id]`.
- `migrate_invariants_to_checks.py` — apply emits **check-materials + name
  references** rather than embedded affordance preconditions; the multi-owner case
  becomes one check-material with two references.

## Migration order (builds on the current transitional state)

1. **Check-material kind** — `enactment_check` in `build_dynamic_material_function`
   (reusing `evaluate_predicate`); a `Violation` result; a check-invocation entry
   point. Pure/registry-level; fully unit-testable. No wiring change yet.
2. **Affordance references** — `Affordance.preconditions` becomes check-material
   names; loader + writer updated. Engine `run_enactment_checks` resolves and runs
   referenced check-materials. Parity test: a referenced check-material fires on the
   same enactments the embedded predicate did.
3. **Convert the transitional state** — turn the 20 distinct embedded
   affordance-preconditions (from the earlier apply) into 20 check-materials +
   references; the multi-owner contract becomes one check-material referenced
   twice. Re-collapse verified.
4. **Authoring** — retire `author_invariant` et al.; the Smoother authors
   check-materials via the dynamic-material path (now with read-before-author
   dedup) + wires a reference via affordance amendment.
5. **Cleanup** — remove `Invariant`, `Substrate.invariants`, the embedded `Check`,
   the legacy `run_invariants`; fix the audit brief to resolve check-materials.

## Open decisions

1. **Check-callable signature** — `check(steps) -> Violation | None` (self-contained,
   does its own trigger-gating) vs. the engine pre-gates on `trigger` and passes an
   `EvalContext`. *Lean: self-contained, so a check-material is fully described by
   its file and reusable across affordances without engine help.*
2. **Where check-material files live** — under `substrate/dynamic_materials/`
   (reuse the existing authored-material path) vs. a dedicated `substrate/checks/`
   dir. *Lean: dynamic_materials, since a check IS a material — no new pool, which
   is the whole point.*

## Verification

- Kind builder: an `enactment_check` material built from a `forbid_when` fires on
  the same `EvalContext` the predicate did (reuses the engine's existing tests).
- Reference parity: an affordance referencing a check-material raises the same
  friction the embedded precondition did, on the same enactments.
- Dedup: authoring a structurally-identical check-material is detectable via
  `read_pool(materials)` / collides on name.
- Audit loop resolves and reviews firings by check-material name.
