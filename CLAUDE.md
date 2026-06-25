# Using Skills

## The Rule

**Invoke relevant skills BEFORE any response or action** — including before asking clarifying questions.

If there is even a 1% chance a skill applies, invoke it first.

## Available Skills (use `Skill` tool)

These are the model-invocable skills in `~/.claude/skills/` — available in every session, regardless of project.

| Skill | When to Use |
|-------|-------------|
| `test-writing` | Before writing, updating, reviewing, or assessing any tests. |
| `code-comments` | Before writing or editing ANY comment in code — inline, block, JSDoc, TODO, or test description. MUST. |
| `reword-plain-english` | When the user asks to reword, simplify, clarify, or rewrite in plain/simple English. MUST. |
| `make-linear-ticket` | Creating a Linear ticket. |
| `review-changes` | Reviewing uncommitted edits or branch commits — runs code, tech-debt, and security reviewers in parallel. MUST. |
| `post-pr-review` | Posting review findings on a GitHub PR as a single pending review for the user to submit. MUST. |

## Process

For every user request:

1. Check: does any **skill** apply? → invoke with `Skill` tool.
2. Announce briefly: "Using `[skill]` to [purpose]."
3. Follow the skill exactly — if it has a checklist, create todos.

## Red Flags (You're Rationalizing)

| Thought | Reality |
|---------|---------|
| "This is too simple for a skill" | Simple tasks become complex. Use it. |
| "I need more context first" | Skills tell you HOW to gather context. Check first. |
| "I'll just write the test quickly" | `test-writing` runs before any test work. No exceptions. |
| "It's only a one-line `//` to explain this bit" | `code-comments` runs before ANY comment — including TODOs and `it(...)` strings. No exceptions. |
| "The user just said 'make this clearer'" | That triggers `reword-plain-english`. Don't reword from memory. |
| "Skill content is the same as last time" | Skills evolve. Read the current version. |

## Skill Priority

1. **Pre-work skills first** (`test-writing`, `code-comments`, `reword-plain-english`) — guide the work itself.
2. **Workflow skills second** (`make-linear-ticket`) — drive specific actions when triggered.

# Reading Orders for Code Changes

When suggesting an order in which to read a code change (PR review, walkthrough, explanation), start at the **impact sites** — the call sites where the changed thing is used — so the reader sees the new way of doing things in context. Then work inward to the changed thing's implementation and its helpers. Put **tests last**.

The shape: `call sites → contexts/types they touch → the change itself → its helpers → deletions → tests`. Each step should answer a question raised by the previous step.

Do NOT default to a foundations-up order (types → helpers → change → call sites → tests) unless the user asks for it. That order builds a vocabulary before showing where it's used, which is the opposite of how this user reads code.
