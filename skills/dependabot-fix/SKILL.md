---
name: dependabot-fix
description: Triage and resolve Dependabot alerts and PRs — research breaking changes, assess impact, and propose actions (dismiss, merge, group PRs, or flag for discussion).
disable-model-invocation: true
---

# Dependabot Triage and Fix

**Prerequisites:** The `gh` CLI must be installed and authenticated. If `gh` isn't set up, stop and tell the user.

**Key principles:**
- **Never auto-merge or auto-dismiss.** Always present the plan and wait for approval.
- **Severity drives priority.** Work through critical > high > medium > low.
- **Dependabot PRs are a means, not a goal.** Only merge a PR if it fixes a vulnerability.

---

## Phase 1: Gather Data

### 1.1 Identify the repo

Use the **Bash** tool to run:

```sh
gh repo view --json nameWithOwner -q .nameWithOwner
```

This gives you `{owner}/{repo}` in one shot.

### 1.2 Fetch alerts

Use the **Bash** tool to run:

```sh
gh api repos/{owner}/{repo}/dependabot/alerts --paginate \
  -q '.[] | {number, state, dependency: .dependency.package.name, manifest: .dependency.manifest_path, severity: .security_advisory.severity, summary: .security_advisory.summary, vulnerable_range: .security_vulnerability.vulnerable_version_range, patched_version: .security_vulnerability.first_patched_version.identifier, created: .created_at}'
```

- Keep only `open` alerts.
- Group by package name (one package may have several advisories).
- If the GitHub API rate limit is hit, tell the user and suggest waiting or using a token with higher limits.

### 1.3 Fetch open Dependabot PRs

Use the **Bash** tool to run:

```sh
gh pr list --author "app/dependabot" --state open --json number,title,headRefName,url,createdAt,labels
```

For each PR, note which package and version bump it covers. Check CI status, conflicts, and review comments by running:

```sh
gh pr view {number} --json mergeable,mergeStateStatus,statusCheckRollup,reviewDecision,comments
```

**Drop any Dependabot PR that doesn't relate to an open alert.** These are pure version bumps with no security motivation — they add noise and shouldn't appear in the output.

**If there are no open alerts (regardless of PRs), tell the user "all clear" and stop.**

### 1.4 Get current versions

For each alerted or PR'd package:

- Use the **Grep** tool to find the package name in `package.json` (declared version) and `package-lock.json` or `yarn.lock` (installed version).
- Note whether it's a production or dev dependency. Dev dependencies matter less but aren't automatically safe — always explain the reasoning.
- In a monorepo, note which workspace owns it.

### 1.5 Trace transitive dependencies

If an alert targets a transitive (indirect) dependency:

- Use the **Bash** tool to run `npm ls {package}` to find which direct dependency pulls it in.
- Check whether upgrading the direct dependency fixes the vulnerability.
- **Check whether the existing semver range already permits the patched version.** Run `npm view {parent-package} dependencies.{vulnerable-package}` to see the range. If the range allows the patched version (e.g. `^9.0.5` allows `9.0.7`), the fix may be as simple as `npm update` or an npm override — no dependency upgrade needed. Don't flag these as "needs discussion" when the fix is trivial.
- Target the direct dependency in the action plan, not the transitive one.

### 1.6 Check exploitability of unpatched alerts

If an alert has no patched version (e.g. EOL package), don't automatically flag it for discussion. First check whether the specific vulnerable code path is actually used:

- Read the advisory summary to identify the vulnerable function or pattern (e.g. `startStandaloneServer`, `fromJS()`).
- Use the **Grep** tool to search the codebase for that function or pattern.
- If the vulnerable code path is not used, classify the alert for dismissal with reason `not_used`, not as "needs discussion".
- If it IS used, then flag for discussion with the exploitability details.

### 1.7 Build a unified map

Combine alerts and PRs into one table per package:

| Package | Current | Target | Severity | Dependabot PR | Dev only? | Workspace | Direct / Transitive |
|---------|---------|--------|----------|---------------|-----------|-----------|---------------------|

---

## Phase 2: Research Breaking Changes

Work through packages in severity order: critical > high > medium > low.

**Check every version bump, not just major ones.** Not all packages follow semver. A minor or patch bump can still have breaking changes. Treat the changelog as the source of truth, not the version number.

**Always do this research — even when CI passes on a Dependabot PR.** CI can miss things tests don't cover.

### 2.1 Find changelogs

- Use the **WebSearch** tool with query `"{package} changelog"` or `"{package} releases"`.
- Use the **Bash** tool to run `gh release list --repo {package-owner}/{package} --limit 20` for GitHub-hosted packages.
- List breaking changes between the current and target versions — including those in minor and patch releases.
- If you can't find a changelog, say so in the plan and mark the package for manual review.

### 2.2 Assess impact

For each breaking change:

- Use the **Grep** tool to search the codebase for imports and usage of the affected API.
- Decide whether the change actually affects this project.
- Rate impact: **none** (API not used), **low** (small code change), **medium** (several files), **high** (architectural change).

### 2.3 Research migration path

If a breaking change affects the codebase:

- Look for an official migration guide.
- Check whether peer dependencies or related packages also need updating.
- Note the specific code changes needed.

---

## Phase 3: Classify and Group

### 3.1 Assign an action to each package

#### Dismiss

All of these must be true:

- The dependency is dev-only **and** the vulnerability isn't exploitable in that context, **or** the alert is a false positive / not applicable to how the package is used.
- Always explain the reasoning so the user can verify.

#### Merge the Dependabot PR

All of these must be true:

- An open Dependabot PR exists that fixes a security vulnerability.
- CI passes (or failures are unrelated to the update).
- No breaking changes affect the codebase, or the PR already handles them.
- The version bump fully resolves the alert.

Don't merge PRs just to clear the list.

#### Raise a new PR (grouped)

Use when:

- Several related dependencies should update together (e.g. a framework and its plugins).
- The Dependabot PR is incomplete or needs code fixes for breaking changes.
- Small updates can be batched to reduce noise.

Group by ecosystem or logical relationship.

#### Flag for discussion

Use when:

- Breaking changes are complex or risky.
- The migration path is unclear.
- The update needs architectural decisions.
- You aren't sure whether the update is safe.

### 3.2 Triage CI failures on Dependabot PRs

- Use the **Bash** tool to run `gh pr checks {number}` and, if needed, `gh run view {run_id} --log-failed` to check CI logs.
- If the update caused the failure: move it to "Raise a new PR" (with the fix) or "Flag for discussion" (if the fix is unclear).
- If unrelated: note it and keep the "Merge" recommendation.

### 3.3 Handle merge conflicts

- Use the **Bash** tool to run `gh pr comment {number} --body "@dependabot rebase"`.
- Note in the plan that the PR needs a rebase first.
- If the rebase fails or the conflict is non-trivial, reclassify as "Raise a new PR".

### 3.4 Group related updates

- Identify packages that should update together.
- Name each group clearly (e.g. "ESLint ecosystem upgrade", "React 18 compatibility").
- List all packages and version changes in the group.
- Use good judgement — consider affected workspaces, shared ecosystems, and whether updating separately would cause breakage.

---

## Phase 4: Present the Action Plan

### 4.1 Summary table

| # | Action | Package(s) | Current -> Target | Severity | Breaking Changes | Notes |
|---|--------|-----------|-------------------|----------|------------------|-------|

### 4.2 Detailed breakdown

#### Dismiss (with reasoning)

For each: explain why it's safe and which alert is dismissed.

#### Merge these Dependabot PRs

For each: PR number and link, what vulnerability it fixes, confirmation that CI passes and no breaking changes apply.

#### New grouped PRs to raise

For each group: name and rationale, all packages and version bumps, breaking changes and code fixes needed, estimated scope.

#### Needs discussion

For each flagged item:

1. **One-line summary** — what's wrong and why it can't be fixed now.
2. **What's blocking** — name the upstream package, version constraint, or breaking change. Don't use vague phrases like "monitor upstream" — say what needs to happen.
3. **Who owns what** — separate the direct dependency (which we control) from the transitive one (which we don't). Name each and say whether it's prod or dev.
4. **Next step** — one concrete action the user can take now.
5. **How items relate** — if two flagged items are connected, say so up front. Consider grouping them under one heading.

### 4.3 Wait for approval

Present the full plan and wait for the user to approve, change, or reject actions. Don't merge, dismiss, or change code without explicit approval.

---

## Phase 5: Execute Approved Actions

Once the user approves, execute all approved actions without pausing between them.

### 5.1 Dismiss alerts

For each alert approved for dismissal, use the **Bash** tool to run:

```sh
gh api --method PATCH repos/{owner}/{repo}/dependabot/alerts/{alert_number} \
  -f state=dismissed \
  -f dismissed_reason="{reason}" \
  -f dismissed_comment="{explanation from Phase 4}"
```

Valid reasons: `fix_started`, `inaccurate`, `no_bandwidth`, `not_used`, `tolerable_risk`.

Pick the reason that best matches the Phase 4 reasoning. For dev-only dependencies where the vulnerability isn't exploitable, use `tolerable_risk`. For false positives, use `inaccurate`. For dependencies not used in the way the advisory describes, use `not_used`.

### 5.2 Merge Dependabot PRs

First, check the repo's allowed merge strategies and whether branches must be up to date before merging:

```sh
gh api repos/{owner}/{repo} -q '{merge: .allow_merge_commit, squash: .allow_squash_merge, rebase: .allow_rebase_merge}'
```

Pick the allowed strategy: prefer `--squash` if available, otherwise `--rebase`, otherwise `--merge`.

#### Strategy A: Auto-merge (preferred when branches must be up to date)

If the repo requires branches to be up to date before merging, or if Dependabot rebases are slow, use auto-merge to avoid polling:

1. **Approve all approved PRs** (branch protection often requires at least one review):
   ```sh
   gh pr review {number} --approve
   ```
   Do this for every PR in the queue. Without an approving review, auto-merge will stay blocked even after rebase and CI pass.

2. **Trigger rebases on all approved PRs at once:**
   ```sh
   gh pr comment {number} --body "@dependabot rebase"
   ```
   Do this for every PR in the queue in parallel — Dependabot will process them.

3. **Enable auto-merge on all approved PRs:**
   ```sh
   gh pr merge {number} --auto --squash  # or --rebase / --merge per repo config
   ```
   This tells GitHub to merge each PR automatically once it's up to date and CI passes.

4. **Schedule a check-in** using `CronCreate` for 15–20 minutes later (one-shot, `recurring: false`). The check-in prompt should:
   - Check the state of each PR: `gh pr view {number} --json state,mergeable,mergeStateStatus,autoMergeRequest -q '{state: .state, mergeable: .mergeable, mergeState: .mergeStateStatus, autoMerge: .autoMergeRequest}'`
   - Report which PRs have merged, which are still pending, and which have problems.
   - For PRs that are still behind and not rebasing, re-trigger `@dependabot rebase`.
   - For PRs where CI failed after rebase, disable auto-merge and tell the user.
   - If PRs remain pending, schedule another check-in for 15 minutes later.

5. **Tell the user** that auto-merge is set and you'll check back. They don't need to wait.

**Note:** After each PR merges, the remaining PRs will become "behind" again. Dependabot usually auto-rebases them, but if it doesn't, the check-in will re-trigger rebases.

#### Strategy B: Sequential polling (fallback)

Use this only if auto-merge is not available (e.g. repo settings or permissions prevent it).

1. **Pick the next PR** from the approved list.
2. **Check the PR is mergeable:**
   - Use the **Bash** tool to run `gh pr view {number} --json mergeable,mergeStateStatus` to check for conflicts.
   - If it has conflicts, run:
     ```sh
     gh pr comment {number} --body "@dependabot rebase"
     ```
   - Then poll until the rebase finishes. Check every 30 seconds:
     ```sh
     gh pr view {number} --json mergeable,mergeStateStatus,statusCheckRollup
     ```
   - If the rebase hasn't finished after 5 minutes, tell the user and move on to the next PR.
3. **Wait for CI to pass:**
   - Poll the PR's check status every 30 seconds:
     ```sh
     gh pr view {number} --json statusCheckRollup
     ```
   - If CI fails, tell the user and skip this PR. Don't block the rest of the queue.
   - If CI hasn't finished after 15 minutes, tell the user and move on.
4. **Merge the PR:**
   ```sh
   gh pr merge {number} --squash  # or --rebase / --merge per repo config
   ```
5. **Trigger rebase on the next PR** — if there are more PRs in the queue, immediately run `gh pr comment {next_number} --body "@dependabot rebase"` so it starts rebasing while you report progress.
6. **Tell the user** — after each merge (or skip): "Merged PR #X" or "Skipped PR #X — CI failed / rebase timed out".
7. **Repeat** from step 1 until the queue is empty.

### 5.3 Raise grouped PRs

For each approved group:

1. **Get the Linear ticket:**
   - Ask the user for the Linear ticket ID for this group (e.g. "What's the Linear ticket for the ESLint ecosystem upgrade?").
   - Look up the ticket using the Linear MCP tools to get the ticket title and branch name.
   - If there are multiple grouped PRs to raise, append a short disambiguator to the branch name (e.g. `sea-456-dependency-updates-eslint`, `sea-456-dependency-updates-sequelize`). The disambiguator goes at the end.

2. **Create a branch** from main using the **Bash** tool:
   ```sh
   git checkout main && git pull
   git checkout -b {linear-ticket-branch-name}-{disambiguator}
   ```
   If there's only one grouped PR, use the branch name as-is without a disambiguator.

3. **Update the dependencies:**
   - Use the **Edit** tool to update version ranges in the relevant `package.json` file(s).
   - Use the **Bash** tool to run `npm install` to update the lockfile.
   - If peer dependency conflicts arise, resolve them by also updating the peer dependencies. Note any extra packages you had to bump.

4. **Apply code fixes for breaking changes:**
   - Make the code changes identified in Phase 2.
   - Keep changes minimal — only fix what's needed for the upgrade, don't refactor surrounding code.

5. **Verify the build:**
   - Use the **Bash** tool to run `npx tsc --noEmit` (backend) or the relevant build command to catch breakage.
   - If the build fails, investigate and fix. If the fix isn't obvious, stop and ask the user.

6. **Commit and push:**
   - Stage only the changed files by name (don't use `git add -A`).
   - Use the **Bash** tool to run:
     ```sh
     git add {list of changed files}
     git commit -m "{ticket-id}: {group description}"
     git push -u origin {linear-ticket-branch-name}
     ```

7. **Create a draft PR** using the **Bash** tool:
   ```sh
   gh pr create --draft --base main \
     --title "{ticket-id}: {group description}" \
     --body "{body}"
   ```
   The PR body should include:
   - Link to the Linear ticket
   - Which alerts this resolves (link to alert numbers)
   - All packages updated and their version changes
   - Breaking changes and what code was changed to handle them

8. **Don't wait for CI.** Tell the user you've created the PR and they can check CI results there.

9. **Return to main** before starting the next group:
   ```sh
   git checkout main
   ```

### 5.4 Report results

After all actions are done, present a summary:

| Action | Package(s) | Result |
|--------|-----------|--------|
| Dismissed | {package} (alert #{n}) | Done |
| Merged | {package} (PR #{n}) | Done |
| Merged | {package} (PR #{n}) | Skipped — CI failed |
| Grouped PR | {group name} | PR #{n} created (draft) |
| Flagged | {package} | No action (needs discussion) |

Include links to any PRs created or merged.
