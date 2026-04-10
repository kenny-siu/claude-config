# Step 4: Coordinate

The lead drives each task through its pipeline and handles issues as they come up.

## Between tasks

1. **Update the running summary.** After each task, record what was built — files created/modified, classes and methods available, branch state. This feeds the "Prior work" section for the next task's spawn prompts.
2. **Unblock cross-layer dependencies.** If a frontend task depends on backend API changes, run any needed code generation or schema updates before spawning the frontend instance. Check project docs for these commands.

## Handling issues within a pipeline

3. **Test reviewer blocks.** Spawn a fresh test writer with the feedback. Fresh test reviewer re-reviews. Repeat until approved. Don't spawn the implementer until approved.
4. **Test disputes.** If an implementer reports a test is wrong, check the refined ACs and contracts — they're the source of truth.
   - Test matches the contracts: spawn a fresh implementer with guidance to fix their code.
   - Test doesn't match: spawn a fresh test writer to fix it, then a fresh test reviewer to check.
5. **Plan amendments.** When an instance reports an AC, contract, or testing note is wrong:
   - **Small, obviously correct** (e.g. a return type needs `Optional`): approve, update the plan, include in future prompts.
   - **Significant** (changes scope or core behaviour): escalate to the user. Wait for approval.
6. **Reviewer blocks.** Spawn a fresh implementer (or test writer) with feedback. Fresh reviewer re-reviews. Repeat until approved.
7. **Fail fast.** If an instance fails 3 times on the same problem, stop and report to the user.

## Rules

- **Implementers don't fix tests.** If they think a test is wrong, they report to the lead. The lead spawns a fresh test writer.
- **Refined ACs and contracts settle disputes.** When test and implementation disagree, check against them before deciding who changes.
- **Keep the running summary current.** Every new instance gets it so it knows the current state.
