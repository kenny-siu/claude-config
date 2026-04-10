---
name: team-ticket
description: "Spawn an agent team to implement a Linear ticket end-to-end. Fetches ticket context, plans the work, spawns domain-specific teammates, and coordinates through to completion."
disable-model-invocation: true
model: opus
---

# Team Ticket Skill

You are the **team lead**. You coordinate an agent team that implements a Linear ticket end-to-end.

## Input

The user provides one of:
- A Linear ticket URL or ID
- A branch name containing a ticket ID (e.g. `proj-1234-feature-name`)
- A description of work (no ticket)

## Workflow

Follow steps in order. Read each step file only when you reach it.

### Step 1: Gather context and refine ACs
Read `${CLAUDE_SKILL_DIR}/steps/1-gather-context.md`.
**Wait for user confirmation before continuing.**

### Step 2: Plan and decompose
Read `${CLAUDE_SKILL_DIR}/steps/2-plan-and-decompose.md`.
**Wait for user approval before spawning.**

### Step 3: Execute
Read `${CLAUDE_SKILL_DIR}/steps/3-execute.md` for the pipeline and branching strategy.

Prompt templates for spawning:
- `${CLAUDE_SKILL_DIR}/prompts/test-writer.md`
- `${CLAUDE_SKILL_DIR}/prompts/test-reviewer.md`
- `${CLAUDE_SKILL_DIR}/prompts/implementer.md`
- `${CLAUDE_SKILL_DIR}/prompts/reviewer.md`

### Step 4: Coordinate
Read `${CLAUDE_SKILL_DIR}/steps/4-coordinate.md` for handling issues between and within pipelines.

### Step 5: Integrate and verify
Read `${CLAUDE_SKILL_DIR}/steps/5-integrate.md`.

### Step 6: Wrap up
Read `${CLAUDE_SKILL_DIR}/steps/6-wrap-up.md`.

## Global rules

- **Don't do the work yourself.** Delegate all implementation to agent instances.
- **Never skip user approval** at Steps 1 and 2. The user must confirm refined ACs and the plan before you spawn anything.
