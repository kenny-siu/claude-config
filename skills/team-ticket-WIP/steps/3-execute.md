# Step 3: Execute Tasks

Each task runs through a four-stage pipeline: **test writer -> test reviewer -> implementer -> reviewer**. Each stage is a fresh instance with clean context. The lead spawns one instance per stage, captures the result, then spawns the next.

## Branching

Create the feature branch (e.g. `proj-1234-feature-name`) from `main`. All work happens on this branch. Each instance commits directly to it.

## Pipeline

For each task (in order from Step 2):

1. **Test writer** — writes tests for this task, commits, exits. Template: `${CLAUDE_SKILL_DIR}/prompts/test-writer.md`.
2. **Test reviewer** — checks tests cover ACs, match contracts, follow testing notes. Reports findings, exits. Template: `${CLAUDE_SKILL_DIR}/prompts/test-reviewer.md`.
3. **Implementer** — gets the test writer's summary (plus any reviewer amendments), writes code, runs tests, commits, exits. Template: `${CLAUDE_SKILL_DIR}/prompts/implementer.md`.
4. **Reviewer** — reviews combined test and implementation changes, reports findings, exits. Template: `${CLAUDE_SKILL_DIR}/prompts/reviewer.md`.

### Handling failures

- **Test reviewer finds blocking issues:** spawn a fresh test writer with the feedback. Repeat until approved.
- **Reviewer finds blocking issues:** spawn a fresh implementer (or test writer) with feedback. Repeat until approved.

### Parallel pipelines

Independent tasks run their pipelines at the same time. Each pipeline uses its own worktree to avoid file conflicts.

## Handoff between instances

When one instance finishes and the next begins, the lead provides:
- The previous instance's summary (what was done, files touched)
- Current git state (branch, latest commit)
- Any plan amendments since the task was written

This keeps each instance focused with just the context it needs.

## Spawn options

- **Worktrees** for parallel pipelines to avoid conflicts.
- **Sonnet** for test writers, test reviewers, and reviewers. **Opus** for implementers.

## Rules

- **Never pass raw ticket ACs to instances.** Use the refined ACs, contracts, and testing notes from Steps 1-2. Those are the source of truth.
- **One task per instance.** Each instance handles one task, then exits.
- **Always run the full pipeline.** Every task goes through all four stages — no skipping, even for small tasks.
