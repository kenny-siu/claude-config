---
name: review-changes
description: "You MUST invoke this skill whenever the user asks you to review, check, audit, or critique code changes — uncommitted edits, staged work, or commits in the current branch. Do NOT review code yourself first — activate this skill to run code-reviewer, tech-debt-reviewer, and security-reviewer agents in parallel and consolidate findings. Triggers on phrases like 'review my changes', 'review this branch', 'review the diff', 'check my code', 'what do you think of my code', 'audit these changes', 'is this ready to merge', or any request for a multi-angle code review — even when 'review' isn't named explicitly."
---

# Review Changes

Run a multi-angle review of code changes by spawning three reviewer agents in parallel — `code-reviewer`, `tech-debt-reviewer`, and `security-reviewer` — then merge their findings into one report.

The agents are built for this skill: each takes its scope from the commands you pass, reviews only the diff, and returns findings inline in a shared format (severity, file:line, issue, fix, confidence ≥ 80). Your job is the dynamic part — work out the scope, pass it down, and consolidate what comes back.

**Write the entire output in plain English.** Use short, common words. Keep sentences under 25 words. Avoid jargon — if a technical term is essential, define it right away.

---

## Section 1 — Determine scope

Work out *what* to review before spawning anything. The skill supports two scopes:

- **`uncommitted`** — working tree plus staged edits
- **`branch`** — commits in the current branch that haven't been merged into the base

### How to pick scope

1. **User specified explicitly** — phrases like "review my uncommitted changes", "review this branch", "review my last 3 commits", "review the diff against main". Use what they said.
2. **User said something general** — "review my code", "review my changes". Run both probes:
   - `git status --porcelain` — non-empty means uncommitted changes exist
   - `git rev-list --count <base>..HEAD` — non-zero means commits ahead of base
   - If only one is non-empty → use it. If both → ask the user which (or do both).
3. **No git repo or empty scope** — if `git status` fails, say "not a git repo" and stop. If both probes are empty, say "nothing to review" and stop. **Don't spawn agents on nothing.**

### How to find the base branch

Try in order, stop at the first that works:

1. `git rev-parse --abbrev-ref origin/HEAD` (returns e.g. `origin/main`)
2. `origin/main` if it exists
3. `origin/master` if it exists
4. Ask the user

### Capture scope as exact git commands

You'll pass these to the agents — work them out once and reuse them.

| Scope | Diff command | File list command |
|---|---|---|
| `uncommitted` | `git diff HEAD` | `git status --porcelain` |
| `branch` | `git diff <fork_point>..HEAD` | `git diff --name-status <fork_point>..HEAD` |

For branch scope, compute `<fork_point>` once via `git merge-base HEAD <base>` and substitute the SHA into the commands above.

---

## Section 2 — Spawn agents in parallel

In a **single message with three Agent tool calls**, spawn `code-reviewer`, `tech-debt-reviewer`, and `security-reviewer`. Sending one message with multiple tool calls makes them run in parallel — sending three separate messages does not.

Each agent prompt is just the scope block:

```
Scope: <uncommitted | branch>
Diff command: <the diff command from the table above>
File list command: <the file list command from the table above>
Base: <base branch> (only for branch scope)
Fork point: <sha> (only for branch scope)
```

Everything else — what to look for, the confidence bar, the finding format — is baked into each agent. Their charters:

- **code-reviewer** — bugs, logic errors, type safety, edge cases, project-convention adherence
- **tech-debt-reviewer** — maintainability, duplication, architectural smells, performance bottlenecks
- **security-reviewer** — OWASP Top 10, secrets, input validation, auth, vulnerable dependencies

---

## Section 3 — Consolidate

Once all three agents return, merge their findings into one consolidated review. All three use the same finding shape, so merging is mechanical.

### De-duplicate

Charters barely overlap, so duplicates should be rare. When two agents do report the same issue (e.g. both flag a critical hardcoded key), merge into one entry and attribute it to the most authoritative reviewer for that category:

- Security findings → `security-reviewer`
- Performance / maintainability → `tech-debt-reviewer`
- Bugs / logic / conventions → `code-reviewer`

### Group by severity

Critical → High → Medium → Low. Drop Low-priority findings unless they touch correctness or security.

### Output format

```
## Review Summary

Scope: <uncommitted | branch>
Files reviewed: <count>

| Severity | Count |
|----------|-------|
| Critical | N     |
| High     | N     |
| Medium   | N     |
| Low      | N     |

Verdict: <Approve | Warning | Block>

---

## Findings

### Critical

**1. [CRITICAL] <Title>**
File: path/to/file:line
Issue: <one-line description>
Fix: <one-line suggested fix>
Source: <code-reviewer | tech-debt-reviewer | security-reviewer>

[Repeat for each finding, grouped by severity. Number findings globally — 1, 2, 3… — across all severity groups, so the user can reference "finding 4" without qualifying by severity.]
```

### Verdict rules

- **Approve** — no Critical or High findings
- **Warning** — High findings only, no Critical
- **Block** — any Critical findings

---

## Guiding principles

1. **Problems only** — no praise, no "what's working well", no nits.
2. **Pass scope down** — agents can't read your mind. Give them the exact git commands.
3. **One report, not three** — the user wants the consolidated view, not three raw transcripts. The verdict is yours to compute.
