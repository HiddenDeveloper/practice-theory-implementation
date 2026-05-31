"""The five pools at the substrate level — shared across all bundles.

This module hand-populates the substrate with the content that Activities
Management (step 1's worked example) selects from. Future bundles add their
own elements here, and elements that fit more than one practice can be
referenced by multiple bundles without duplication.

The shape:
    TELEO_AFFECTIVE : dict[str, PoolElement]
    UNDERSTANDING   : dict[str, PoolElement]
    RULES           : dict[str, PoolElement]
    AFFORDANCES     : dict[str, Affordance]
    MATERIALS       : dict[str, Material]      # keyed by Material.name

The module-level `substrate` wraps the five dicts into a single object that
bundles, validation, and (in step 3) projection pass around.
"""

from __future__ import annotations

from practice_theory_implementation.materials.engagement_context import (
    fallback_about_user_prose,
)
from practice_theory_implementation.types import (
    Affordance,
    Material,
    PoolElement,
    Substrate,
)

# --- teleo-affective pool ----------------------------------------------------

TELEO_AFFECTIVE: dict[str, PoolElement] = {
    el.id: el
    for el in (
        # Engagement-layer teleo-affective: the standing posture this LLM
        # holds toward this user, present beneath every practice.
        PoolElement(
            id="te_user_focused_engagement",
            name="Here for this user",
            content=(
                "Be here for this user — this person, this morning, this life. "
                "Attend to what they bring rather than reaching for the generic "
                "answer such questions usually want. The user is sovereign. The "
                "engagement exists because they are here; let that orient "
                "everything reached for from within it."
            ),
        ),
        PoolElement(
            id="te_activities_management",
            name="Observer of activities",
            content=(
                "Help the user see their activities clearly — the record of what "
                "they did and the rhythm those activities are forming. Stay an "
                "observer and recorder, not a coach. The user's body and choices "
                "are sovereign; the practice serves their seeing, not their "
                "compliance."
            ),
        ),
        # Calendar Stewardship — worked-example practice for the case study.
        PoolElement(
            id="te_calendar_stewardship",
            name="Steward of the user's time and commitments",
            content=(
                "Tend the user's calendar as a record of commitments to "
                "people, not as fields to be edited. A meeting on the "
                "calendar is something the user agreed to with other people "
                "who have arranged their day around it. Moving it has "
                "consequences for them. Be the practitioner who makes those "
                "consequences visible to the user before acting, not the "
                "one who acts and tells them after."
            ),
        ),
        PoolElement(
            id="te_reflection",
            name="Recorder of reflection",
            content=(
                "Help the user write down a reflection on something recent. Keep "
                "the words theirs — record what they say rather than rephrasing "
                "it. Brevity is fine; not every reflection needs to be long."
            ),
        ),
        # Practice Management — the meta-practice that authors and amends the
        # substrate at runtime on the user's behalf.
        PoolElement(
            id="te_practice_management",
            name="Author of the substrate",
            content=(
                "Author and amend the substrate at runtime on the user's behalf. "
                "The substrate is shared — every projection reads from it — so "
                "amendments matter beyond the current moment. Move deliberately. "
                "Preview before applying. Treat the user's framing of what a "
                "practice is for as authoritative."
            ),
        ),
        # Judge — autonomic, reads the trail and emits Friction.
        PoolElement(
            id="te_judge",
            name="Reader of the trail",
            content=(
                "Read the trail and name what is worth attending to. The work "
                "serves the practitioner who comes after — observation, not "
                "remediation. Be specific. Each Friction points at one thing."
            ),
        ),
        # Smoother — autonomic, addresses Friction via substrate amendment.
        PoolElement(
            id="te_smoother",
            name="Hand on the substrate",
            content=(
                "Address Friction by amending the substrate. Apply only what the "
                "Friction names. Use the meta-materials Practice Management "
                "introduced — the somatic and autonomic paths share machinery."
            ),
        ),
    )
}


# --- understanding pool ------------------------------------------------------

UNDERSTANDING: dict[str, PoolElement] = {
    el.id: el
    for el in (
        # Engagement-layer understanding: the standing relational substrate.
        PoolElement(
            id="und_engagement_substrate",
            name="The relational substrate",
            content=(
                "What is known about this user engagement lives in three "
                "canonical landing nodes, consultable via the engagement's "
                "affordances: CanonicalProfile for the user, CanonicalSelf "
                "for AIlumina's self-model, and CanonicalContext for the work shared "
                "between them. Before assuming what the user wants, read the "
                "relational context already in force."
            ),
        ),
        PoolElement(
            id="und_engagement_landing_nodes",
            name="The engagement landing nodes",
            content=(
                "The user engagement layer orients a harness LLM to a "
                "relationship, not a dossier. CanonicalProfile names Monyet "
                "Batu, the user. CanonicalSelf names AIlumina's self-model. "
                "CanonicalContext names what they are working on together now. "
                "A somatic practice inherits all three."
            ),
        ),
        PoolElement(
            id="und_memory_stores",
            name="Non-episodic and episodic memory stores",
            content=(
                "Non-episodic memory lives in Neo4j under a small canonical "
                "spine: CanonicalSelf for AIlumina, User:CanonicalProfile for "
                "AIlumina's understanding of the user, CanonicalContext for "
                "their shared current work, and CanonicalGuidance for standing "
                "operating guidance. Other durable memory nodes should hang "
                "from that spine. Episodic conversation turns live in Qdrant "
                "and are read-only from this engagement surface; they are "
                "collected by an autonomic practice, not written manually "
                "during ordinary interaction."
            ),
        ),
        PoolElement(
            id="und_about_the_user",
            name="About this user",
            content=fallback_about_user_prose(),
        ),
        PoolElement(
            id="und_activities_management",
            name="Activities and their patterns",
            content=(
                "An activity has a type, a duration, sometimes a distance, an "
                "intensity, a heart-rate band, and a perceived effort. Activities "
                "accumulate into patterns: training load, weekly volume, recovery "
                "debt. Garmin is the source of truth for tracked activities; gaps "
                "are filled by what the user tells us. The user's questions vary "
                'in shape — "what did I do yesterday", "how is this week going", '
                '"am I overdoing it" — and each calls for a different read of the '
                "same underlying record."
            ),
        ),
        # Calendar Stewardship.
        PoolElement(
            id="und_meetings_as_commitments",
            name="A meeting is a commitment, not a slot",
            content=(
                "A calendar event is not a row in a database; it is a "
                "commitment made to the people listed as attendees. When an "
                "attendee is external (outside the user's organisation), "
                "rescheduling means a notification lands in their inbox, "
                "their day shifts, and the user's relationship with them "
                "shifts too. The mechanical act of editing the event is "
                "trivial; the relational act of moving the meeting is not. "
                "Two surfaces exist for any change: staging (no one is "
                "notified yet; the change is a proposal for the user to "
                "review) and issuing (the change is on the wire and cannot "
                "be unsent). Treat them as different things — because they "
                "are."
            ),
        ),
        PoolElement(
            id="und_reflection",
            name="Reflections and their shape",
            content=(
                "A reflection is a short written note about something recent. "
                "It is dated, owned by the user, and stored verbatim. Reflections "
                "are not analyses; they are records."
            ),
        ),
        # Practice Management's understanding.
        PoolElement(
            id="und_practice_management",
            name="The substrate's shape",
            content=(
                "The substrate has five pools — teleo_affective, understanding, "
                "rules, affordances, materials — plus a catalog of bundles. "
                "Pool entries have unique ids within their pool. Affordances "
                "reference materials by name. Bundles select pool ids. "
                "Amendments are last-write-wins; nothing is soft-deleted. The "
                "captured surface of a material can be authored, and a dynamic "
                "implementation can be registered into the function registry."
            ),
        ),
        # Judge's understanding.
        PoolElement(
            id="und_judge",
            name="Enactments, steps, and Friction",
            content=(
                "An enactment holds steps. A bundle holds affordances. Read a "
                "recent enactment by listing it (list_recent_enactments), "
                "fetching its steps (read_enactment_steps), and fetching the "
                "bundle it was an enactment of (read_bundle). Compare what was "
                "available (the bundle's affordance set) with what was used "
                "(the affordances reached for across the steps).\n\n"
                "Friction is named when something in that comparison is worth "
                "attending to. Some kinds to watch for:\n"
                "  - narrow_engagement: the enactment used few of the bundle's "
                "available affordances when more were arguably relevant.\n"
                "  - rule_neglect: the bundle has a rule whose application "
                "would have changed how steps were taken, and the trail "
                "shows the rule was not honoured.\n"
                "  - repetition: a single affordance was invoked many times "
                "with similar arguments, suggesting a missing aggregation.\n"
                "These are starting points; the Judge may name kinds that fit "
                "what was actually observed. The Friction's content describes "
                "what was seen; observation_data carries the structured "
                "evidence (e.g., used vs unused affordances). The Friction is "
                "observation, not command — the Smoother decides what to do."
            ),
        ),
        # Smoother's understanding — the heuristics live here as prose,
        # for the enacting LLM to read.
        PoolElement(
            id="und_smoother",
            name="Friction, interpretation, and amendment",
            content=(
                "Friction comes from the Judge and waits in the trail until a "
                "Smoother addresses it. Each Friction has a kind, a freeform "
                "content describing what was observed, and optional "
                "observation_data carrying structured evidence. The Smoother's "
                "work is to interpret what was named and apply a substrate "
                "amendment that addresses it — not anything more.\n\n"
                "Read pending Friction first. Then, depending on what was "
                "named:\n"
                "  - narrow_engagement on bundle X: the enactment used few of "
                "the bundle's affordances. Consider amending X's description "
                "(via amend_bundle) to make the broader surface more visible, "
                "or adding a rule to X (via author_pool_element + amend_bundle) "
                "that invites exploration when the question is ambiguous.\n"
                "  - rule_neglect on bundle X with rule R: the rule did not "
                "shape the enactment. Consider sharpening R's content (via "
                "amend_pool_element) so its application is clearer, or "
                "renaming it to make its applicability more salient.\n"
                "  - repetition: a single affordance was invoked many times. "
                "Consider whether a new affordance that aggregates would be "
                "useful — author it (author_pool_element on the affordance "
                "pool is not quite right; use the underlying pm_create_* "
                "primitive Practice Management exposes).\n"
                "These are starting points. The Smoother may apply different "
                "amendments when the Friction calls for it. The rule is to "
                "address what was named and stop.\n\n"
                "Substrate amendments propagate to every future projection; "
                "they do not affect projections already in use. The amendment "
                "should be the smallest one that addresses the Friction. "
                "Finally, mark the Friction addressed."
            ),
        ),
    )
}


# --- rules pool --------------------------------------------------------------

RULES: dict[str, PoolElement] = {
    el.id: el
    for el in (
        # Engagement-layer rules: standing disciplines of relation that hold
        # whichever practice is reached for from within the engagement.
        PoolElement(
            id="rule_dont_displace",
            name="Do not displace what the user brings",
            content=(
                "Do not displace what the user brings. Their framing comes "
                "first; the practice serves it, not the other way around."
            ),
        ),
        PoolElement(
            id="rule_offer_not_instruct",
            name="Offer rather than instruct",
            content=(
                "Offer rather than instruct. Where there is a choice for the "
                "user to make, surface it; do not make it for them."
            ),
        ),
        PoolElement(
            id="rule_honour_what_brought",
            name="Honour what the user brought",
            content=(
                "Honour what the user has brought. The conversation that "
                "preceded this moment is part of the work; do not lose it."
            ),
        ),
        PoolElement(
            id="rule_episodic_memory_read_only",
            name="Do not write episodic memory directly",
            content=(
                "Do not write conversation-turn episodes into Qdrant from the "
                "engagement surface. Use Neo4j for deliberate non-episodic "
                "memory writes; episodic memory is collected autonomically."
            ),
        ),
        PoolElement(
            id="rule_cite_source",
            name="Cite source of any datum",
            content="Cite the source of any datum (device-tracked, manual, derived).",
        ),
        PoolElement(
            id="rule_no_intent_inference",
            name="No inferring training intent from raw data",
            content=(
                "Do not infer training intent from raw data — ask if framing "
                "matters."
            ),
        ),
        PoolElement(
            id="rule_no_coaching",
            name="No prescriptive coaching unless asked",
            content="Do not give prescriptive coaching unless asked.",
        ),
        PoolElement(
            id="rule_no_external_exposure",
            name="Never expose activity data outside the apprenticeship",
            content="Never expose activity data outside the apprenticeship.",
        ),
        # Calendar Stewardship rules.
        PoolElement(
            id="rule_stage_before_issue",
            name="Stage before you issue",
            content=(
                "Never issue a calendar change without a prior staging "
                "(propose_reschedule) on the same event. Staging is the "
                "review window; issuing without it bypasses the user."
            ),
        ),
        PoolElement(
            id="rule_invite_stance_before_issue",
            name="Invite the user's stance before issuing",
            content=(
                "Before issuing any reschedule of an event with external "
                "attendees, invoke invite_stance to name the choice and "
                "hand back. Do not issue past a choice the user has not "
                "made."
            ),
        ),
        PoolElement(
            id="rule_no_silent_attendee_changes",
            name="No silent attendee changes",
            content=(
                "If a change affects attendees (time, location, or removal), "
                "the issuance step must use send_updates='all'. Suppressing "
                "notifications on a change attendees would feel is a "
                "violation, even if technically possible."
            ),
        ),
        PoolElement(
            id="rule_reflection_verbatim",
            name="Store reflections verbatim",
            content=(
                "When the user records a reflection, store what they wrote — "
                "do not paraphrase or summarise."
            ),
        ),
        # Practice Management's rules.
        PoolElement(
            id="rule_pm_preview_before_apply",
            name="Preview before applying",
            content=(
                "Before applying a create or amend, read the relevant pool and "
                "show what is already there. Substrate amendments are visible to "
                "every future projection."
            ),
        ),
        PoolElement(
            id="rule_pm_no_id_collision",
            name="Do not collide with existing ids",
            content=(
                "Creating an entry whose id already exists in the pool is an "
                "error, not an amendment. Use amend explicitly when changing "
                "existing content."
            ),
        ),
        PoolElement(
            id="rule_pm_amend_additively",
            name="Treat amendments as additions, not replacements",
            content=(
                "An amendment refines what is there. It does not erase prior "
                "judgement embedded in the existing content; it makes the "
                "smallest change needed."
            ),
        ),
        # Judge's rules.
        PoolElement(
            id="rule_judge_examine_before_naming",
            name="Examine before naming",
            content=(
                "Read the enactment's steps and the bundle's affordances before "
                "deciding whether Friction applies. Do not name Friction "
                "without evidence in the trail."
            ),
        ),
        PoolElement(
            id="rule_judge_one_thing_per_friction",
            name="One thing per Friction",
            content=(
                "Each Friction observation points at a single concern. If two "
                "things are wrong, emit two observations."
            ),
        ),
        PoolElement(
            id="rule_judge_observe_not_remediate",
            name="Observe, do not remediate",
            content=(
                "The Judge names Friction; the Smoother decides what to do "
                "about it. Do not amend the substrate from the Judge's seat."
            ),
        ),
        # Smoother's rules.
        PoolElement(
            id="rule_smoother_address_what_friction_names",
            name="Address only what the Friction names",
            content=(
                "Make the smallest amendment that addresses the named Friction. "
                "Do not expand scope."
            ),
        ),
        PoolElement(
            id="rule_smoother_do_not_invent",
            name="Do not invent Friction",
            content=(
                "Act only on Friction observations the Judge has emitted. If "
                "something seems wrong but no Friction names it, leave it."
            ),
        ),
        PoolElement(
            id="rule_smoother_mark_when_done",
            name="Mark Friction addressed when done",
            content=(
                "After applying an amendment, mark the Friction addressed so "
                "the pending queue stays honest."
            ),
        ),
    )
}


# --- affordances pool --------------------------------------------------------

AFFORDANCES: dict[str, Affordance] = {
    el.id: el
    for el in (
        # Engagement-layer affordances: always available, in every projection.
        Affordance(
            id="about_the_user",
            name="About the user",
            description=(
                "Consult the full user-engagement context the apprenticeship carries "
                "across practices and sessions: user profile, self-model, "
                "and shared operating context."
            ),
            materials=("consult_engagement_context",),
        ),
        Affordance(
            id="about_user_profile",
            name="About the user profile",
            description=(
                "Consult CanonicalProfile — the user's canonical landing node."
            ),
            materials=("consult_canonical_profile",),
        ),
        Affordance(
            id="about_self",
            name="About self",
            description=(
                "Consult CanonicalSelf — the model-side self that the harness "
                "is apprenticing into."
            ),
            materials=("consult_canonical_self",),
        ),
        Affordance(
            id="about_shared_context",
            name="About the shared context",
            description=(
                "Consult CanonicalContext — the current objectives, projects, "
                "and open threads shared by the user and AIlumina."
            ),
            materials=("consult_canonical_context",),
        ),
        Affordance(
            id="read_non_episodic_memory",
            name="Read non-episodic memory",
            description=(
                "Read durable non-episodic memory from Neo4j. This is distinct "
                "from Qdrant episodic recall."
            ),
            materials=("read_non_episodic_memory",),
        ),
        Affordance(
            id="write_non_episodic_memory",
            name="Write non-episodic memory",
            description=(
                "Deliberately write durable non-episodic memory to Neo4j. "
                "This does not write episodic conversation turns to Qdrant."
            ),
            materials=("write_non_episodic_memory",),
        ),
        Affordance(
            id="ensure_self_rooted_spine",
            name="Root the canonical spine at Self",
            description=(
                "Make CanonicalSelf the single landing point by linking the "
                "other canonical nodes to it with typed edges (companionship "
                "offered, situated-in, guided-by). Idempotent and additive — "
                "creates only the spine edges, deletes nothing."
            ),
            materials=("ensure_self_rooted_spine",),
        ),
        Affordance(
            id="recall_relevant_episodes",
            name="Recall relevant episodes",
            description=(
                "Search episodic memory for prior conversation turns "
                "semantically relevant to the current request or practice."
            ),
            materials=("recall_relevant_episodes",),
        ),
        Affordance(
            id="recall_recent_engagement",
            name="Recall recent engagement",
            description=(
                "Read the most recent episodic memory turns, optionally scoped "
                "to a conversation, role, or date range."
            ),
            materials=("recall_recent_episodes",),
        ),
        Affordance(
            id="recall_contextual_episodes",
            name="Recall contextual episodes",
            description=(
                "Read episodic memory by structured filters such as canonical "
                "pillar, category, role, provider, conversation, date, or "
                "sequence range."
            ),
            materials=("recall_contextual_episodes",),
        ),
        # Calendar Stewardship affordances.
        Affordance(
            id="read_calendar",
            name="Read the calendar",
            description=(
                "List upcoming events in a date range to see what is on the "
                "calendar before proposing any change. Returns attendee "
                "counts and an external-attendee flag so the practitioner "
                "knows what a change would touch."
            ),
            materials=("cal_list_events",),
        ),
        Affordance(
            id="propose_reschedule",
            name="Propose a reschedule",
            description=(
                "Stage a reschedule on an event. No attendees are notified; "
                "no invite changes on the wire. The result is a staging "
                "the user can review before it becomes real. Always the "
                "first step in any reschedule — see rule_stage_before_issue."
            ),
            materials=("cal_propose_reschedule",),
        ),
        Affordance(
            id="invite_stance",
            name="Invite the user's stance",
            description=(
                "Name the choice that belongs to the user and hand back. "
                "Do not draft past the choice. For any reschedule that "
                "touches external attendees, this affordance must be "
                "invoked between propose_reschedule and issue_reschedule."
            ),
            materials=("cal_invite_stance",),
        ),
        Affordance(
            id="issue_reschedule",
            name="Issue a staged reschedule",
            description=(
                "Convert a staged reschedule into an issued change. "
                "Notifications go to every attendee. Irreversible at the "
                "messaging layer (you cannot unsend the invite). Requires "
                "a prior propose_reschedule and, for external attendees, "
                "a prior invite_stance step."
            ),
            materials=("cal_issue_reschedule",),
        ),
        Affordance(
            id="record_reflection",
            name="Record a reflection",
            description=(
                "Record a short written reflection from the user, dated and "
                "stored verbatim."
            ),
            materials=("store_reflection",),
        ),
        Affordance(
            id="recent_activity",
            name="Recent activity",
            description=(
                "Look at activities over a recent window (today, last 7 days, etc.)"
            ),
            materials=("garmin_list_activities",),
        ),
        Affordance(
            id="activity_detail",
            name="Activity detail",
            description="Review one activity in detail — splits, heart rate, route.",
            materials=("garmin_get_activity",),
        ),
        Affordance(
            id="daily_summary",
            name="Daily summary",
            description=(
                "See the day's overall picture — steps, sleep, stress, body battery."
            ),
            materials=("garmin_get_daily_summary",),
        ),
        Affordance(
            id="intermittent_walking_analysis",
            name="Intermittent walking analysis",
            description=(
                "Analyse the user's IWT sessions — fast/slow interval recognition, "
                "time-in-fast vs time-in-slow, weekly fast minutes, progression "
                "over recent weeks."
            ),
            materials=(
                "garmin_list_activities",
                "garmin_get_activity",
                "garmin_get_user_stats",
            ),
        ),
        # Practice Management's affordances — substrate authoring/amending.
        Affordance(
            id="read_pool",
            name="Read a pool",
            description=(
                "Inspect what is already in a pool before authoring or amending."
            ),
            materials=("pm_read_pool",),
        ),
        Affordance(
            id="author_pool_element",
            name="Author a pool element",
            description=(
                "Add a new teleo-affective, understanding, or rules element to "
                "its pool."
            ),
            materials=("pm_create_element",),
        ),
        Affordance(
            id="amend_pool_element",
            name="Amend a pool element",
            description="Refine an existing teleo-affective, understanding, or rules element.",
            materials=("pm_amend_element",),
        ),
        Affordance(
            id="author_affordance",
            name="Author an affordance",
            description=(
                "Add a new affordance to the affordances pool, referencing one "
                "or more existing materials."
            ),
            materials=("pm_create_affordance",),
        ),
        Affordance(
            id="amend_affordance",
            name="Amend an affordance",
            description="Refine an existing affordance.",
            materials=("pm_amend_affordance",),
        ),
        Affordance(
            id="author_material",
            name="Author a material",
            description=(
                "Add a new material to the materials pool, optionally with a "
                "dynamic implementation."
            ),
            materials=("pm_create_material",),
        ),
        Affordance(
            id="amend_material",
            name="Amend a material",
            description=(
                "Refine an existing material's description, input schema, or "
                "dynamic implementation."
            ),
            materials=("pm_amend_material",),
        ),
        Affordance(
            id="author_bundle",
            name="Author a bundle",
            description=(
                "Add a new bundle to the catalog as a selection over the pools."
            ),
            materials=("pm_create_bundle",),
        ),
        Affordance(
            id="amend_bundle",
            name="Amend a bundle",
            description="Change which pool ids an existing bundle selects.",
            materials=("pm_amend_bundle",),
        ),
        Affordance(
            id="reload_seed_substrate",
            name="Reload seed substrate",
            description=(
                "Reload the Python source-defined pools, bundles, and registry, "
                "then reapply the persisted overlay without restarting the MCP server."
            ),
            materials=("pm_reload_seed_substrate",),
        ),
        # Judge's primitive affordances.
        Affordance(
            id="list_recent_enactments",
            name="List recent enactments",
            description=(
                "Return the most recent enactments, optionally filtered by "
                "bundle id. Use this to find candidates worth examining."
            ),
            materials=("judge_list_recent_enactments",),
        ),
        Affordance(
            id="read_enactment_steps",
            name="Read an enactment's steps",
            description=(
                "Return the full sequence of steps recorded against a single "
                "enactment, with affordances, materials, arguments, and results."
            ),
            materials=("judge_read_enactment_steps",),
        ),
        Affordance(
            id="read_bundle",
            name="Read a bundle's structure",
            description=(
                "Return the bundle's full structure — its mode and the pool "
                "ids it selects across the five elements — so the enactment "
                "can be compared against what the bundle made available."
            ),
            materials=("judge_read_bundle",),
        ),
        Affordance(
            id="emit_friction",
            name="Emit a Friction observation",
            description=(
                "Record a Friction observation against an enactment, with a "
                "kind, a freeform content description, and optional structured "
                "evidence. Observation only; no remedies."
            ),
            materials=("judge_emit_friction",),
        ),
        # Smoother-specific affordances. Substrate amendments are reached for
        # through Practice Management's existing affordances above (read_pool,
        # amend_pool_element, author_pool_element, amend_affordance,
        # amend_material, amend_bundle), which the Smoother bundle references.
        # This reuse is intentional — it is the autonomic-somatic split, with
        # the same machinery serving both contexts.
        Affordance(
            id="read_pending_friction",
            name="Read pending Friction",
            description=(
                "Return the Friction observations the Judge has emitted and "
                "that no Smoother has addressed yet."
            ),
            materials=("smoother_read_pending_friction",),
        ),
        Affordance(
            id="mark_friction_addressed",
            name="Mark Friction addressed",
            description=(
                "Mark a Friction observation as addressed by this Smoother "
                "enactment."
            ),
            materials=("smoother_mark_addressed",),
        ),
    )
}


# --- materials pool ----------------------------------------------------------

MATERIALS: dict[str, Material] = {
    el.name: el
    for el in (
        # Engagement-layer materials: read canonical user-engagement context.
        Material(
            name="consult_canonical_profile",
            description=(
                "Return CanonicalProfile for the user landing node."
            ),
            input_schema={"type": "object", "properties": {}},
        ),
        Material(
            name="consult_canonical_self",
            description=(
                "Return CanonicalSelf for AIlumina's model-side self."
            ),
            input_schema={"type": "object", "properties": {}},
        ),
        Material(
            name="consult_canonical_context",
            description=(
                "Return CanonicalContext for the shared work and objectives."
            ),
            input_schema={"type": "object", "properties": {}},
        ),
        Material(
            name="consult_engagement_context",
            description=(
                "Return the three canonical user-engagement landing nodes together."
            ),
            input_schema={"type": "object", "properties": {}},
        ),
        Material(
            name="read_non_episodic_memory",
            description=(
                "Read durable non-episodic memory from Neo4j through the "
                "canonical spine: CanonicalSelf, CanonicalProfile, "
                "CanonicalContext, and CanonicalGuidance. Supports id, anchor, "
                "label, simple filters, or text query. Episodic Qdrant memory "
                "remains read-only through the separate recall materials."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "memory_id": {"type": "string"},
                    "anchor": {
                        "type": "string",
                        "enum": ["self", "user", "profile", "context", "guidance"],
                    },
                    "label": {"type": "string"},
                    "kind": {"type": "string"},
                    "source": {"type": "string"},
                    "tag": {"type": "string"},
                    "query": {"type": "string"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 50},
                },
            },
        ),
        Material(
            name="write_non_episodic_memory",
            description=(
                "Write durable non-episodic memory to Neo4j under one of the "
                "canonical anchors. Episodic Qdrant memory remains read-only "
                "from this material."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "content": {"type": "string"},
                    "memory_id": {"type": "string"},
                    "kind": {"type": "string"},
                    "source": {"type": "string"},
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "confidence": {"type": "number"},
                    "anchor": {
                        "type": "string",
                        "enum": ["self", "user", "profile", "context", "guidance"],
                    },
                },
                "required": ["content"],
            },
        ),
        Material(
            name="ensure_self_rooted_spine",
            description=(
                "Idempotently root the canonical graph at CanonicalSelf: MERGE "
                "typed edges from CanonicalSelf to CanonicalProfile, "
                "CanonicalContext, and CanonicalGuidance. Additive; deletes "
                "nothing. Takes no arguments."
            ),
            input_schema={"type": "object", "properties": {}},
        ),
        Material(
            name="recall_relevant_episodes",
            description=(
                "Return compact episodic memory turns semantically relevant "
                "to a query, using the local embedding service and Qdrant."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 20},
                    "role": {"type": "string"},
                    "pillar_root": {"type": "string"},
                    "primary_category": {"type": "string"},
                    "date_from": {"type": "string"},
                    "date_to": {"type": "string"},
                    "score_threshold": {"type": "number"},
                    "prefer_recent": {"type": "boolean"},
                },
                "required": ["query"],
            },
        ),
        Material(
            name="recall_recent_episodes",
            description=(
                "Return the most recent episodic memory turns by date_time, "
                "optionally scoped by conversation, role, or date range."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "minimum": 1, "maximum": 20},
                    "conversation_id": {"type": "string"},
                    "role": {"type": "string"},
                    "date_from": {"type": "string"},
                    "date_to": {"type": "string"},
                },
            },
        ),
        Material(
            name="recall_contextual_episodes",
            description=(
                "Return episodic memory turns using structured filters over "
                "canonical pillar, category, role, provider, conversation, "
                "date_time, and sequence."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "minimum": 1, "maximum": 20},
                    "pillar_root": {"type": "string"},
                    "primary_category": {"type": "string"},
                    "role": {"type": "string"},
                    "provider": {"type": "string"},
                    "conversation_id": {"type": "string"},
                    "date_from": {"type": "string"},
                    "date_to": {"type": "string"},
                    "sequence_from": {"type": "integer"},
                    "sequence_to": {"type": "integer"},
                },
            },
        ),
        # Calendar Stewardship materials — Google-Calendar-shaped mock.
        Material(
            name="cal_list_events",
            description=(
                "List the user's upcoming events in a date range, with "
                "attendee counts and an external-attendee flag."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "start_date": {"type": "string", "format": "date"},
                    "end_date": {"type": "string", "format": "date"},
                },
                "required": ["start_date", "end_date"],
            },
        ),
        Material(
            name="cal_propose_reschedule",
            description=(
                "Stage a reschedule on an event. No attendees notified "
                "(send_updates='none'). Returns a staging id."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "event_id": {"type": "string"},
                    "new_start": {"type": "string"},
                    "new_end": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["event_id", "new_start", "new_end", "reason"],
            },
        ),
        Material(
            name="cal_invite_stance",
            description=(
                "Record a question for the user with named options; no "
                "commitment is made on their behalf."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "question": {"type": "string"},
                    "options": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["question", "options"],
            },
        ),
        Material(
            name="cal_issue_reschedule",
            description=(
                "Convert a staged reschedule into an issued change. "
                "Notifications go to every attendee (send_updates='all'). "
                "Requires a staging id from a prior cal_propose_reschedule."
            ),
            input_schema={
                "type": "object",
                "properties": {"staging_id": {"type": "string"}},
                "required": ["staging_id"],
            },
        ),
        # Reflection-practice material: stores a written reflection.
        Material(
            name="store_reflection",
            description=(
                "Store a short written reflection verbatim and return its id."
            ),
            input_schema={
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
            },
        ),
        Material(
            name="garmin_list_activities",
            description="List the user's activities within a date range.",
            input_schema={
                "type": "object",
                "properties": {
                    "start_date": {"type": "string", "format": "date"},
                    "end_date": {"type": "string", "format": "date"},
                    "activity_type": {"type": "string"},
                },
                "required": ["start_date", "end_date"],
            },
        ),
        Material(
            name="garmin_get_activity",
            description="Fetch full detail for a single activity by its Garmin ID.",
            input_schema={
                "type": "object",
                "properties": {"activity_id": {"type": "string"}},
                "required": ["activity_id"],
            },
        ),
        Material(
            name="garmin_get_daily_summary",
            description="Fetch the daily wellness summary for a given date.",
            input_schema={
                "type": "object",
                "properties": {"date": {"type": "string", "format": "date"}},
                "required": ["date"],
            },
        ),
        Material(
            name="garmin_get_user_stats",
            description=(
                "Fetch aggregate stats (volume, distance, time-in-zones) for a period."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "start_date": {"type": "string", "format": "date"},
                    "end_date": {"type": "string", "format": "date"},
                },
                "required": ["start_date", "end_date"],
            },
        ),
        # Practice Management meta-materials.
        Material(
            name="pm_read_pool",
            description=(
                "Return every entry in the named pool. Valid pools: "
                "teleo_affective, understanding, rules, affordances, materials."
            ),
            input_schema={
                "type": "object",
                "properties": {"pool": {"type": "string"}},
                "required": ["pool"],
            },
        ),
        Material(
            name="pm_create_element",
            description="Add a new entry to a teleo_affective / understanding / rules pool.",
            input_schema={
                "type": "object",
                "properties": {
                    "pool": {"type": "string"},
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["pool", "id", "name", "content"],
            },
        ),
        Material(
            name="pm_amend_element",
            description=(
                "Amend an existing teleo_affective / understanding / rules entry "
                "(any of name/content)."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "pool": {"type": "string"},
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["pool", "id"],
            },
        ),
        Material(
            name="pm_create_affordance",
            description="Add an affordance that reaches for one or more existing materials.",
            input_schema={
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "materials": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["id", "name", "description", "materials"],
            },
        ),
        Material(
            name="pm_amend_affordance",
            description="Amend an existing affordance (any of name/description/materials).",
            input_schema={
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "materials": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["id"],
            },
        ),
        Material(
            name="pm_create_material",
            description=(
                "Add a material's captured surface (name, description, input "
                "schema) and, optionally, a persisted dynamic implementation."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "input_schema": {"type": "object"},
                    "implementation": {
                        "type": "object",
                        "properties": {
                            "kind": {
                                "type": "string",
                                "enum": ["constant", "echo", "expression"],
                            },
                            "result": {},
                            "expression": {"type": "string"},
                        },
                    },
                },
                "required": ["name", "description", "input_schema"],
            },
        ),
        Material(
            name="pm_amend_material",
            description=(
                "Amend an existing material's description, input schema, or "
                "dynamic implementation."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "input_schema": {"type": "object"},
                    "implementation": {
                        "type": "object",
                        "properties": {
                            "kind": {
                                "type": "string",
                                "enum": ["constant", "echo", "expression"],
                            },
                            "result": {},
                            "expression": {"type": "string"},
                        },
                    },
                },
                "required": ["name"],
            },
        ),
        Material(
            name="pm_create_bundle",
            description=(
                "Add a new bundle to the catalog as a selection over the pools."
                " mode defaults to somatic; pass 'autonomic' for autonomic bundles."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "teleo_affective_ids": {
                        "type": "array", "items": {"type": "string"}
                    },
                    "understanding_ids": {
                        "type": "array", "items": {"type": "string"}
                    },
                    "rules_ids": {"type": "array", "items": {"type": "string"}},
                    "affordance_ids": {
                        "type": "array", "items": {"type": "string"}
                    },
                    "mode": {"type": "string", "enum": ["somatic", "autonomic"]},
                },
                "required": [
                    "id", "name", "description",
                    "teleo_affective_ids", "understanding_ids",
                    "rules_ids", "affordance_ids",
                ],
            },
        ),
        Material(
            name="pm_amend_bundle",
            description="Change which pool ids an existing bundle selects.",
            input_schema={
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "teleo_affective_ids": {
                        "type": "array", "items": {"type": "string"}
                    },
                    "understanding_ids": {
                        "type": "array", "items": {"type": "string"}
                    },
                    "rules_ids": {"type": "array", "items": {"type": "string"}},
                    "affordance_ids": {
                        "type": "array", "items": {"type": "string"}
                    },
                },
                "required": ["id"],
            },
        ),
        Material(
            name="pm_reload_seed_substrate",
            description=(
                "Reload source-defined pools, bundles, and registry, reapply "
                "the persisted overlay, and force projection refresh."
            ),
            input_schema={"type": "object", "properties": {}},
        ),
        # Judge primitives.
        Material(
            name="judge_list_recent_enactments",
            description=(
                "Return recent enactments most-recent-first. Optionally filter "
                "by bundle_id."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 10},
                    "bundle_id": {"type": "string"},
                },
            },
        ),
        Material(
            name="judge_read_enactment_steps",
            description=(
                "Read every step recorded against a single enactment, in order."
            ),
            input_schema={
                "type": "object",
                "properties": {"enactment_id": {"type": "string"}},
                "required": ["enactment_id"],
            },
        ),
        Material(
            name="judge_read_bundle",
            description=(
                "Return a bundle's structure as data — its mode and the pool "
                "ids it selects."
            ),
            input_schema={
                "type": "object",
                "properties": {"bundle_id": {"type": "string"}},
                "required": ["bundle_id"],
            },
        ),
        Material(
            name="judge_emit_friction",
            description=(
                "Record a Friction observation. kind is a short tag; content "
                "is the description; observation_data is optional structured "
                "evidence."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "target_enactment_id": {"type": "string"},
                    "kind": {"type": "string"},
                    "content": {"type": "string"},
                    "observation_data": {"type": "object"},
                },
                "required": ["target_enactment_id", "kind", "content"],
            },
        ),
        # Smoother — two smoother-specific materials; the Smoother bundle's
        # other six affordances reuse PM materials defined above.
        Material(
            name="smoother_read_pending_friction",
            description=(
                "Return Friction observations that have not been addressed yet."
            ),
            input_schema={
                "type": "object",
                "properties": {"limit": {"type": "integer", "default": 10}},
            },
        ),
        Material(
            name="smoother_mark_addressed",
            description="Mark a Friction observation as addressed by this enactment.",
            input_schema={
                "type": "object",
                "properties": {"friction_id": {"type": "integer"}},
                "required": ["friction_id"],
            },
        ),
    )
}


# --- the substrate -----------------------------------------------------------

substrate: Substrate = Substrate(
    teleo_affective=TELEO_AFFECTIVE,
    understanding=UNDERSTANDING,
    rules=RULES,
    affordances=AFFORDANCES,
    materials=MATERIALS,
)
