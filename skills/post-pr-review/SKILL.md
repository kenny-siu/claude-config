---
name: post-pr-review
description: "You MUST invoke this skill whenever the user asks you to post, raise, or leave a set of comments on a GitHub PR as a single review — typically the findings from a `/review-pr` run. Do NOT post comments one-by-one or compose them in your own voice — activate this skill to create ONE pending review with inline comments so the user can check and submit. Triggers on phrases like 'post these as PR comments', 'leave a review with these', 'raise these on the PR', 'open a pending review', 'add these as inline comments', or any request to land review findings on GitHub as a review for the user to submit."
---

# Post a Pending PR Review

Land a set of review findings on a GitHub PR as a **single pending review** with inline comments. The user reviews and submits in the GitHub UI.

## When to use

The user has findings (often from `/review-pr`) and wants them on the PR — but not auto-submitted. Typical triggers: "post these as comments", "raise these on the PR", "leave a pending review", "add these as inline comments".

## Style rules for the comments

Apply these to every comment, including the review body:

- **Plain English.** Short, common words. Sentences under 25 words. Active voice. (Mirrors the `reword-plain-english` rules.)
- **`[Non-blocking]` prefix** for any finding that's a quibble, nit, or doesn't really matter — anything the user could reasonably ignore without consequences.
- **No em-dashes or en-dashes** in the comment body. Use `--`, a colon, a single hyphen, or just a period and a new sentence. Single hyphens inside compound words (e.g. `[Non-blocking]`) are fine.
- **No priority levels.** Don't write "Priority: low" or similar.
- **Keep it short.** Two short paragraphs at most, unless the detail genuinely matters (e.g. a code-example fix the reader needs to act on).
- **One finding per comment.** Don't bundle.

## Process

### 1. Gather PR identity

Get the PR number and head SHA. If the user didn't say which PR, use the current branch:

```bash
gh pr view --json number,headRefOid,headRefName,baseRefName
```

You need:
- `number` → goes in the API path
- `headRefOid` → `commit_id` in the payload (the review pins to this commit)

### 2. Map findings to diff lines

Every inline comment needs a `path`, a `line` in the current file (HEAD), and a `side`. Use `side: "RIGHT"` for added or unchanged lines on the new side (the default for new code). Use `"LEFT"` only when commenting on a deleted line.

Findings whose file is **not** in the diff (e.g. a stale comment in `schema.prisma` that nobody touched) can't be inline. Put those in the review body instead, with a clear file:line reference.

Confirm line numbers exist in HEAD before posting:

```bash
grep -n "<some unique token>" path/to/file
```

### 3. Build the payload as a file

Write a JSON file (don't pass huge inline JSON — escaping bites):

```json
{
  "commit_id": "<headRefOid>",
  "body": "Optional top-level review body. Use for findings that have no diff line to attach to, or a short summary of what was reviewed.",
  "comments": [
    {
      "path": "src/...",
      "line": 123,
      "side": "RIGHT",
      "body": "[Non-blocking] One finding, plain English."
    }
  ]
}
```

**Omit `event`.** That's what leaves it pending. Setting `event` to `APPROVE`, `REQUEST_CHANGES`, or `COMMENT` would submit it immediately — never do that here unless the user explicitly says to.

### 4. Post the review

```bash
gh api --method POST \
  /repos/<owner>/<repo>/pulls/<pr-number>/reviews \
  --input /tmp/pr-review.json
```

The response includes `id`, `state: "PENDING"`, and an `html_url` like `https://github.com/<owner>/<repo>/pull/<pr>#pullrequestreview-<id>` — give that link to the user.

### 5. Iterating (if the user wants changes)

Pending reviews are private to the user, so the cleanest iteration is **delete and recreate**:

```bash
gh api --method DELETE /repos/<owner>/<repo>/pulls/<pr>/reviews/<review-id>
```

Then rewrite the JSON file and POST again. There's no clean API to edit individual comments inside a pending review.

If you've lost the review id, list pending reviews:

```bash
gh api /repos/<owner>/<repo>/pulls/<pr>/reviews \
  --jq '.[] | select(.state=="PENDING") | {id, html_url}'
```

## Gotchas

- **`line` is the line number in the file at `commit_id`.** Not the diff hunk position. If the PR has new commits since you last read the file, re-fetch the head SHA.
- **Files outside the diff cannot host inline comments.** GitHub silently rejects them or 422s. Use the body.
- **Don't pipe the response through `python3`.** This machine uses `mise`/`asdf` and bare `python3` may not be on PATH. Use `gh api ... --jq '...'` instead.
- **Don't submit the review.** Only the user does that. Leave `event` out of the payload.
