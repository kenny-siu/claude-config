---
name: make-linear-ticket
description: Guide for creating Linear tickets
---

Do any exploration or research you need to understand the issue and fill in the ticket.

# Linear Ticket Guide

Use the Linear MCP tool to create a ticket.

## Defaults

| Field | Value |
|---|---|
| Team | **Not configured yet** -- see setup below |
| Assignee | `me` |
| State | **Not configured yet** -- see setup below |
| Priority | `4` (Low) |
| Estimate | `0` |

### First-time setup

If Team or State say "Not configured yet", run this setup before creating a ticket:

1. **Team:** Call `get_user("me")` to list the user's teams. Ask them to pick one. Note the team ID and name.
2. **State:** Call `list_issue_statuses` for the chosen team. Ask the user which default state they want. Note the state ID and name.
3. **Save:** Update the Defaults table in this file yourself using the Edit tool. Replace the "Not configured yet" rows with the chosen IDs, e.g.:
   - Team: `<team-id>` (Team Name)
   - State: `<state-id>` (State Name)

   This only needs to happen once.

## Title

Concise and action-oriented. Under 100 characters.

## Description

Use this template. Only include sections where you have concrete content — omit any section entirely if there's nothing meaningful to add.

```markdown
## Overview

[High-level summary in domain language, <15 words]

## Acceptance Criteria

[] [High-level domain-scoped acceptance criteria. Each AC should be individual and specific.]

## Additional Resources

* [Links to relevant designs/documentation, if any]
* [Links to related issues, if any]
* [Other helpful context, if any]

## Technical Notes

* [Implementation details, constraints, or technical considerations, if any]
```

## Output

After creating, show:
- **Title**: [title]
- **URL**: [clickable link]
