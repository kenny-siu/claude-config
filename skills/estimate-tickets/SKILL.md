---
name: estimate-tickets
description: >
  You MUST invoke this skill whenever assigning, agreeing, recalibrating, or
  sanity-checking story-point estimates on Linear tickets. Triggers on phrases
  like "estimate these tickets", "point this", "add story points", "how many
  points", "size this ticket", "re-point the backlog", or any request to put
  numbers on tickets. Do NOT size tickets from your own gut first — activate
  this skill so estimates stay consistent across sessions and people.
---

# Estimating tickets

## The one idea

A point is **not** a measure of how much code there is to write. AI writes code
almost instantly, so typing effort is close to free. A point measures **how much
human attention the ticket consumes to reach Done**. That attention goes two
places:

1. **Size of interface with the existing codebase** — the dominant factor.
   Wide interfaces eat attention in careful review, testing, and nervous
   deploys.
2. **Coordination loops** — the second factor. Threads we drive with other
   people eat attention in rounds of agreement, training, and verification.

Because points measure attention, a project's total should roughly track how
long it takes. Everything below is a way to score the two factors
consistently.

## What a point measures

### 1. Size of interface with the existing code (main factor)

How much does this change wire into the existing platform code? This team's
code is largely legacy and tangled, so the more of it a change touches, the more
scared we are to deploy it and the longer it takes to review. That fear is the
point value.

Count the number of **existing** code paths, modules, hooks, and read/write
sites the change threads into. A change that touches four existing write paths
is expensive. A change that adds a self-contained new module is cheap, even if
the module is large.

Logic complexity counts a little here too — genuinely tricky logic (concurrency,
idempotency) adds a bit — but only a little. Weight the breadth of the interface
far more than the cleverness of the logic.

### 2. Coordination loops (second factor)

Score coordination by counting the **loops** we drive. A loop is one round of
human back-and-forth: agreeing something, training someone, scheduling
something, verifying something. "Another team is involved" alone earns
nothing — count what we actually do.

- **A single handoff** — ask once, receive, sign off — adds nothing. The
  ticket stays a **1**.
- **One sustained thread** — a multi-round agreement, or an agreement plus a
  verification sweep of our own — is worth about **1 point** of attention.
  That's comparable to a small self-contained code change: pure code needs
  little human work, but not none, and a sustained thread costs more than a
  handoff.
- **Several distinct loops**, or loops choreographed with our own build
  (train a team, schedule against our deploy, re-run an import), push the
  ticket to **2**.
- **Many parties or loops sustained over weeks** push it to **3**.
- Coordination alone earns a **5** only when we personally have days of
  hands-on work driving it — say, building the tooling for a case review and
  then driving hundreds of cases through it. This is rare. Be suspicious of
  any coordination 5.
- **Working across multiple repos is a small factor.** A nudge, not a leap.

Examples (generalised from real tickets):

- Another team retires a tool once we sign off → single handoff → **1**.
- Agree data-handover mechanics with another team — options, schema,
  credentials, a join-key check → one sustained thread → **1**.
- A workflow switchover: agree it with two stakeholders, train their team,
  and schedule it against our own deploy plus a re-run → several loops → **2**.
- Drive a data cleanup with two other teams over weeks — agree the policy,
  run a scripted pass, then support their review of hundreds of live
  cases → **3**.

## What a point does NOT measure

- **Volume of code.** A big greenfield module you write in one sitting is still
  small if it barely touches existing code.
- **A clean external API.** Calling a well-defined third-party or government
  service is cheap, however important it sounds. The interface is defined and
  stable — that's the opposite of scary.
- **An observability dashboard.** These are just Datadog, so they're
  straightforward — score them a **1**. Don't bump to a 2 for "spans a separate
  tool"; Datadog is the default home and adds no real interface risk.
- **External wait time.** Being blocked on another team is tracked by the
  ticket's blocking relations, not by its points. Waiting costs no attention —
  don't inflate the number to represent it. Only the loops we actively drive
  count.
- **Calendar time.** A 2 that sits in review for a week is still a 2.

## The scale

The team this scale was calibrated for uses Linear's **linear** estimation
scale, **extended**, with **zero allowed** — so the values are 0–7. Work with the set
**0, 1, 2, 3, 5**. Reach for 4, 6, or 7 only when nothing else fits; needing one
usually means you're wavering between two anchors.

| Points | Anchor |
|--------|--------|
| **0** | A spike. Not counted — its effort is treated as spread across the project. |
| **1** | Greenfield or isolated code (even a large chunk), OR coordination up to one sustained thread. |
| **2** | Touches a little existing code (one hook or surface), OR several coordination loops / loops choreographed with our own build, OR spans a separate tool/repo. First-integration uncertainty can also sit here. |
| **3** | Wires into several existing code sites, OR many-party coordination sustained over weeks. |
| **5** | The widest interface into the legacy code (many existing paths). Coordination alone gets here only with days of personal hands-on work. |
| **7** | Bigger or less certain than a 5 — usually a sign to split it or spike it first. |

## Spikes are 0

A spike always scores **0**. It's the vehicle for uncertainty, its output is a
decision rather than a deliverable, and its effort is considered spread across
the project rather than booked against one ticket.

## When you can't size it

If there's enough uncertainty that you genuinely can't pick an anchor, **don't
guess**. That's the signal to carve out a spike to flesh it out first, and leave
the original unsized until the spike lands. Most work is known enough to size —
this is the exception, not the default.

## What "done" the estimate covers

Everything to get the ticket to the team's Done bar: implementation, tests, and
PR review cycles. Not the external waits above.

## Sanity-check the distribution

A healthy backlog under this model **skews small**: lots of 1s and 2s, a thin
middle of 3s, and only a few 5s — and those 5s are almost always the
widest-interface tickets, not the ones with the most code or the most
meetings.

If you find yourself handing out lots of 3s, you're probably scoring code
volume instead of interface size. Re-check each 3: if it's a big but
self-contained change, it's really a 1 or 2.

## Calibrate the project total

After pointing a whole project or phase, add up the points and divide by the
team's usual velocity. Does the implied duration match your instinct for the
work? If it's far off, don't smear points across the batch — find the
individual tickets whose loops or interfaces you mis-counted and re-score
those.

## Process

1. **Read the ticket properly** — description and comments. Decisions and scope
   changes usually live in the comments.
2. **Score the interface:** how many existing code paths does it thread into?
   That sets the base value.
3. **Add coordination:** count the loops we drive (see factor 2) and nudge up
   accordingly. Repos spanned add a small nudge.
4. **Discount the noise:** ignore raw code volume, clean external APIs, clever
   logic, and any waiting time.
5. **Pick the anchor.** Spike → 0. Can't pick → spike it, leave unsized.
6. **Sanity-check the spread and the total** across the whole batch before
   committing (see "Calibrate the project total").
7. **Update the Linear ticket** with the chosen estimate.

## Applying to a different team

The scale above is specific to one team. Before estimating another team's tickets, check
its estimation scale in Linear so your numbers fit the tooling — the available
values differ by team.

The two-factor model (interface size + coordination) carries over; only the
available numbers change.
