---
name: review-linear-project
description: >
  Reviews every ticket in a Linear project (or one milestone/phase of it) for
  writing quality, point estimates, correct blocking/blocked-by links, and
  stale comments, and sweeps the project for easily forgotten functionality
  (auditing, undo, personal data, monitoring), then fixes the tickets in
  Linear after the user approves. Use this whenever the user wants a quality pass over a set of
  tickets: "review the tickets in project X", "check the phase 2 tickets",
  "are these tickets ready to pick up", "groom/tidy/audit the backlog",
  "make sure the project's tickets are well written and pointed" — even if
  they only name a project URL. For a single ticket's estimate use
  estimate-tickets; for splitting one ticket into subtasks use
  break-down-linear-ticket. This skill is for sweeping a whole project or
  phase.
---

# Review a Linear project's tickets

Sweep every open ticket in a project (or one phase of it), check each against
the quality bar below, and propose concrete fixes: rewritten titles and
descriptions, corrected point estimates, corrected blocking links, and
replies that clear up stale comments. Then check the project as a whole for
functionality that is easy to forget entirely — auditing, undo, personal
data, monitoring and the like — and raise what's missing as questions.
Nothing is written to Linear until the user approves the full set of
changes.

One other skill does the thinking on estimates: **estimate-tickets** holds
the pointing model. Invoke it before judging any estimate. Don't reimplement
it. If it isn't installed in this session, skip check 7 entirely and tell
the user why — a review pointed against an invented scale is worse than one
that leaves points alone.

## Working with Linear, whatever the tooling

This skill names no particular Linear tooling — use whatever this session
has. The review needs to: read issues with their comments and relations,
update an issue's title, description, and estimate, create issues and
comments, and add or remove blocking relations. If some write operation turns out not to
be available, still do the full review — list those changes in the report
as manual steps for the user instead of failing.

If the session has no Linear tooling at all and you're calling the API
directly, don't construct queries from memory — read
[references/linear-api.md](references/linear-api.md) for known-good ones
covering every step of this skill.

Facts about Linear that trip up reviews, whatever route you take:

- **Issue reads don't always include comments.** Some tools silently omit
  them, and comments are where decisions live — a review that never saw
  them gets checks 3 and 6 wrong by construction. Confirm your first ticket
  read actually returned comments; if not, fetch them separately for every
  ticket before judging anything.
- **Comments usually arrive newest-first.** Read them oldest-first so
  corrections land after the things they correct. Skim past Slack-sync
  boilerplate and bot noise.
- **Writes usually need internal ids, not display identifiers.** Updating
  relations or comments takes the entity's internal id, not "ENG-123".
  Capture the ids of issues, comments, and relations during the read so the
  apply step doesn't need a second lookup.
- **Long responses get truncated.** Read tickets in small batches — a few
  per request — so a cut-off response doesn't silently eat a description or
  the comments.

## Step 1: Resolve the scope

Work out which tickets are in scope. The user may give a project name, a
project URL, or a phase ("phase 2 only"). Phases are usually project
milestones.

Resolve the project first — by name search, or from the URL (the hex after
the last hyphen in `.../project/my-project-abc123def456/...` identifies the
project). Then list its milestones, match the phase to a milestone by name,
and list the issues in that milestone — or in the whole project if no phase
was given — with identifier, title, estimate, and state.

**Skip tickets whose state type is `completed` or `canceled`.** Rewriting
finished work churns history for no benefit. Tell the user how many you
skipped. Review `started` tickets but be conservative about proposing rewrites
— someone is mid-flight on them.

## Step 2: Read the project, then every in-scope ticket

Start with the project itself, not the tickets: read the project's
description and any documents linked from it. That content often answers
questions the tickets don't, and the Step 4 sweep needs it to judge what
the project plausibly requires. If the project has no description at all,
note that as a finding for the report.

Then read each in-scope ticket in full. A complete read includes:

- the description,
- every comment, with author, date, and thread structure (plus the ids —
  the apply step replies to and resolves specific comments),
- relations in **both directions** — who this ticket blocks and who blocks
  it, with the relation ids,
- estimate and state.

Comments and relations both matter here: decisions and scope changes often
live only in comments, and the relations are what check 5 judges. Keep
per-ticket notes of the blocks/blocked-by links as you read, so you can
check the graph as a whole afterwards.

If the scope is large (more than ~25 open tickets), review in chunks of
around ten so nothing gets truncated or skimmed, and keep running notes per
chunk before writing the report.

## Step 3: Review each ticket

Judge every ticket against these seven checks. The bar: **someone new to the
project, with no prior context, could pick the ticket up and know what to
build, why it matters, and when it's done.**

Sometimes a check can't be judged because the ticket doesn't say — the facts
are missing, not wrong. Don't guess, and don't silently pass the check.
Record it as a question for the report's Open questions section, naming the
ticket it affects.

### 1. Title

The title says what the change delivers, in product terms — not which layer
it touches or how it's built.

- Good: "Let Support add a verified tax ID to a customer"
- Good: "Course status filtering"
- Bad: "Add GraphQL mutation for tax ID" (implementation detail)
- Bad: "Backend — move logic" (layer, not outcome)
- Bad: "tax-ID work pt 3" (says nothing)

### 2. Plain English

The description reads as plain English:

- Short sentences (aim under 25 words) and short paragraphs.
- Common words; active voice.
- **No metaphors.** "The importer starves", "the change lands", "surfaces
  errors", "a danger window", "guardrails" — replace each with the literal
  fact it stands for.
- Jargon and project shorthand defined on first use, or removed. An acronym
  the whole company knows (say, the product's own name) is fine; a
  project-private codename is not.

Run this scan on every ticket no matter how the user framed the request —
"ready to pick up" and "well written" both include "reads plainly". The
framing of the ask must not pull you off this check. And hold your own
replacement text to the same rules: don't fix one metaphor and write
another.

### 3. Standalone context

The description gives enough context that the reader needs nothing else:

- Why the ticket exists and how it fits the project's goal — one or two
  sentences, not the whole project history.
- What it builds on and what depends on it, with ticket references the
  reader can follow (Linear auto-links bare IDs like ENG-123 — that's fine,
  don't flag the format).
- Decisions made in comments that changed scope are folded back into the
  description.
- Coordination tickets name the counterpart: the team, the contact person,
  and where the conversation happens. "Waits on the data team" with nobody
  to chase means the ticket quietly rots.

### 4. Acceptance criteria

- Every criterion is an observable end state ("Support can enter a tax ID"),
  not an implementation step ("add a column").
- The set is complete: nothing the ticket clearly requires is missing, and
  there are no unresolved placeholders ("TBD", "work out later") — unless
  working that out is explicitly the ticket's job.
- **No routine criteria.** Tests, regenerated GraphQL types, linting, code
  review — the team's Done bar already covers these. Flag them for removal;
  never flag their absence.
- Out-of-scope items are marked as such, at the end.

### 5. Dependency links

The blocking/blocked-by graph in Linear tells the truth about ordering.
Check it both ways:

- Every ordering constraint stated in prose ("gated on X", "runs after Y",
  "must land before Z") exists as a blocks/blocked-by relation.
- **Walk every existing block link and justify it**: state in one sentence
  what work product the blocked ticket needs from its blocker before its
  own work can start or finish. Then apply the removal test: **could
  someone pick up the blocked ticket today, with the blocker never
  started, and finish it to its acceptance criteria?** If yes, propose
  removing the link. If the need is really met by a different ticket —
  often one that was split out of the blocker — the link points at the
  wrong ticket and quietly serialises work meant to run in parallel. Don't
  mark a ticket's links as passing unless you walked them; an unexamined
  link is not a passing link.
- **Runtime direction is not build order.** "A calls B", "A queues the
  worker that B implements", "A's page shows B's data" describe how the
  finished system flows, not the order to build it in. Either side can
  usually be built first against an agreed contract — the message shape,
  the API schema, the interface. If the contract isn't agreed yet, the
  real dependency is agreeing it, which is far smaller than the other
  ticket. "The feature doesn't work until both exist" argues for shipping
  together, not for building in sequence — it justifies no link. Treat a
  justification that only restates runtime flow as a failed justification.
- No links to canceled or superseded tickets.
- Where early work hides inside a late ticket (a design decision that must
  happen before the chain's first ticket, owned by a ticket at the chain's
  end), flag it — the blocking graph will make someone open it too late.
- **Look for extractions that unblock several tickets at once.** When one
  ticket blocks two or more others, or heads a long chain, ask what the
  blocked tickets actually need from it. Often it's a small slice: an
  agreed contract, a stubbed API, a schema, a decision. Propose extracting
  that slice into its own small ticket — the blocked tickets then depend
  only on the slice, and the rest of the original ticket runs in parallel
  with them. Example: pulling "define and stub the API" out of a backend
  ticket unblocks the frontend tickets (they build against the stub) and
  the backend ticket itself (it implements the real thing behind the
  stub). Extraction repackages work without adding scope, so propose it
  fully drafted and let the user decide.

### 6. Comment hygiene

Comments are where tickets rot. A comment that later decisions have made
wrong is a trap for the next reader, because comments read as history and
nothing marks the wrong one as superseded.

- A stale comment gets a **short correcting reply**: what changed, and where
  the current truth lives. Never edit or delete someone else's comment —
  the thread is the record.
- If the corrected content is already in the description, propose
  **resolving the thread** with that reply, so it collapses out of the way
  but stays expandable. If it isn't in the description yet, that's a
  description fix first (check 3), then resolve.
- Ignore chit-chat and Slack-sync noise — only correct comments that would
  mislead someone doing the work.

### 7. Points

Invoke the **estimate-tickets** skill and score each ticket with its model
(interface size first, coordination second — never code volume). Where your
score disagrees with the current estimate, propose the change with a
one-line reason. Then sanity-check the whole batch's spread as that skill
describes.

## Step 4: Sweep the project for forgotten functionality

Checks 1–7 judge each ticket on its own. This step judges the project as a
whole: some functionality is easy to forget entirely, so no ticket fails a
check — the ticket just doesn't exist.

For each item below, ask two things: does this project's functionality
plausibly need it, and if so, does any ticket cover it? Raise an item only
when the answer is "plausibly yes" and "nothing covers it" — and give the
one-sentence reason you think it applies. Judge against the project
description and tickets read in Step 2; don't flag items the project
clearly doesn't need. Raise each finding as a question in the report's
Open questions section, never as a drafted ticket. These items are often
skipped on purpose — the review's job is to make sure the skip was a
decision, not an accident.

- **Auditing** — who changed what, and when. Matters for anything
  Compliance or a regulator might later ask about.
- **Undo** — can a user reverse their own change? If not, what's the
  recovery path when they make a mistake — support ticket, admin tool,
  an engineer?
- **Personal data** — does the project collect, share, or process personal
  data in a new way? If the pave-compliance-checker skill is available,
  invoke it to judge whether a privacy process applies; if not, still
  raise the question and name the data that made you ask.
- **Permissions** — who is allowed to use the new functionality? New
  actions often ship with no role check because nobody wrote one down.
- **Existing data** — do rows that already exist need a backfill or a
  migration? Tickets describe the new world and forget the data already
  in the database.
- **Failure and empty states** — what does the user see when the feature
  breaks, or when there's nothing to show yet?
- **Rollout** — is a feature flag needed? What happens to work that's
  mid-flight when the feature turns on or off?
- **Measuring impact** — how will the org know the project worked? If
  success isn't observable in existing data, something must record the
  numbers: analytics events, a dashboard, a report.
- **Monitoring and alerts** — when a new job, integration, or sync fails
  silently, who finds out, and how?

## Step 5: Report

Print the full review in chat before touching Linear. Use this structure:

```markdown
## Ticket review: <project> — <scope>

Reviewed N tickets (skipped M completed/canceled).

### Summary

| Ticket | Title | Plain English | Context | ACs | Links | Comments | Points |
|--------|-------|---------------|---------|-----|-------|----------|--------|
| ENG-123 | ✅ | ⚠️ metaphors | ✅ | ✅ | ⚠️ missing block | ✅ | 2 → 1 |

### ENG-123: <current title>

**Findings:** <what fails which check, briefly>

**Proposed description:** <the full replacement text, ready to paste>

**Proposed link changes:** <e.g. "add: blocked by ENG-100 (prose says gated
on it); remove: blocks ENG-101 (re-serialises the split)"> — omit if none

**Proposed comment replies:** <the reply text in full, plus "resolve thread"
where the description already carries the correction> — omit if none

**Points:** 2 → 1 — <one-line reason>

### Tickets that pass

- ENG-124 — well formed, points agree.

### Proposed extractions

**New ticket: Agree and stub the signup API** — extracted from ENG-130.

<full draft description, ready to create>

**Points:** 1 — <one-line reason, scored with estimate-tickets>

**Link changes:** ENG-131 and ENG-132 become blocked by the new ticket
instead of ENG-130; the new ticket blocks ENG-130 (the real implementation
builds behind the stub).

**ENG-130 description change:** <the updated text, with the extracted work
removed and the new ticket referenced>

### Open questions

- Nothing covers auditing of manual tax-ID edits — Support may need the
  history. Was leaving it out a decision?
- ENG-123 stores the customer's tax ID from a new source. Does that need a
  privacy process before it ships? (affects ENG-123)
```

Rules for the report:

- Propose **full replacement text**, not advice like "add more context".
  The user approves text, not intentions.
- Only propose a rewrite when it materially helps. A ticket that passes gets
  one line. Wholesale rewording of fine tickets is churn, and churn makes
  the real fixes harder to review.
- Keep each ticket's voice and facts — you are editing for clarity, not
  re-deciding scope. If you spot what looks like a genuine scope problem,
  raise it as a question in the report instead of silently changing it.
- Every open question says why it came up and which tickets it affects (or
  that it's project-wide). Questions are for things the review genuinely
  couldn't judge — not a place to park weak findings.
- Omit the Proposed extractions and Open questions sections entirely when
  there are none.

## Step 6: Apply after approval

Wait for the user to approve. They may approve everything, or only some
tickets — apply exactly what they approved, nothing more.

Apply one ticket at a time, so a failure part-way is easy to see and pick
up from. The operations, and what trips each one up:

- **Title, description, estimate** — a description update replaces the
  whole text, it doesn't patch it. Always write the full agreed description,
  never a fragment.
- **Add a blocking link** — blocking relations have a direction; double-check
  which ticket is the blocker before writing. Getting it backwards inverts
  the project's ordering and is easy to miss in review.
- **Remove a wrong link** — use the relation's own id captured in Step 2.
- **Create an extracted ticket** — create it in the same project (and
  milestone, if the scope was one) with the agreed title, description, and
  points. Then rewire the links: add the new relations, remove the old
  ones by their relation ids. Finally update the original ticket's
  description as agreed, so the extracted work isn't described in two
  places.
- **Reply to a stale comment** — create the reply inside the stale comment's
  thread (as a child of it), not as a new top-level comment, or the
  correction ends up detached from the thing it corrects.
- **Resolve the thread** — resolve it with the correcting reply, so the
  collapsed thread shows the correction. Only resolve when the correction
  already lives in the description (possibly because you just updated it in
  this same run). If your tooling can't resolve threads, post the reply
  anyway and list the resolve as a manual step for the user.

Each open question gets one of three outcomes, chosen by the user:

- **They answer it in chat** — fold the answer into the affected ticket's
  description (a normal description update, held to the same checks).
- **They ask you to post it** — write it as a comment on the affected
  ticket, or on the project when it belongs to no single ticket, so the
  person who knows can answer in Linear. Never post a question to Linear
  without the user choosing this.
- **They drop it** — leave it out of the applied changes entirely.

Unaddressed questions stay open: list them at the end of the run so they
aren't lost.

Then report what changed, with links, and what was left alone.
