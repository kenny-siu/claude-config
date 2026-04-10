# Step 1: Gather Context and Refine ACs

## 1a. Fetch and explore

1. **Fetch the ticket.** Use `/fetch-linear-issue` to pull the full ticket — description, comments, attachments, linked issues, and ACs.
2. **Explore the codebase.** Spawn an Explore subagent to find files and patterns relevant to the ticket. Understand what exists before planning changes.
3. **Find the dev loop.** Check project docs (CLAUDE.md, README, Makefile, package.json, pyproject.toml) for lint, format, type-check, and test commands. Record them for later steps.

## 1b. Restate and clarify

4. **Restate the feature in your own words.** Identify the core user-facing behaviour. This forces you to check your understanding.
5. **Ask clarifying questions one at a time** until ambiguity is gone:
   - What are the edge cases? (boundaries, zero values, limits)
   - How does this interact with existing features?
   - What error states are possible?
   - What are the permission and access boundaries?

## 1c. YAGNI challenge

6. **For each requirement, ask: "Is this needed now?"** Cut or defer anything that can't justify immediate need.

## 1d. Write refined ACs

7. **Rewrite ACs as testable statements.** Each must be:
   - Product-focused, not implementation details
   - Written as "the system should..." or "users can..."
   - Observable and testable — specific inputs, actions, expected outcomes
   - Inclusive of edge cases found during clarification

   **Bad:** "Status transitions work correctly"
   **Good:** "When a user sets activity status from 'active' to 'paused', the system updates the status, refreshes `updated_at`, and returns the updated activity. Setting status to an invalid value returns a validation error."

8. **Present the summary and refined ACs to the user:**
   - What the ticket asks for (your own words)
   - Which areas of the codebase are affected
   - Dependencies or blockers
   - The refined ACs
   - Dev loop commands (lint, format, type-check, test)

> **Wait for user confirmation before continuing to Step 2.**
