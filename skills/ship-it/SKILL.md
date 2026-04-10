---
name: ship-it
description: Take uncommitted changes, create a Linear ticket, branch, commit, and open a draft PR
disable-model-invocation: true
---

# Ship It

Takes the current uncommitted changes and ships them end-to-end: Linear ticket, branch, commit, and draft PR.

## Phase 1: Check you're on main

- If you're on a feature branch, stop and ask the user what to do
- Only proceed from the `main` branch

---

## Phase 2: Review uncommitted changes

### 2.1 Get the diff
- Run `git diff` and `git diff --cached` to see all uncommitted changes (staged and unstaged)
- If there are no changes, stop and tell the user

### 2.2 Check for mixed concerns
- Analyse the changes to see if they touch different, unrelated areas (e.g. a bug fix and a docs update, or two separate features)
- If the changes cover more than one concern, stop and list what you see — don't proceed
- Ask the user to confirm which changes they want to include, in case some are unintentional
- Only proceed once the user confirms

---

## Phase 3: Create Linear ticket

- Use the `/makelinearticket` skill to create a Linear ticket based on the uncommitted changes
- The ticket description should reflect what the changes actually do

---

## Phase 4: Create branch and commit

### 4.1 Create branch
- Use the `gitBranchName` from the Linear ticket response
- Run `git checkout -b <branch-name>`

### 4.2 Stage and commit
- Stage the relevant changed files
- Write a clear, concise commit message that describes the changes
- Commit the changes

---

## Phase 5: Push and create draft PR

- Use the `/push-pr` skill to push the branch and create a draft PR
