---
name: push-pr
description: Push the current branch and open a draft GitHub PR with a Linear-aware description that follows the repo's PR template. Use when the user says "push pr", "raise pr", "open pr", "create draft pr", "push and open pr", or otherwise wants to ship the current branch up for review.
---

# Push Branch and Open Draft PR

Fetch the Linear ticket, draft a PR description from the cumulative diff, push the branch, open a draft PR with `gh`, then comment `@cursor review`.

---

## 1. Validate the branch

- Refuse to run on `main` / `master` — ask the user to switch.
- Identify the base branch (default `main`, fall back to `master`); ask if neither exists.
- Extract the ticket ID from the branch (e.g. `PROJ-123` from `proj-123-feature-name`); ask the user if it isn't present.

---

## 2. Fetch the Linear ticket

Use the Linear MCP or the CLI: `linear issue show <id> --format json`. Always capture **title, description, comments, and `url`**.

Fetch extra context only when it would change the PR framing:

- **Linked docs / attachments** when designs, RFCs, or specs shape the change.
- **Parent project / initiative** when the PR is one of several tied to a larger piece of work.
- **Related tickets** (blockers, sub-issues, "relates to") when a sibling explains the shape of this one.

If the ticket is self-contained, skip the extras. If fetching fails, ask the user for the title and URL.

---

## 3. Review the changes

The PR description must reflect the **net diff between `origin/<base>` and `HEAD`** — not the journey. Intermediate commits (bug introduced and fixed in a later commit, "address review feedback") are not standalone changes.

- `git diff origin/<base>...HEAD` is the source of truth for **what** changed.
- `git log` provides context for **why** — never describe intermediate commits as bullets.
- Cross-reference the ticket's requirements and acceptance criteria.

---

## 4. Draft the PR description

Read `.github/pull_request_template.md` and fill out **every section** in it (mark non-applicable sections "N/A" or leave empty per template convention). If the template is missing, fall back to: Linear ticket, Summary, What changed and why, How to review, Risk and rollback, How to test.

### Section guidelines

- **Linear ticket** — `[PROJ-XXX](linear-url)` using the `url` from the ticket JSON.

- **Summary** — one sentence in plain English, leading with user/system impact.
  - Example: "Show course enrollment count on the course card so learners can see at a glance how many peers are on the same course."

- **What changed and why** — 2–5 bullets describing the **net diff** vs the base branch. Each bullet leads with impact, not file names.
  - **Do not narrate the journey.** A bug introduced and fixed in the same branch is part of the final behaviour — the base branch never saw it.
  - ❌ Bad: "Concurrent deliveries for the same goal id no longer orphan an FCG — only the worker that inserts the goal builds." (Implies the base branch had this orphaning behaviour — but FCGs weren't associated with goals at all before the PR.)
  - ✅ Good: "Goal-keyed FCG creation is concurrency-safe — only one worker per goal id inserts and builds; concurrent deliveries fall back to a scoped UPDATE."
  - Example bullets:
    - Course cards now display the enrollment count (new badge component)
    - Enrollment count refreshes when learners join or leave a course
    - Added a backfill job to populate counts for existing courses

- **How to review** (bullet list) — point reviewers at the focus area; flag tricky, non-obvious, or out-of-scope bits.
  - If genuinely straightforward: `- Nothing tricky — review in any order.`
  - Examples:
    - `` - Start with `EnrollmentCounter.tsx` — the rest is wiring. ``
    - `` - The cache invalidation logic in `courseCache.ts` is the riskiest bit. ``
    - `- Ignore the snapshot test churn — it's all from the new badge.`

- **Risk and rollback** (bullet list) — flag blast radius (feature flags, migrations, data writes, third-party calls, schema changes, removed endpoints) **and how to revert**.
  - If trivial: `- Low risk — pure UI change, no data side effects.`
  - Example: `` - Toggle the `enrollment-count` flag off to disable. ``

- **How to test** (numbered list) — manual local steps only; thorough, specific, reproducible. Do not mention automated tests. Use "N/A" if not applicable (e.g. docs, config).

- **Checklist** — keep template checkboxes as boilerplate; do not pre-tick them.

- **Other sections** — fill out as appropriate; leave empty or "N/A" if not applicable.

### Apply plain English (from the `reword-plain-english` skill)

To all prose (Summary, What changed and why, How to review, Risk and rollback):

- Sentences ≤ 25 words.
- Active voice ("This adds X", not "X has been added").
- Simple, common words; no unexplained jargon.
- Front-load keywords (readers scan in an F-shape).
- Each bullet leads with the impact, not the implementation.
- Inverted pyramid: most important info at the top of each section.

### Self-check before continuing

- Every template section is present.
- No "What changed" bullet implies the base branch had behaviour it didn't (e.g. "no longer X" only if the base branch did X).
- "How to review" and "Risk and rollback" are bullet lists; "How to test" is a numbered list (or "N/A").
- Description matches the net diff from Phase 3.

---

## 5. Push the branch

- If there are uncommitted changes, ask whether to commit them first.
- `git push -u origin <branch>` if the branch isn't tracked, otherwise `git push`.
- Surface push errors and stop until the user resolves them.

---

## 6. Open the draft PR

```bash
gh pr create --draft --base <base> --head <branch> \
  --title "<ticket_id>: <title>" \
  --body "<description>"
```

- **Title format**: `<ticket_id>: <Linear title or concise summary>`. Use the Linear title verbatim if it accurately describes the change; otherwise rewrite.
- **Body**: the description from Phase 4.
- If `gh` is missing or unauthenticated, tell the user how to fix it and stop.
- If creation fails, surface the error and suggest creating the PR manually in the GitHub UI.

After creation:

1. Capture the PR URL from `gh` output.
2. Post `@cursor review` (and nothing else) as a comment:
   ```bash
   gh pr comment <pr-url> --body "@cursor review"
   ```
   If it fails, tell the user to comment manually.
3. Display the PR as a clickable markdown link: `[PR #<number>](<pr-url>)`.
