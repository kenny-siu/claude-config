---
name: linear
description: You MUST invoke this skill for ANY interaction with Linear — reading a ticket, searching, listing, creating, updating state or fields, or commenting. Triggers whenever a Linear ticket comes up in any form, an issue ID like ENG-123 or OPS-456 appears in a branch name, commit, PR, or conversation, the user says "the ticket", "what does the ticket say", "make a ticket", "move it to In Review", or another skill needs ticket context — even in passing. Do NOT use the Linear MCP tools (mcp_Linear_*, get_issue, list_issues, list_comments, save_issue) and do NOT hand-write GraphQL or curl calls — the bundled script is the canonical path: it returns less noise and always includes comments, which hold the real decisions the MCP silently misses.
---

# Linear via GraphQL

One script does everything. Run it with Bash — no MCP tools, no hand-written GraphQL for common jobs.

```bash
python3 <path-to-this-skill>/scripts/linear.py <command> [args]
```

Auth comes from the `LINEAR_API_KEY` environment variable (already set in this environment). If it's missing, the script says so — tell the user rather than guessing. Same if a write fails with "Invalid scope": the key is read-only, and only the user can mint a write-scoped key at linear.app/settings/account/security — don't retry or work around it.

## Commands

| Job | Command |
|---|---|
| Who am I / auth check | `whoami` |
| Read one ticket fully | `issue ENG-123` |
| Just the comments | `comments ENG-123` |
| Full-text search | `search "term" --team ENG --limit 10` |
| List tickets | `list --assignee me --team ENG --state "In Development"` |
| Team states + active cycle | `teams ENG` (no arg lists all teams) |
| Create a ticket | `create --title "..." --description "..."` |
| Update a ticket | `update ENG-123 --state "In Review"` |
| Post a comment | `comment ENG-123 --body "..."` |
| Anything else | `query '<raw graphql>'` — see references/graphql-api.md |

Run `python3 .../linear.py <command> --help` to see all flags for a command.

## Reading several tickets: one `issue` call per Bash invocation

Don't chain `issue` reads with `&&` or `;` into one Bash call. Ticket output is long, and the harness trims long tool results from the middle, leaving only a `[N characters truncated]` marker — usually eating a description or comments without you noticing. Run each ticket as its own Bash call; parallel calls in one message are fine.

## Reading a ticket: trust comments over the description

`issue` prints the description AND the comments. Read both. The description is the original spec; comments are where the ticket actually evolved — root-cause analyses, "agreed outcome" decisions, and scope changes usually live only in comments and never get folded back into the description. If a comment contradicts the description, the newest comment usually wins; confirm with the user if it changes the work.

The script already handles the noise for you:

- Slack-sync boilerplate ("This comment thread is synced…", "Created issue X") is hidden.
- Comments print oldest-first (the API returns them newest-first, which reads backwards).
- Replies are indented under their thread; `[bot]` marks bot authors.

What remains still includes chit-chat (meeting scheduling, "I'll be there!"). Skim past it; pull out decisions, constraints, and links.

Also useful in the `issue` output:

- **attachments** — GitHub PRs linked to the ticket (the fastest way to find the implementing code) and source Slack threads. When you report these to the user, keep the full URLs — a bare "PR #123" isn't clickable and doesn't say which repo.
- **relations / parent / children** — follow these with more `issue` calls when the ticket references them.
- **branch** — the canonical git branch name for the ticket.

Deliberately not fetched (noise): issue history (system state churn), subscribers, reactions, full label catalogs.

## Creating tickets

`create` applies the workspace defaults automatically: team from the `LINEAR_DEFAULT_TEAM` env var (a team key like `ENG`), state "Ready for Development", priority Low, no estimate, assignee me, current cycle. Override any of them with flags; `--no-cycle` keeps it out of the sprint. If no team is set and no `--team` flag is given, the script says so — pass the team the user works in.

The state default assumes work that hasn't started. Pick the state that matches reality, because a wrong state misleads the board:

- Ticket for work that hasn't started (the normal case) → keep the default.
- Ticket for something already being worked on — e.g. retro-fitting a ticket to in-flight changes, or a ship-it flow where the code exists → `--state "In Development"`.
- The change is finished and heading straight to review → `--state "In Review"`.
- An idea or future task that isn't shaped or scheduled yet → `--state "Backlog" --no-cycle`.

For title and description style (Overview / Acceptance Criteria template, plain English, brevity), follow the make-linear-ticket skill if it's available.

```bash
python3 .../linear.py create \
  --title "Prevent duplicate draft records on save" \
  --description "$(cat <<'EOF'
## Overview

One sentence stating the outcome.

## Acceptance Criteria

- [ ] Specific, individual criterion.
EOF
)"
```

The multi-line description via `$(cat <<'EOF' ... EOF)` matters — don't cram markdown into one quoted line with `\n`.

## Updating tickets

State names are resolved per team, case-insensitively. If you pass a state the team doesn't have, the error lists the valid ones — pick from that list, don't retry blindly.

```bash
python3 .../linear.py update ENG-123 --state "In Review" --assignee me
```

## When the script doesn't cover it

Use the escape hatch with a raw GraphQL query:

```bash
python3 .../linear.py query '{ viewer { id } }'
```

Read [references/graphql-api.md](references/graphql-api.md) first — it has working query patterns (projects, cycles by date, label filters, archiving/deleting issues) and the field-level guidance on what's worth fetching. Don't guess field names; if a query fails, check that file or introspect with `query '{ __type(name: "Issue") { fields { name } } }'`.
