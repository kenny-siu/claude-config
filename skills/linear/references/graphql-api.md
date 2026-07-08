# Linear GraphQL reference

Read this when `scripts/linear.py` doesn't cover the job and you need the `query` escape hatch, or when editing the script.

Endpoint: `POST https://api.linear.app/graphql`
Auth header: `Authorization: <LINEAR_API_KEY>` (no "Bearer" prefix).

Via the script:

```bash
python3 scripts/linear.py query '<graphql>' --variables '{"key": "value"}'
```

## Contents

- [Which fields are signal, which are noise](#field-assessment)
- [Look-ups: issues take identifiers, everything else takes UUIDs](#ids)
- [Query patterns](#query-patterns) — filters, cycles, projects, users, pagination
- [Mutation patterns](#mutation-patterns) — archive, delete, relations, labels
- [Pitfalls](#pitfalls)

## Field assessment

Learned from probing real workspace data. When writing raw queries, fetch from the left column and skip the right.

| Worth fetching | Skip (noise) |
|---|---|
| `identifier title description url branchName` | `descriptionData` (ProseMirror JSON blob) |
| `state { name type }` | `history` — mostly automated state churn |
| `assignee/creator { name }` | `subscribers` — tells you nothing |
| `priority priorityLabel estimate` | `sortOrder`, `boardOrder`, position fields |
| `comments` — see below | `reactions` |
| `attachments { title url sourceType }` — GitHub PRs, Slack threads | full team `labels` catalog (50+ stale entries) |
| `relations` / `inverseRelations` / `parent` / `children` | `integrationsSettings`, sync metadata |
| `labels { nodes { name } }` on one issue | |

**Comments are the most commonly missed high-value field.** Decisions, root-cause analyses, and scope changes live there and rarely get folded back into the description. Always request them when reading a ticket for context. Two things to handle:

- They return newest-first; sort by `createdAt` ascending before reading.
- Slack-synced threads inject boilerplate ("This comment thread is synced…", bot posts like "Created issue [X]"). Skip those; keep human comments and substantive bot posts.

## IDs

`issue(id: ...)` accepts the human identifier (`"ENG-123"`) or the UUID. Everything else — mutations' `stateId`, `teamId`, `cycleId`, `assigneeId`, `parentId`, `labelIds` — needs UUIDs. Resolve names to UUIDs first (the script's `teams` command prints state and cycle UUIDs).

## Query patterns

Issue filtering (the `IssueFilter` type is rich — comparators include `eq`, `neq`, `in`, `containsIgnoreCase`, `eqIgnoreCase`, `null`):

```graphql
query {
  issues(
    first: 25
    orderBy: updatedAt
    filter: {
      team: { key: { eq: "ENG" } }
      state: { type: { eq: "started" } }        # backlog|unstarted|started|completed|canceled|triage
      assignee: { name: { containsIgnoreCase: "alice" } }
      labels: { name: { eq: "Bug" } }
      cycle: { isActive: { eq: true } }          # current sprint
    }
  ) { nodes { identifier title state { name } } }
}
```

Full-text search:

```graphql
query { searchIssues(term: "duplicate draft records", first: 10) {
  nodes { identifier title state { name } team { key } } } }
```

Current cycle for a team, with its issues:

```graphql
query { teams(filter: { key: { eq: "ENG" } }) { nodes {
  activeCycle { id number startsAt endsAt
    issues(first: 50) { nodes { identifier title state { name } assignee { name } } } } } } }
```

Projects:

```graphql
query { projects(first: 20, filter: { state: { eq: "started" } }) {
  nodes { id name state lead { name } targetDate } } }
```

Find a user's UUID:

```graphql
query { users(filter: { name: { containsIgnoreCase: "alice" } }) {
  nodes { id name email } } }
```

Pagination — every connection supports it:

```graphql
query { issues(first: 50, after: "<endCursor>") {
  pageInfo { hasNextPage endCursor }
  nodes { identifier } } }
```

## Mutation patterns

All follow the shape `<entity><Verb>(input: ...) { success <entity> { ... } }`. The script covers `issueCreate`, `issueUpdate`, `commentCreate`. Others:

```graphql
# Archive (reversible, preferred over delete)
mutation { issueArchive(id: "<uuid>") { success } }

# Trash (recoverable from trash for ~30 days)
mutation { issueDelete(id: "<uuid>") { success } }

# Link two issues: type is "related" | "blocks" | "duplicate"
mutation { issueRelationCreate(input: {
  issueId: "<uuid>", relatedIssueId: "<uuid>", type: related
}) { success } }

# Add labels (labelIds REPLACES the set on issueUpdate — fetch existing ids first)
mutation { issueUpdate(id: "<uuid>", input: { labelIds: ["<uuid>", "<uuid>"] }) { success } }

# Attach a URL to an issue
mutation { attachmentLinkURL(issueId: "<uuid>", url: "https://...") { success } }
```

## Pitfalls

- **No "Bearer" prefix** on the Authorization header for personal API keys.
- **Mutations need UUIDs**, not identifiers like ENG-123 — resolve first.
- **`labelIds` on `issueUpdate` replaces** all labels; merge with existing before writing. (`addedLabelIds` / `removedLabelIds` exist on `IssueUpdateInput` for incremental changes.)
- **Comment order is newest-first** by default.
- **Rate limit** is ~1500 requests/hour per key. Batch reads into one query with multiple fields rather than looping single-field calls.
- **Errors come back as HTTP 200** with an `errors` array — always check for it (the script does).
- When a field name guess fails, introspect: `query '{ __type(name: "Issue") { fields { name } } }'`.
