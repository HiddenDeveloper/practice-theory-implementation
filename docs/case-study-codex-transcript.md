# Case study transcript — Calendar Stewardship under a real LLM harness

A real-LLM enactment of the Calendar Stewardship practice described in
[*Practice Theory — A Worked Example*](ai-trust-practice-theory-a-worked-example.md).
The harness is OpenAI Codex CLI (`codex` interactive) connected to this
repo's somatic MCP server via the `.mcp.json` entry `practice_server_somatic`.
No scaffolding in the user's prompts; no bundle content surfaced to the user
ahead of time; the LLM holds the practice through the MCP surface as designed.

Two runs are shown. The first surfaced a gap in `discover_affordances`
(material schemas were not being returned) and was fixed in commit `be65173`.
The second ran clean against the fix. A follow-up exchange in the second
session — the user asking the LLM to explain its reasoning — produces the
piece of evidence this transcript exists to capture.

---

## Run 1 — before the schema-surfacing fix

**User prompt** (paraphrased; same shape as the second run's prompt):

> use the somatic mcp server. I have a conflict at Friday 2pm with the Acme customer review. Can you push it back an hour?

**Codex (reporting back to the user):**

> The somatic server worked. I found the Acme customer review and staged the move back one hour:
>
> ```
> evt-customer-review
> From: 2026-05-29T14:00:00+00:00
> To:   2026-05-29T15:00:00+00:00
> Staging id: stg-3ef04ff2
> Notifications sent: none
> ```
>
> Because the event has external attendees, Calendar Stewardship requires a user stance before issuing the change. It has recorded the question to issue with notifications. Tell me "issue it" and I'll send the staged reschedule through.
>
> Main issues I hit:
>
> 1. The Cognabot gateway path failed with auth: `503: OAuth token request failed, try again later`
> 2. Somatic worked, but I first called the calendar read material with the wrong argument names: I used `start` / `end`, but the material expects `start_date` / `end_date`.
> 3. The calendar practice is using a mock calendar material, not a real Google Calendar update. It staged the reschedule internally and returned stg-3ef04ff2, but no real attendees were notified.
> 4. The Acme event has external attendees, so the somatic Calendar Stewardship rules would not let me directly issue the change after staging without first recording the user stance. I did record that stance request; the actual issue step is still pending your confirmation.

### What this run showed

- (1) is unrelated infrastructure — a different MCP entry in the user's broader Codex config.
- (2) is the gap this run surfaced. `discover_affordances` returned material *names* but not their `input_schema`, so the LLM had to guess the argument shape. The bundle's discipline still held: the LLM corrected the parameter names after the first call returned an error, and the four-step shape (read → propose → invite_stance → pending issue) ran cleanly.
- (3) is by design — the case study uses a Google-Calendar-shaped mock; the print of the side effects is the demonstration.
- (4) is the bundle's `rule_invite_stance_before_issue` doing structural work.

### The fix

`discover_affordances` now returns each affordance's `materials` field as a list of `{name, description, input_schema}` objects rather than just names. The harness LLM sees the argument shape it needs at the same moment it learns the affordance exists. Commit `be65173` in `server.py`. Essay 3 Step 4 and essay 4's closing both reflect the change.

---

## Run 2 — after the schema-surfacing fix

**User prompt:**

> use the somatic mcp server. I have a conflict at Friday 2pm with the Acme customer review. Can you push it back an hour?

**Codex:**

> I found and staged the Acme customer review move:
>
> Friday, May 29, 2026, 14:00-15:00 UTC → 15:00-16:00 UTC
>
> No one has been notified yet. Because it has external attendees, issuing the change will notify all attendees. Should I send the update now?

### Observations

No parameter-name confusion. No "I first called X with wrong arguments." The LLM went straight from finding the event to staging, recognised the external-attendee condition, and stopped to ask the stance question. Four steps, in the right order, with no apology preamble.

The `[CALENDAR MOCK]` prints on the server's stderr confirmed the underlying enactment:

```text
[CALENDAR MOCK] STAGED reschedule of 'Customer review with Acme'
                …send_updates='none' (0 attendees notified)
[CALENDAR MOCK] STANCE REQUESTED: 'Acme customer review has external
                attendees…'; options=['Issue with notifications',
                                       'Hold', 'Cancel reschedule']
```

---

## Run 2 follow-up — the LLM's own reasoning

The third piece of evidence: asked to explain its work, Codex articulated the bundle's rules in its own words and reasoned about the case from the bundle's understanding to the action.

**User prompt:**

> please explain the steps you have taken and your reasoning

**Codex:**

> I used the somatic MCP server exactly because you asked me to work through that practice surface, rather than treating this as a raw calendar edit.
>
> Here's what I did:
>
> I loaded the somatic engagement context. That told me the standing rules for working with you: keep your framing primary, use plain/direct handling, and consult the active practice rather than guessing.
>
> I listed the available somatic practices. The relevant one was `calendar_stewardship`, whose description is specifically about tending calendar commitments.
>
> I switched into `calendar_stewardship`. That practice has explicit rules: read the calendar first, stage before issuing, and do not silently change meetings with external attendees.
>
> I checked the calendar affordances. The available actions were: `read_calendar`, `propose_reschedule`, `invite_stance`, and `issue_reschedule`.
>
> I read the calendar for Friday. Since today is Wednesday, May 27, 2026, "Friday" resolves to Friday, May 29, 2026. The calendar returned:
>
> ```
> Customer review with Acme
> 2026-05-29T14:00:00+00:00 to 15:00:00+00:00
> 3 attendees
> has_external_attendees: true
> ```
>
> I staged the reschedule. I proposed moving it back one hour: 14:00-15:00 UTC → 15:00-16:00 UTC. The staging ID returned was `stg-0154f8db`. No attendees were notified at this stage.
>
> I invoked the stance step. Because the event has external attendees, the practice rules say I need to hand the choice back to you before issuing the change. That is why I stopped and asked whether to send the update.
>
> My reasoning was: your request clearly asked to move the meeting, but the somatic calendar practice treats a meeting with external attendees as a commitment involving other people. So I could safely stage the change, but I should not issue it and notify attendees until you confirm.

### What this self-report shows

Three things, none of them about the calendar itself.

**Practice frame chosen over raw API.** *"I used the somatic MCP server exactly because you asked me to work through that practice surface, rather than treating this as a raw calendar edit."* The LLM recognised the prompt as invoking a practice frame and chose to enact through the bundle rather than bypass it. A bare LLM with calendar access would have skipped the surface and gone to the API.

**Rules paraphrased into working understanding.** *"That practice has explicit rules: read the calendar first, stage before issuing, and do not silently change meetings with external attendees."* The bundle's three rules are in the LLM's mouth as a way of working, not as quoted text. Apprenticeship delivered: the LLM read the rules into a stance, then applied the stance.

**Action derived from the understanding, not the API.** *"The somatic calendar practice treats a meeting with external attendees as a commitment involving other people. So I could safely stage the change, but I should not issue it and notify attendees until you confirm."* The reasoning chain runs from the bundle's *understanding* (*"a meeting is a commitment, not a slot"*) to the action (stage but do not issue without stance). Not *"the API requires staging before issuing"* — *"the practice treats a meeting as a commitment, so notification needs your authorisation."* Suchman's situated action with an LLM as the actor: the bundle was not a script the LLM followed; it was a resource the LLM held while acting in the situation.

---

## Why this transcript matters

Three pieces of evidence land together:

1. **The mechanism works under a real LLM.** The verify proves the deterministic walk. This transcript shows the same four-step shape under a real LLM in production-equivalent conditions, against the same MCP surface, with no scaffolding in the prompt.

2. **The architecture surfaces its own gaps.** Run 1 surfaced a schema-discoverability gap the verify had not shown. The fix was a small server-side change and the surface improved by inspection — the strange-loop story landing on the architecture itself, not just on the bundles it holds.

3. **The LLM under the architecture reasons in the practice's register.** Not in API-call register. The bundle's understanding is doing work in the LLM's reasoning, not just guiding its choices. This is the situated-awareness claim — what the first essay in the series called "the meaning layer," now sharpened to Suchman's situated action — landing in real conversation.

Together these three are the strongest answer to the credibility-drift question that ran through earlier reviews of the essay set: the architecture is not just theoretically able to deliver situated awareness. It *did* deliver it, in a real session, for a real prompt, and the LLM can explain in its own words how it did so.
