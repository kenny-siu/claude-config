# Step 5: Integrate and Verify

Once all tasks pass review:

1. **Combine commits.** Rebase onto the feature branch in narrative order — backend first, frontend second. Interleave test and implementation commits so each commit is a complete unit: code change and its tests together. Use interactive rebase or cherry-pick.

2. **Run the full dev loop** across the whole project. Use the lint, format, type-check, and test commands from Step 1. Run the full test suite, not just individual task tests.

3. **Fix integration issues** — typically import errors, type mismatches at boundaries, or test failures from combined changes.

4. **Report results to the user** — what was done, what passed, any remaining issues.
