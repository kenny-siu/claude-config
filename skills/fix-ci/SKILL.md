---
name: fix-ci
description: Fetch failed CI checks for a pull request, retrieve the failure logs, diagnose each failure, and fix it after user confirmation. Use when a PR has failing checks, CI is red, tests are failing, or the user wants to diagnose and fix CI failures.
args:
  - name: ARG
    description: "Pull request identifier: a PR number (e.g. 123), a full GitHub PR URL, or an '<owner>/<repo>#<number>' reference."
---

# Fix PR CI Checks

Diagnose and fix failed CI checks for a pull request, one failure at a time.

## Workflow

### 1. Find the pull request

Parse `{{ARG}}` to get the PR number. If no argument, find the open PR for the current branch. Derive owner/repo from `git remote get-url origin` if needed.

### 2. Get failed checks

```bash
gh pr checks {pr_number} --repo {owner}/{repo} --json name,state,conclusion,link \
  | jq '.[] | select(.conclusion == "failure" or .conclusion == "timed_out")'
```

If everything passes, tell the user and stop. Otherwise show a summary table of failed checks.

### 3. Fetch failure logs

Detect the CI provider from the check link URL.

- **GitHub Actions** (links contain `github.com`): Use `gh run view {run_id} --repo {owner}/{repo} --log-failed`.
- **CircleCI** (links contain `circleci.com`): If CircleCI MCP tools are available, use `mcp__circleci__get_build_failure_logs` with the check link URL. Use `mcp__circleci__get_job_test_results` for detailed test results.
- **Other providers**: Follow the check link and extract the failure log manually, or ask the user to paste the relevant output.

**Truncate before analysing.** Only load the relevant error block (last 200 lines or the specific failure section) — don't load the entire log.

### 4. Diagnose and fix — one at a time

For each failed check:

1. **Diagnose** the failure type: test failure, lint/format error, type error, snapshot mismatch, or other.
2. **Explain** what's failing and why. Quote the relevant log lines and show the referenced code.
3. **Propose a fix.** If an auto-fix command exists (linter `--fix`, snapshot `--update`), mention it. If no code change helps (flaky test, infra issue), say so.
4. **Wait for user approval** before applying. Skip if declined.

### 5. Summary

Report how many checks were fixed vs skipped. Remind the user to run the project's dev loop (type-check, lint, test) before pushing — infer the right commands from project config.

## Rules

- Process one failure at a time with user approval. Never batch-apply fixes.
- Read the actual code on the current branch, not just the log output.
- Don't re-trigger CI or push changes — leave that to the user.
