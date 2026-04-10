---
name: dependabot-fix
description: Triage and resolve Dependabot alerts and PRs — research breaking changes, assess impact, and propose actions (dismiss, merge, group PRs, or flag for discussion).
---

# Dependabot Triage and Fix

**Prerequisite:** The `gh` CLI must be installed and authenticated. If it isn't, stop and tell the user.

**Key principles:**
- **Never auto-merge or auto-dismiss.** Present the plan and wait for approval.
- **Severity drives priority.** Work through critical > high > medium > low.
- **Dependabot PRs are a means, not a goal.** Only merge a PR if it fixes a vulnerability.

---

## Phase 1: Gather Data

### 1.1 Identify the repo

```sh
gh repo view --json nameWithOwner -q .nameWithOwner
```

### 1.2 Fetch open alerts

```sh
gh api repos/{owner}/{repo}/dependabot/alerts --paginate \
  -q '.[] | {number, state, dependency: .dependency.package.name, manifest: .dependency.manifest_path, severity: .security_advisory.severity, summary: .security_advisory.summary, vulnerable_range: .security_vulnerability.vulnerable_version_range, patched_version: .security_vulnerability.first_patched_version.identifier, created: .created_at}'
```

- Keep only `open` alerts. Group by package name.
- If the API rate limit is hit, tell the user and suggest waiting or using a token with higher limits.

### 1.3 Fetch open Dependabot PRs

```sh
gh pr list --author "app/dependabot" --state open --json number,title,headRefName,url,createdAt,labels
```

For each PR, check CI status, conflicts, and review comments:

```sh
gh pr view {number} --json mergeable,mergeStateStatus,statusCheckRollup,reviewDecision,comments
```

**Drop any Dependabot PR that doesn't relate to an open alert.** These are pure version bumps with no security motivation.

**If there are no open alerts, tell the user "all clear" and stop.**

### 1.4 Get current versions

For each alerted or PR'd package, use **Grep** to find it in `package.json` (declared version) and `package-lock.json` or `yarn.lock` (installed version).

Note whether it's a production or dev dependency. Dev dependencies matter less but aren't automatically safe — always explain the reasoning. In a monorepo, note which workspace owns it.

### 1.5 Trace transitive dependencies

If an alert targets a transitive dependency:

1. Run `npm ls {package}` to find which direct dependency pulls it in.
2. Check whether upgrading the direct dependency fixes the vulnerability.
3. **Check whether the existing semver range already permits the patched version.** Run `npm view {parent-package} dependencies.{vulnerable-package}` to see the range. If it allows the patched version (e.g. `^9.0.5` allows `9.0.7`), the fix may be as simple as `npm update` or an npm override.
4. Target the direct dependency in the action plan, not the transitive one.

### 1.6 Check exploitability of unpatched alerts

If an alert has no patched version (e.g. EOL package), check whether the vulnerable code path is used before flagging for discussion:

1. Read the advisory summary to identify the vulnerable function or pattern (e.g. `startStandaloneServer`, `fromJS()`).
2. Use **Grep** to search the codebase for that function or pattern.
3. If the vulnerable code path isn't used, classify for dismissal with reason `not_used`.
4. If it is used, flag for discussion with the exploitability details.

### 1.7 Build a unified map

Combine alerts and PRs into one table per package:

| Package | Current | Target | Severity | Dependabot PR | Dev only? | Workspace | Direct / Transitive |
|---------|---------|--------|----------|---------------|-----------|-----------|---------------------|

---

## Phase 2: Research Breaking Changes

Work through packages in severity order: critical > high > medium > low.

**Check every version bump, not just major ones.** Not all packages follow semver. Treat the changelog as the source of truth, not the version number.

**Always do this research, even when CI passes.** CI can miss things tests don't cover.

### 2.1 Find changelogs

- Use **WebSearch** with query `"{package} changelog"` or `"{package} releases"`.
- Run `gh release list --repo {package-owner}/{package} --limit 20` for GitHub-hosted packages.
- List breaking changes between current and target versions, including those in minor and patch releases.
- If you can't find a changelog, say so and mark the package for manual review.

### 2.2 Assess impact

For each breaking change:

1. Use **Grep** to search the codebase for imports and usage of the affected API.
2. Decide whether the change actually affects this project.
3. Rate impact: **none** (API not used), **low** (small code change), **medium** (several files), **high** (architectural change).

### 2.3 Research migration path

If a breaking change affects the codebase:

- Look for an official migration guide.
- Check whether peer dependencies or related packages also need updating.
- Note the specific code changes needed.

---

## Phase 3: Classify and Group

### 3.1 Assign an action to each package

**Dismiss** when:
- The dependency is dev-only and the vulnerability isn't exploitable in that context, or the alert is a false positive / not applicable to how the package is used.
- Always explain the reasoning so the user can verify.

**Merge the Dependabot PR** when all of these are true:
- An open Dependabot PR exists that fixes a security vulnerability.
- CI passes (or failures are unrelated to the update).
- No breaking changes affect the codebase, or the PR already handles them.
- The version bump fully resolves the alert.

Don't merge PRs just to clear the list.

**Raise a new PR (grouped)** when:
- Several related dependencies should update together (e.g. a framework and its plugins).
- The Dependabot PR is incomplete or needs code fixes for breaking changes.
- Small updates can be batched to reduce noise.

Group by ecosystem or logical relationship.

**Flag for discussion** when:
- Breaking changes are complex or risky.
- The migration path is unclear.
- The update needs architectural decisions.
- You aren't sure whether the update is safe.

### 3.2 Triage CI failures

Run `gh pr checks {number}` and, if needed, `gh run view {run_id} --log-failed` to check CI logs.

- If the update caused the failure: move to "Raise a new PR" (with the fix) or "Flag for discussion" (if the fix is unclear).
- If unrelated: note it and keep the "Merge" recommendation.

### 3.3 Handle merge conflicts

Run `gh pr comment {number} --body "@dependabot rebase"`. Note in the plan that the PR needs a rebase first. If the rebase fails or the conflict is non-trivial, reclassify as "Raise a new PR".

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

**Dismiss (with reasoning):** For each, explain why it's safe and which alert is dismissed.

**Merge these Dependabot PRs:** For each, include PR number and link, what vulnerability it fixes, confirmation that CI passes and no breaking changes apply.

**New grouped PRs to raise:** For each group, include name and rationale, all packages and version bumps, breaking changes and code fixes needed, estimated scope.

**Needs discussion:** For each flagged item:

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

For each alert approved for dismissal:

```sh
gh api --method PATCH repos/{owner}/{repo}/dependabot/alerts/{alert_number} \
  -f state=dismissed \
  -f dismissed_reason="{reason}" \
  -f dismissed_comment="{explanation from Phase 4}"
```

Valid reasons: `fix_started`, `inaccurate`, `no_bandwidth`, `not_used`, `tolerable_risk`.

Pick the reason that best matches the Phase 4 reasoning. Use `tolerable_risk` for dev-only dependencies where the vulnerability isn't exploitable. Use `inaccurate` for false positives. Use `not_used` for dependencies not used in the way the advisory describes.

### 5.2 Merge Dependabot PRs

First, check the repo's allowed merge strategies:

```sh
gh api repos/{owner}/{repo} -q '{merge: .allow_merge_commit, squash: .allow_squash_merge, rebase: .allow_rebase_merge}'
```

Prefer `--squash` if available, otherwise `--rebase`, otherwise `--merge`.

#### Strategy A: Auto-merge (preferred when branches must be up to date)

Use when the repo requires branches to be up to date before merging, or when Dependabot rebases are slow.

1. **Approve all approved PRs** (branch protection often requires at least one review):
   ```sh
   gh pr review {number} --approve
   ```

2. **Trigger rebases on all approved PRs at once:**
   ```sh
   gh pr comment {number} --body "@dependabot rebase"
   ```

3. **Enable auto-merge on all approved PRs:**
   ```sh
   gh pr merge {number} --auto --squash  # or --rebase / --merge per repo config
   ```

4. **Schedule a check-in** using `CronCreate` for 15-20 minutes later (one-shot, `recurring: false`). The check-in should:
   - Check PR state: `gh pr view {number} --json state,mergeable,mergeStateStatus,autoMergeRequest -q '{state: .state, mergeable: .mergeable, mergeState: .mergeStateStatus, autoMerge: .autoMergeRequest}'`
   - Report which PRs merged, which are pending, and which have problems.
   - Re-trigger `@dependabot rebase` for PRs still behind and not rebasing.
   - Disable auto-merge and tell the user for PRs where CI failed after rebase.
   - Schedule another check-in if PRs remain pending.

5. **Tell the user** that auto-merge is set and you'll check back. They don't need to wait.

After each PR merges, the remaining PRs become "behind" again. Dependabot usually auto-rebases them, but the check-in will re-trigger rebases if it doesn't.

#### Strategy B: Sequential polling (fallback)

Use only if auto-merge isn't available (e.g. repo settings or permissions prevent it).

1. **Pick the next PR** from the approved list.
2. **Check the PR is mergeable** with `gh pr view {number} --json mergeable,mergeStateStatus`. If it has conflicts, run `gh pr comment {number} --body "@dependabot rebase"`, then poll every 30 seconds. If the rebase hasn't finished after 5 minutes, tell the user and move on.
3. **Wait for CI to pass.** Poll every 30 seconds with `gh pr view {number} --json statusCheckRollup`. If CI fails, tell the user and skip. If CI hasn't finished after 15 minutes, tell the user and move on.
4. **Merge the PR:**
   ```sh
   gh pr merge {number} --squash  # or --rebase / --merge per repo config
   ```
5. **Trigger rebase on the next PR** immediately so it starts rebasing while you report progress.
6. **Tell the user** after each merge or skip: "Merged PR #X" or "Skipped PR #X — CI failed / rebase timed out".
7. **Repeat** until the queue is empty.

### 5.3 Raise grouped PRs

For each approved group:

1. **Get the Linear ticket.** Ask the user for the Linear ticket ID. Look it up using Linear MCP tools to get the title and branch name. If there are multiple grouped PRs, append a short disambiguator to the branch name (e.g. `proj-456-dependency-updates-eslint`). If there's only one, use the branch name as-is.

2. **Create a branch** from main:
   ```sh
   git checkout main && git pull
   git checkout -b {linear-ticket-branch-name}-{disambiguator}
   ```

3. **Update the dependencies.** Use **Edit** to update version ranges in the relevant `package.json` file(s), then run `npm install`. If peer dependency conflicts arise, resolve them by also updating the peer dependencies. Note any extra packages you had to bump.

4. **Apply code fixes** for breaking changes identified in Phase 2. Keep changes minimal — only fix what's needed for the upgrade.

5. **Verify the build** with `npx tsc --noEmit` or the relevant build command. If the build fails and the fix isn't obvious, stop and ask the user.

6. **Commit and push.** Stage only the changed files by name (don't use `git add -A`):
   ```sh
   git add {list of changed files}
   git commit -m "{ticket-id}: {group description}"
   git push -u origin {linear-ticket-branch-name}
   ```

7. **Create a draft PR:**
   ```sh
   gh pr create --draft --base main \
     --title "{ticket-id}: {group description}" \
     --body "{body}"
   ```
   The PR body should include: link to the Linear ticket, which alerts this resolves (link to alert numbers), all packages updated and their version changes, breaking changes and what code was changed to handle them.

8. **Don't wait for CI.** Tell the user you've created the PR and they can check CI results there.

9. **Return to main** before starting the next group:
   ```sh
   git checkout main
   ```

### 5.4 Report results

| Action | Package(s) | Result |
|--------|-----------|--------|
| Dismissed | {package} (alert #{n}) | Done |
| Merged | {package} (PR #{n}) | Done |
| Merged | {package} (PR #{n}) | Skipped — CI failed |
| Grouped PR | {group name} | PR #{n} created (draft) |
| Flagged | {package} | No action (needs discussion) |

Include links to any PRs created or merged.
