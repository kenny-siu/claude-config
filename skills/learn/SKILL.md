---
name: learn
description: Capture a lesson from the recent conversation (or a user-specified topic) into the right Claude config — personal `~/.claude/CLAUDE.md` or project root `CLAUDE.md`/`AGENTS.md` for always-on rules, `<repo>/.claude/rules/<name>.md` for path-scoped rules, or an active skill's `SKILL.md` when the rule is scoped to that skill.
disable-model-invocation: true
args:
  - name: ARG
    description: "Optional. What to learn. If omitted, infer the lesson from the recent conversation."
---

# Learn

Turn a lesson into a durable rule in a Claude config file. Apply the edit; the user can redirect afterwards.

## Step 1 — Identify the lesson

If `{{ARG}}` is given, refine it into a single rule.

Otherwise scan the recent conversation for the strongest candidate:
- **Corrections** — "no, don't…", "stop doing X"
- **Validated choices** — "yes exactly", silent acceptance of an unusual approach
- **Surprises** — a non-obvious codebase fact (hidden constraint, gotcha)

If nothing clearly stands out, ask one short question instead of guessing.

## Step 2 — Pick the home

Match the rule's scope to the destination's scope. Don't path-scope a rule that always applies; don't promote a path-specific rule to always-on. If two homes genuinely fit, pick the better and flag the call in your report.

### Always on, every project — `~/.claude/CLAUDE.md`

Personal config. Loaded in every session, regardless of repo.

### Always on, anywhere in this repo — project root config

First of `<repo>/CLAUDE.md`, `<repo>/AGENTS.md`, `<repo>/.claude/CLAUDE.md`. If `CLAUDE.md` is a symlink to `AGENTS.md`, edit the underlying `AGENTS.md`. If both exist as real files or if none exist, ask before creating one.

### Only for files matching a glob — `<repo>/.claude/rules/<name>.md`

A rule with `paths:` frontmatter loads only when Claude reads a matching file. Pick `<name>` as a short kebab-case topic (e.g. `testing.md`, `api-design.md`); each file covers one topic, so update an existing topic file in place. Create `.claude/rules/` if missing — it's Claude-Code-specific, so no `AGENTS.md` symlink dance applies.

Frontmatter format, one glob per quoted list item:

```markdown
---
paths:
  - "apps/backend/**/*.ts"
  - "apps/backend/**/*.test.ts"
---

# <Topic heading>

<rule body>
```

Globs support brace expansion (`**/*.{ts,tsx}`). Use the narrowest globs that capture the rule's real scope — over-broad globs load the rule on unrelated work. A file with no `paths:` frontmatter loads unconditionally; if that's the intent, use the always-on destination instead.

These rules are Claude-Code-specific. Other agents (Cursor, Codex) won't see them. If the rule needs to reach those tools too, flag that in your report so the user can mirror it manually.

### Only when active skill X is doing its thing — that skill's `SKILL.md`

Active skills appear in the session's `<system-reminder>` skill list. First of `<repo>/.claude/skills/<name>/SKILL.md`, then `~/.claude/skills/<name>/SKILL.md`. Never edit a plugin skill (anything under `.claude/plugins/**`) — plugin files are vendored and overwritten on update. If only a plugin copy exists, pick the next-best home, or offer to create a project/user skill that overrides the plugin one.

Don't shoehorn a general rule into a skill because the skill mentions a related keyword.

## Step 3 — Place and write the rule

Treat the file as documentation for how things should be done, not a log of lessons. Find the relevant section and add, update, or remove content there; add a new section only if none fits. Match the file's existing structure (headings, ToC entries, code-block style, tone) and keep the change concise. If you overwrite a contradicting rule, flag it in your report.

## Step 4 — Report

Make the edit. Then report in three lines:

```
Learned: <one sentence>
→ <path> · <section heading or paths: glob>
Reason: <one line>
```

Add one extra line for any judgement call — picked between two homes, overwrote a contradicting rule, created a new file or directory, the rule is Claude-Code-only — so the user can correct course.
