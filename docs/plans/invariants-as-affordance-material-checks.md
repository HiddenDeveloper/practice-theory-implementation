# Plan: dissolve the free-floating `invariants` pool into affordance/material checks

Status: **proposed** (design + migration plan; no code yet)
Author: Claude Code session 2026-06-24

## Why

Invariants are deterministic checks that, today, live as a **free-floating
substrate pool** (`Substrate.invariants`), a peer of `rules` with **no link**
to the thing they constrain. Consequences observed in `activities_management`:

- **Sprawl** — 28 near-identical invariants all encoding "list before detail",
  because the Smoother has no way to see existing invariants before authoring
  (`read_pool` covers `teleo_affective/understanding/rules/affordances/
  materials/evaluations` — *not* invariants) and `rule_substrate_no_id_collision`
  only guards id-string uniqueness, so it mints discriminated ids
  (`_892`, `_951`, `_f999`).
- **Duplication / drift** — the same contract exists as a rule (prose) *and* N
  invariants (predicate), unlinked, free to disagree.
- **Boundary smell** — the project's founding principle is that the
  determinable/judgement split should *be* the code/LLM split. Invariants are
  deterministic, yet they sit in their own pool rather than with the
  deterministic things (materials/affordances).

## Target model

A determinable check lives **on the thing it constrains**, sorted by the role
distinction:

- **Affordance** = *what is afforded* and how it is properly reached
  (perspectival, practice-facing), framed over materials. Carries **usage
  preconditions** — sequencing/ordering contracts about proper use of the
  afforded capability (e.g. "to reach `garmin_get_activity`, an earlier
  `garmin_list_activities` step must exist"). This is where the overwhelming
  majority of today's invariants belong.
- **Material** = *the actual function/action* (raw deterministic I/O). Carries
  **intrinsic contracts** — true wherever the function is invoked, regardless of
  framing (e.g. `arg_present`, `arg_nonempty`, output validity).
- **rules / understanding / teleo-affective** = judgement layer (LLM-facing
  prose). Rules keep *only* what needs judgement; determinable ordering prose
  moves out.
- **The free-floating `invariants` pool is removed.**

Discriminator for sorting an existing invariant:

> Is the contract about *how/when the afforded capability is properly used*
> (sequencing across materials)? → **affordance precondition**.
> Is it intrinsic to *the function itself* (its args/output), true under any
> framing? → **material contract**.

`activity_detail` already declares `materials: [garmin_list_activities,
garmin_get_activity]` — the ordering contract is that affordance describing its
own proper use. So the 28 collapse to ~2 affordance preconditions
(`activity_detail` requires an earlier list; `daily_summary` requires an earlier
list). You cannot have 28, because there are ~2 affordances — sprawl becomes
structurally impossible, and the pools that hold the checks
(`affordances`, `materials`) are already readable + collision-guarded +
bundle-composed.

## What stays (reused, not rebuilt)

The predicate machinery is already material/affordance-keyed and is kept as-is:

- `invariant_engine.evaluate_predicate` / `validate_predicate` and the leaf ops
  (`step_exists` {affordance_id?, material_name?, result_contains?},
  `any_earlier_step_result_contains`, `arg_present`, `arg_nonempty`,
  `all`/`any`/`not`). Only the *source* of checks changes — from a flat
  invariant list to checks attached to affordances/materials.
- The trail `invariant_firings` table + idempotency + the audit loop
  (`_run_invariant_audit_loop`) — kept, re-keyed on a stable check identity.

## Touch-point inventory (file:symbol)

Data model — `src/practice_theory_implementation/types.py`
- `Invariant` dataclass + `Substrate.invariants` — to be retired.
- `Affordance` (`id, name, description, materials`) — **add** `preconditions`
  (tuple of check records).
- `Material` (`name, description, input_schema`) — **add** `contracts`
  (tuple of check records).
- New `Check` dataclass: `{ id, trigger, friction_kind, message, when
  (predicate), status, mode }` — the per-check governance state that the
  free-floating Invariant carried, now owned by an affordance/material.

Engine — `src/practice_theory_implementation/invariant_engine.py`
- `run_invariants(store, enactment, invariants=None)` — change the default
  source: gather active checks from `substrate.affordances[*].preconditions` and
  `substrate.materials[*].contracts` instead of `substrate.invariants`. Firing
  identity becomes `<owner_kind>:<owner_id>::<check_id>` (stable, replaces bare
  invariant id).

Runtime caller — `src/practice_theory_implementation/judge_triage.py:257`
- `run_invariants(store, enactment)` on enactment close — unchanged call site;
  picks up the new source automatically.

Loader — `src/practice_theory_implementation/substrate_loader.py`
- `_load_invariants` (parses `substrate/invariants/*.md`) — retire after
  migration.
- `_load_affordances` — parse a `preconditions:` block from affordance
  frontmatter. New `_load_materials` contract parsing (materials currently come
  from `MATERIAL_SURFACES` / dynamic_materials — decide where material contracts
  are declared; see Open decisions).

Authoring — `src/practice_theory_implementation/materials/practice_management.py`
- `pm_create_invariant` / `pm_amend_invariant` / `pm_tombstone_invariant`
  (≈ lines 284-340) → reframe to `pm_add_check` / `pm_amend_check` /
  `pm_retire_check` taking an `(owner_kind, owner_id, check)` — add/amend/retire
  a check *on* an affordance or material. Dedup is now free: the owner's
  existing checks are visible via `read_pool` (affordances/materials are already
  readable), so the Smoother sees them before adding.

Affordances (the Smoother's tools) — `substrate/affordances/`
- `author_invariant.md` / `amend_invariant.md` / `tombstone_invariant.md` →
  `add_check` / `amend_check` / `retire_check`, described as "attach/refine/
  retire a determinable check on the affordance or material it constrains; read
  the owner's current checks first."

Persistence — `src/practice_theory_implementation/substrate_writer.py`
- `write_invariant` (line 139) — retire. Checks persist inside their owner's
  file via `write_affordance` (extend to emit `preconditions`) and the material
  surface.

Trail — `src/practice_theory_implementation/trail.py`
- `invariant_firings` table + `unaudited_invariant_firings` /
  `mark_invariant_firing_audited` — keep the table; the `invariant_id` column
  now stores the stable check identity. (Optional later: rename column.)

Audit loop — `src/practice_theory_implementation/autonomic_runner.py`
- `_run_invariant_audit_loop` + `_invariant_audit_brief` — reviews firings as
  "judgement over the rules". Update the brief to resolve a firing's
  owner+check instead of `substrate.invariants[...]`.

Substrate dir
- `substrate/invariants/*.md` → migrated into affordance `preconditions` /
  material `contracts`, then the directory is removed.

## Migration order (phased, non-breaking)

1. **Add the data model** — `Check` dataclass; `Affordance.preconditions`,
   `Material.contracts`. Loader parses them. No behaviour change yet.
2. **Union the engine source** — `run_invariants` evaluates checks from
   affordances/materials **in addition to** the legacy `invariants` pool, with
   the new firing identity. Both sources active → nothing breaks while we
   migrate content. Tests: same enactment fires the same friction from either
   source.
3. **One-time content migration** — a script reads every
   `substrate/invariants/*.md`, sorts each by the discriminator (usage →
   affordance precondition; intrinsic → material contract), resolves the owner
   from the `trigger` material + which affordance reaches it, and **de-dupes**
   structurally identical `(trigger, when)` contracts into one check per owner.
   The 28 activities invariants → ~2 affordance preconditions. Output reviewed
   by a human (it encodes judgement about ownership).
4. **Reframe authoring** — swap the `pm_create/amend/tombstone_invariant`
   materials + affordances for the check-on-owner versions. Smoother now reads
   the owner's checks (free dedup) before adding.
5. **Remove the legacy pool** — delete `Substrate.invariants`, `_load_invariants`,
   `write_invariant`, `substrate/invariants/`, and the legacy branch in
   `run_invariants`, once steps 2-4 are verified and the directory is empty.
6. **(Optional) prevention mode** — with checks owned by affordances, a
   precondition *could* be enforced before invocation (prevent), not only
   detected after close. Defer; `mode: detect` stays the default.

## Identity & idempotency note

Today firing idempotency and audit keying use the bare invariant id. After the
move, the stable identity is `<owner_kind>:<owner_id>::<check_id>` (e.g.
`affordance:activity_detail::requires_prior_list`). This must be stable across
reloads so `invariant_firings` idempotency and `mark_invariant_firing_audited`
keep working. The content-migration script assigns each surviving check a stable
`check_id` and that becomes the firing key.

## Open decisions (need your call)

1. **Where material contracts are declared.** Materials come from
   `MATERIAL_SURFACES` (code) or `dynamic_materials/` (files). Affordance
   preconditions are clean (affordance files are authorable). Material intrinsic
   contracts may be few; options: (a) declare them in the material surface
   alongside `input_schema`; (b) defer material-contracts entirely for v1 and
   only ship affordance preconditions (covers ~all current invariants).
   *Recommendation: ship affordance preconditions first (v1), add material
   contracts later if needed.*
2. **Inline vs co-located checks.** Embed `preconditions:` in the affordance
   frontmatter (contract lives with the thing — recommended), vs separate check
   files carrying an `owner` ref (preserves per-check file history). *Recommend
   inline; per-check `status`/governance lives in the structured entry.*
3. **Separately:** the *rule* bloat (additive Friction-paragraph walls, driven
   by `rule_substrate_amend_additively`) is a distinct Smoother pathology this
   refactor does **not** fix. Track separately.

## Verification

- Engine parity test (step 2): a corpus of closed enactments fires identical
  frictions whether checks come from the legacy pool or the new owners.
- Migration test (step 3): the 28 activities invariants collapse to the expected
  ~2 affordance preconditions; no enactment loses a firing it had before.
- Loader round-trip: affordance with `preconditions` written then re-read is
  byte-stable.
- The existing `_run_invariant_audit_loop` still resolves and reviews firings
  by the new identity.
