---
name: code-comments
description: "You MUST invoke this skill BEFORE writing or editing any comment in a code file — inline (`//`, `#`), block (`/* */`), JSDoc/docstring, TODO, or test descriptions like `it(...)` / `describe(...)`. Triggers whenever you're about to add or change a comment, regardless of language. Do NOT decide what to comment using your own judgment first — activate this skill to apply comment rules consistently."
---

# Writing Code Comments

Apply these rules silently to whatever you're about to write. Don't explain that you applied them.

## Default to silence

Most comments shouldn't exist. Before writing one, ask: **"Will removing this confuse a future reader?"** If no, don't write it. Three similar lines beat a clarifying comment that restates them. A future reader can re-derive intent from the code, the diff, and the PR — they can't un-read a stale or misleading comment.

## Two tests every comment must pass

A comment earns its place only if it passes both:

1. **It explains WHY, not WHAT.** A real comment records non-obvious *reasoning* — a hidden constraint, a subtle invariant, a workaround for a specific bug, behaviour that would surprise a reader. If it paraphrases the code, delete it; well-named identifiers already say what the code does.

2. **The WHY is genuinely non-obvious *and* not already carried nearby.** The reader already has the subsystem's `CLAUDE.md`, the `.claude/rules` files, and the names and shape of the surrounding code. So actually read the relevant `CLAUDE.md` and trace the structure before keeping a comment — don't judge it against the few lines around it. If the next reader could derive the same conclusion in 30 seconds, or a doc / sibling comment / self-documenting call (a `ToCounterClockwiseFromAbove()` call already says the result is normalised) already states it, the comment is noise even when it's correct. Cut it.

## A WHAT-comment is a design signal, not a writing task

When you reach for a comment to explain *what* code is or does, stop — the urge means the structure and names aren't carrying their meaning. Change the code, don't narrate it. Roughly in order of reach:

- **Rename** — when one identifier is mislabelled or ambiguous, or a comment explains how a type/function differs from a sibling.
- **Extract** — when a function does several things, or a comparison hides intent. Pull the expression into a named predicate (`x > threshold` → `IsExpired()`, `IsCorner()`).
- **Relocate / scope** — move a value next to its single user (a constant beside the one function that reads it), so it needs no explanation in the wider file.
- **Label inline** — when a comment maps or names the elements of a literal collection, drop a short label on each element (`(1, -1), // NE`) instead of a prose block describing the whole mapping.
- **Simplify** — when the comment would explain *how* a dense expression works ("Min/Max clamps the signed reach to…"), the expression is the problem. This is usually self-inflicted: you contorted the code to satisfy a linter, then reached for a comment to excuse it. Undo the contortion. If you avoided the plain form on a hunch it would break, *test the hunch* before keeping the dense version — usually it's fine.

Only after restructuring, keep a short comment for a genuinely non-obvious *why*. The meaning lives in a name if it possibly can.

Beware the label "non-obvious math": real maths comments record a *why* (why this formula, why this constant is safe), never a paraphrase of *how* the operators combine. If the code isn't actually surprising, that label is a rationalisation for keeping noise.

## Disqualifiers

Strip any comment that does these, even if it passed the two tests:

- **References the current task, fix, or callers** — "used by X", "added for the Y flow", "handles the case from issue #123". Coupling notes rot; provenance belongs in the PR description and `git blame`.
- **Carries a Linear / Jira ticket ID.** The **only** exception is `TODO(SEA-XXXX): …` that defers work to another ticket. Otherwise the ID adds noise without context.
- **Runs long.** One short line is the default. No multi-paragraph docstrings or comment blocks unless the user explicitly asks. No investigation logs or ruled-out approaches — those go in chat or the PR description.

Test descriptions follow the same rules: `it('does X when Y')` describes the behaviour, the assertions describe the rule, no ticket prefix in the string, no "the reason we test this is…" preamble.

## Examples

### Keep — the WHY is non-obvious

```ts
// Backfill uses NOW() rather than each row's createdAt to dodge clock skew
// across read replicas.
```

```ts
// Only delete inferred children — learner-entered answers must survive
// even when the parent flips to EXPERT.
```

```ts
// TODO(SEA-1739): drop once the input-trim work ships.
```

### Strip — restates code, ties to current work, or is already carried

```ts
// SEA-1738: adds parentQuestionComponentId for client inference.
//   ↑ provenance — belongs in the PR description, not source

// Increment the counter
//   ↑ restates code

// Used by SurveyPage to compute next-draft state
//   ↑ coupling note, rots when the caller changes

// Try this approach first; if it fails fall back to bulkCreate
//   ↑ investigation log; the chosen approach is now the code

// Normalised to CCW winding so the mesh faces point up.
//   ↑ true and non-obvious, but the CLAUDE.md doc + the normalise call already say it

it('SEA-1738: should set parentQuestionComponentId on child questions', …)
//   ↑ test description with a ticket prefix
```