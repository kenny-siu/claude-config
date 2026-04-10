# Step 2: Plan, Decompose, and Validate

## 2a. Break work into tasks

1. **Break the work into tasks.** Each task is a self-contained unit one agent instance can complete. One task per instance — fresh context, no degradation.

## 2b. Define interface contracts

2. **Write interface contracts for each task.** Teammates work in parallel — without contracts, they'll build incompatible code.

   | Field | Content |
   |-------|---------|
   | **Assumptions** | What this task depends on from other tasks — models, methods, types, return shapes, event names |
   | **Exports** | What this task provides to other tasks — classes, methods, signatures, return types |

   **Example:**
   - **Assumptions:** `Activity` model has `status` field (task 1). `ActivityType` GraphQL type exposes `status` (task 2).
   - **Exports:** `ActivityStatusInput` enum (`ACTIVE`, `PAUSED`, `COMPLETED`). `update_activity_status(activity_id, new_status) -> Activity` service method.

   Every assumption must match an export from another task. An unmatched assumption means the plan has a gap.

## 2c. Write testing notes

3. **Write testing notes for each task** using the 4-scenario framework. These are the test writer's brief — specific enough that test writer and implementer arrive at compatible interpretations.

   | Scenario | What to cover |
   |----------|---------------|
   | **Happy path** | Core behaviour works as described in the AC |
   | **Edge cases** | Boundaries, empty states, max values, concurrency |
   | **Negative cases** | Invalid input, unauthorised access, missing resources |
   | **State preservation** | Side effects — timestamps update, events fire, related objects stay consistent |

   **Example:**
   ```
   Task: Activity status transitions
   - Happy path: active -> paused succeeds, returns updated activity with refreshed updated_at
   - Edge case: setting status to its current value (succeed or no-op?)
   - Negative: invalid transition (completed -> active) returns validation error
   - Negative: non-owner returns 403
   - State: status change fires ActivityStatusChangedEvent with old and new status
   ```

## 2d. Layer and order tasks

4. **Identify layers** — backend, frontend, or both. Each task belongs to one layer. Find the relevant source directories and test locations.

5. **Order tasks.** Each runs through the pipeline: test writer -> test reviewer -> implementer -> reviewer. Independent tasks run pipelines in parallel. Dependent tasks run sequentially. If backend API changes must land before frontend can use them, mark that dependency.

## 2e. Validate the plan

6. **Validate before presenting.** Check for:
   - **No unmatched assumptions** — every assumption maps to an export
   - **No overlapping deliverables** — no two tasks editing the same file
   - **No circular dependencies** — one-way dependency directions
   - **Complete AC coverage** — every refined AC is covered by at least one task's testing notes

7. **Present the plan to the user:**
   - Refined ACs (from Step 1)
   - Task list with interface contracts and testing notes
   - Teammates and their roles
   - Dependencies and order of operations

> **Wait for user approval before spawning any instances.**
