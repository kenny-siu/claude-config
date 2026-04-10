---
name: review-pr
description: Review the PR for the current branch against its Linear ticket.
disable-model-invocation: true
---

# Review PR

Review a pull request against its Linear ticket requirements and evaluate code quality. Report problems only — no strengths, praise, or minor style nits.

**Write the entire review in plain English.** Use short, common words. Keep sentences under 25 words. Avoid jargon — if a technical term is essential, define it right away. Explain things in terms of what they do, not how they're built.

---

## Phase 1: Identify Branch and Changes

1. Get the current branch: `git rev-parse --abbrev-ref HEAD`
2. Extract the ticket ID from the branch name (e.g., `PROJ-123` from `proj-123-feature-name`)
3. Find the fork point: `git merge-base HEAD <base_branch>` — this isolates changes made in this branch only
4. Get the diff and file list:
   - `git diff <fork_point>..HEAD`
   - `git diff --name-status <fork_point>..HEAD`
5. Read all changed files to understand the scope, relationships, and nature of changes

**Error handling:**
- Can't determine base branch → ask the user
- Can't find fork point → fall back to direct comparison with base branch, inform the user

---

## Phase 2: Load Linear Ticket

1. Extract the ticket ID from the branch name. If none found, ask the user.
2. Fetch the ticket via `mcp_Linear_get_issue`. If not found, ask the user to verify the ID.
3. Store title, description, and acceptance criteria for use in later phases.

---

## Phase 3: Review Against Acceptance Criteria

### Extract and map criteria
- Parse the ticket for acceptance criteria (sections labelled "AC", "Requirements", checkboxes, numbered lists, etc.)
- For each criterion, determine whether the code changes fully meet, partially meet, or don't address it
- Also check for technical, integration, or documentation requirements in the ticket description and comments

### Report only problems
- **Partially met** or **not met** criteria → report as problems
- **Fully met** criteria → do not mention
- Additional requirements not addressed → report

---

## Phase 4: Code Quality Review

For every category below, only report **significant** problems. Skip minor style preferences, small optimizations, and trivial improvements.

### 4.1 Patterns and conventions
- Compare to similar existing code: imports, naming, organization
- Report only significant deviations from established patterns

### 4.2 Structure and organization
- Separation of concerns violations, significant duplication, excessively large functions/classes
- Excessively nested or complex conditional logic, problematic magic values

### 4.3 Error handling
- Missing, inappropriate, or unhelpful error handling
- Unhandled edge cases, especially those mentioned in acceptance criteria

### 4.4 Type safety
- **Python:** Missing required type hints, incorrect types that could cause bugs
- **TypeScript:** Unnecessary `any` types hiding real issues, type mismatches risking runtime errors

### 4.5 Security and performance
- **Security:** Real vulnerabilities (SQL injection, XSS, auth bypasses), missing input validation, improper handling of sensitive data
- **Performance:** N+1 queries, clearly inefficient algorithms or DB queries, significant unnecessary computation

### 4.6 Documentation
- Missing docs for complex code that's hard to understand, misleading or incorrect comments
- Skip minor documentation gaps or style preferences

### 4.7 Test coverage
- Missing tests for critical new functionality or edge cases that could cause bugs
- Skip minor coverage gaps or style differences

### 4.8 Bugs and logic issues
- Obvious bugs, incorrect logic, boundary condition errors
- Off-by-one errors, incorrect comparisons, missing null checks, race conditions

### 4.9 Event publishing
Only check when changes involve significant business actions (entity creation/deletion, state transitions, user-facing actions):
- Compare to similar existing code to see what events are normally published
- Report missing events for important state transitions that follow established patterns
- Don't suggest events for read-only operations or where no pattern exists

---

## Phase 5: Compile Review Summary

### 5.1 Change summary

Before listing problems, explain what changed. This helps reviewers understand the code before evaluating it.

**File ordering:** Start with foundational changes (models, types, utilities) and build up to higher-level changes (components, pages, endpoints). Each file should introduce only one new concept, building on what came before.

**Short filenames:** Use only the base filename (e.g., `update_pathway.py` not the full path). Add parent directory segments only when two or more changed files share the same name — and only enough to disambiguate (e.g., `pathway/models.py` vs `course/models.py`).

**Plain language:** Explain what changes accomplish, not implementation details. Avoid jargon.

**File formatting:** Each file gets its own block — filename on one line (bold, backticks, linked), description on the next, blank line before the next file:

```
**`update_pathway.py`**
Adds validation for supplemental pathway types before saving.

**`models.py`**
New `is_supplemental` property on the Pathway model.
```

### 5.2 Findings

Report only problems, grouped by category:
- **Acceptance criteria issues** — partially met or unmet criteria only
- **Code quality problems** — significant issues only
- **Bugs found** — bugs and logic errors
- **Security/performance problems** — real vulnerabilities and clear inefficiencies
- **Event publishing issues** — missing events for important business actions

Test plan execution is handled separately by `test-pr`.

### 5.3 Recommendations

For each problem:
- Clear description of what's wrong — for nuanced or complicated issues, include an illustrative example showing how the problem could happen (e.g., "if a user does X, then Y breaks because Z")
- Why it matters — again, use a concrete example if the impact isn't immediately obvious
- Suggested fix — include a short code example if it helps make the fix concrete
- Priority: critical, high, medium, or low

Filter out low-priority issues unless they're critical to functionality.

---

## Guiding Principles

1. **Problems only** — no strengths, praise, or "what's working well"
2. **Significant issues only** — skip minor style, trivial optimizations, small nits
3. **Codebase standards, not personal preferences** — judge by existing patterns
4. **Acceptance criteria first** — verifying requirements is the primary goal
5. **Be concise** — report only what needs to be addressed

---

## Error Handling

- No ticket ID extractable → ask the user
- Linear ticket not found → ask the user to verify the ID
- Base branch unclear → ask the user which branch to compare against
- Fork point not found → fall back to direct base branch comparison, inform the user
- Changes unclear → read more surrounding context or ask for clarification
