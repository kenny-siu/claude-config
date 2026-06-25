---
name: fix-review
description: Fix review.
disable-model-invocation: true
args:
  - name: ARG
    description: "Pull request identifier: a PR number (e.g. 123), a full GitHub PR URL, or an '<owner>/<repo>#<number>' reference."
---

# PR Comments (review, explain, and fix)

Fetch all review comments for a pull request, filter to **unresolved** threads, and for each one: explain the issue, propose a fix, and apply it only after explicit user approval.

## Prerequisites

- **Agent mode**: The skill must run in agent mode. If not, prompt the user to switch and stop.
- **PR identifier**: `{{ARG}}` can be a PR number, a full GitHub URL, or an `owner/repo#number` reference.
  - If missing, fetch open PRs targeting the current branch; if multiple match, ask the user to choose.
- **GitHub access**: Access via gh CLI authentication or GitHub MCP permissions is required.
- **jq**: Required for parsing gh CLI JSON responses. If unavailable, inform the user and stop.

## Detection

- **gh CLI**: Available if `gh --version` succeeds. This is the preferred method.
- **GitHub MCP**: Use as a fallback if gh CLI is unavailable.

If neither is available, stop and inform the user.

## Workflow

### 1. Resolve the pull request

- Parse `{{ARG}}` to extract the PR number (and optionally owner/repo).
- If only a number is provided, derive owner and repo from `git remote get-url origin`.
- If no `{{ARG}}` is provided, fetch open PRs targeting the current branch and ask the user to choose one if there are multiple.
- If no open PR is found, stop and inform the user.

### 2. Fetch PR feedback

Fetch **both** sources — inline review threads and top-level PR comments. Bots like Cursor Bugbot post their findings as top-level PR comments, which never appear in `reviewThreads`. Skipping the issue-comments endpoint silently drops them.

#### gh CLI

Use the GraphQL API for inline review threads (gives `isResolved` / `isOutdated`):

```bash
gh api graphql -f query='
  query {
    repository(owner: "{owner}", name: "{repo}") {
      pullRequest(number: {pr_number}) {
        reviewDecision
        reviews(last: 50) {
          nodes { author { login } state body }
        }
        reviewThreads(last: 100) {
          nodes {
            isResolved
            isOutdated
            comments(last: 10) {
              nodes {
                body
                path
                line
                author { login }
                createdAt
              }
            }
          }
        }
      }
    }
  }
'
```

Use the issues endpoint for top-level PR comments (bugbot, kickoff notes, human top-level review summaries):

```bash
gh api repos/{owner}/{repo}/issues/{pr_number}/comments --paginate
```

Fetch the PR diff for context:

```bash
gh pr diff {pr_number}
```

#### GitHub MCP (fallback)

Use available GitHub MCP tools to fetch both pull request review threads and issue comments.

### 3. Filter to actionable feedback

- **Inline review threads**: keep only threads where `isResolved` is `false`. Mention `isOutdated: true` threads in case they're still relevant, but they may be skipped.
- **Top-level PR comments**: drop bot/system noise (linear linkback, Datadog status, CI badges) and the user's own meta-comments ("bugbot run", re-open notes). Keep substantive review content from humans and review bots (e.g. Cursor Bugbot). For each finding, sanity-check whether it still applies to the **current** branch state — earlier reviews may target a commit that has since been refactored away. Treat already-fixed findings as resolved and say so.

If both sources are empty after filtering, tell the user there's nothing to fix and stop.

### 4. Process each piece of feedback

For **each** actionable item (inline thread or top-level comment), in order:

1. **Read the relevant file and code** referenced by the comment (`path` and `line`). Use the file as it exists on the current branch to understand context.
2. **Explain the issue** to the user:
   - Quote the reviewer's comment.
   - Show the relevant code snippet.
   - Clearly explain what the reviewer is asking for and why.
3. **Propose a fix** (or state that none is needed):
   - If a code change addresses the comment, describe the specific fix you would make.
   - If no code change is needed (e.g. the comment is a question, an acknowledgement, or already addressed), inform the user and explain why.
4. **Ask for confirmation** before applying any fix:
   - Wait for explicit user approval before making changes.
   - If the user requests a different approach, adjust and re-propose.
   - If the user wants to skip, move on to the next comment.
5. **Apply the fix** once approved:
   - Make the code change.
   - Briefly confirm what was changed.

### 5. Verify and summarise

After processing all unresolved comments, **run the development loop yourself** for the area touched by the fixes — typecheck, lint, and the closest existing tests. Don't punt this to the user.

- Pick the right invocations for the repo (e.g. `npx tsc --noEmit`, the test file co-located with the change, or the project's `task test` equivalent).
- Surface results in the summary; if anything fails, fix or flag it before reporting done.

Then provide a summary:

- How many comments were addressed with code changes.
- How many required no changes.
- How many were skipped by the user.
- Verification results (typecheck/lint/tests run, with pass/fail counts).

## Important guidelines

- **Never batch-apply fixes.** Always process comments one at a time with user approval.
- **Preserve the reviewer's intent.** If a comment is ambiguous, ask the user for clarification rather than guessing.
- **Do not mark threads as resolved.** Leave that to the PR author in the GitHub UI.
- **Read the actual code** on the current branch, not just the diff context from the comment, to ensure fixes are accurate.

## Out of scope

- Resolving or dismissing review threads in GitHub.
- Responding to review comments in GitHub (posting replies).
- Creating new commits or pushing changes (the user controls when to commit and push).
