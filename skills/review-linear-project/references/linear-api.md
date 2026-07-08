# Known-good Linear GraphQL for this skill

Read this only when the session has no Linear tooling of its own and you're
talking to the API directly. Every snippet here has been run successfully
against a real workspace — prefer them over constructing queries from
memory.

Endpoint: `POST https://api.linear.app/graphql`
Auth: `Authorization: <personal API key>` — **no "Bearer" prefix** for
personal keys.
Errors come back as HTTP 200 with an `errors` array — always check for it.

## Step 1: resolve the scope

Find the project and its milestones. A project URL's last hex segment is
its `slugId` (e.g. `.../project/my-project-abc123def456/...` → filter on
name, then confirm against `slugId`):

```graphql
{ projects(first: 5, filter: { name: { containsIgnoreCase: "<term>" } }) {
    nodes { id name slugId projectMilestones { nodes { id name } } } } }
```

List the tickets in a milestone (swap the filter to
`project: { id: { eq: "<uuid>" } }` for a whole project):

```graphql
{ issues(first: 100, filter: { projectMilestone: { id: { eq: "<uuid>" } } }) {
    nodes { identifier title estimate state { name type } } } }
```

## Step 2: the full ticket read

`issue(id:)` accepts the display identifier ("ENG-123") or the UUID. This
returns everything the review and the apply step need, including the
internal ids for relations and comments:

```graphql
{ issue(id: "ENG-123") { id identifier title description estimate
    state { name type }
    comments { nodes { id body createdAt user { name } parent { id } } }
    relations { nodes { id type relatedIssue { identifier } } }
    inverseRelations { nodes { id type issue { identifier } } } } }
```

Comments return newest-first — sort by `createdAt` ascending before
reading. `relations` are links this issue points at; `inverseRelations`
are links pointing at it.

## Step 5: the writes

All mutations need UUIDs, not display identifiers. Use the ids captured in
the Step 2 read.

Title / description / estimate (the description replaces the whole text):

```graphql
mutation { issueUpdate(id: "<issue-uuid>", input: {
  title: "...", description: "...", estimate: 2
}) { success } }
```

Add a blocking link — **the blocker is `issueId`**, the blocked ticket is
`relatedIssueId`:

```graphql
mutation { issueRelationCreate(input: {
  issueId: "<blocker-uuid>", relatedIssueId: "<blocked-uuid>", type: blocks
}) { success } }
```

Remove a wrong link (the relation's own id, from the Step 2 read):

```graphql
mutation { issueRelationDelete(id: "<relation-uuid>") { success } }
```

Reply inside a stale comment's thread, then resolve the thread with that
reply:

```graphql
mutation { commentCreate(input: {
  issueId: "<issue-uuid>", parentId: "<stale-comment-uuid>", body: "..."
}) { comment { id } } }

mutation { commentResolve(id: "<stale-comment-uuid>",
  resolvingCommentId: "<reply-uuid>") { success } }
```

## If a query fails

Don't retry variations blindly — introspect the schema for the field you
need:

```graphql
{ __type(name: "Issue") { fields { name } } }
```
